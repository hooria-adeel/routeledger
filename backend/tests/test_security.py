"""Automatic security tests for the RouteLedger backend.
Run from the backend folder:   pytest -v
"""
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import psycopg
import pytest

from app.config import settings
from app.database import pool
from app.middleware import login_limiter
from tests.conftest import PASSWORD


# ----------------------------------------------------------------------
# 1. Passwords and login
# ----------------------------------------------------------------------
def test_passwords_are_stored_as_argon2_hashes(users):
    with pool.connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM employees WHERE email = %s", (users["Admin"],)
        ).fetchone()
    assert row["password_hash"].startswith("$argon2id$")
    assert PASSWORD not in row["password_hash"]


def test_wrong_email_and_wrong_password_look_the_same(client, users):
    a = client.post("/auth/login", json={"email": "nobody@routeledger.test", "password": "x"})
    b = client.post("/auth/login", json={"email": users["Viewer"], "password": "wrong"})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()                 # an attacker cannot tell which emails exist


def test_account_locks_after_five_wrong_passwords(client, new_user):
    _, email = new_user()
    codes = [
        client.post("/auth/login", json={"email": email, "password": "wrong"}).status_code
        for _ in range(5)
    ]
    assert codes == [401, 401, 401, 401, 401]
    # now even the CORRECT password is refused
    r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 423


def test_login_is_rate_limited(client):
    login_limiter.max_calls = 3
    try:
        codes = [
            client.post("/auth/login", json={"email": "x@routeledger.test", "password": "x"}).status_code
            for _ in range(5)
        ]
    finally:
        login_limiter.max_calls = 10
    assert codes[:3] == [401, 401, 401]
    assert codes[3:] == [429, 429]


def test_login_cookie_is_httponly_and_samesite(client, users):
    r = client.post("/auth/login", json={"email": users["Viewer"], "password": PASSWORD})
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_deactivated_employee_loses_access(client, login, new_user, users):
    employee_id, email = new_user("Editor")
    victim = client.__class__(client.app)
    victim.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert victim.get("/auth/me").status_code == 200

    login("Admin")
    assert client.patch(f"/employees/{employee_id}", json={"is_active": False}).status_code == 200
    assert victim.get("/auth/me").status_code == 401     # the old cookie no longer works


# ----------------------------------------------------------------------
# 2. Tickets (tokens) cannot be faked
# ----------------------------------------------------------------------
def make_token(secret, employee_id=1, minutes=60, algorithm="HS256"):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(employee_id), "iat": now, "exp": now + timedelta(minutes=minutes)},
        secret, algorithm=algorithm,
    )


@pytest.mark.parametrize("label,token", [
    ("garbage", "not.a.token"),
    ("signed with a different key", make_token("x" * 40)),
    ("expired", make_token(settings.secret_key, minutes=-5)),
    ("algorithm none", jwt.encode({"sub": "1"}, key="", algorithm="none")),
])
def test_forged_tokens_are_rejected(client, label, token):
    client.cookies.set("access_token", token)
    assert client.get("/auth/me").status_code == 401, label


# ----------------------------------------------------------------------
# 3. SQL injection
# ----------------------------------------------------------------------
PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE products; --",
    "\" OR \"\"=\"",
    "1; SELECT pg_sleep(5) --",
    "' UNION SELECT password_hash FROM employees --",
]


@pytest.mark.parametrize("payload", PAYLOADS)
@pytest.mark.parametrize("path", ["/products", "/retailers", "/branches"])
def test_sql_injection_in_search_finds_nothing(login, path, payload):
    client = login("Viewer")
    r = client.get(path, params={"search": payload})
    assert r.status_code == 200
    assert r.json()["total"] == 0          # treated as plain text, not as SQL


@pytest.mark.parametrize("payload", PAYLOADS)
def test_sql_injection_in_login_fails(client, payload):
    r = client.post("/auth/login", json={"email": payload, "password": payload})
    assert r.status_code == 401


def test_tables_survived_the_attacks(login):
    assert login("Viewer").get("/products").json()["total"] > 0


@pytest.mark.parametrize("param,value", [
    ("sort", "name; DROP TABLE products"),
    ("order", "asc; DELETE FROM products"),
    ("page_size", "1000"),
    ("page", "0"),
])
def test_bad_sort_and_paging_values_are_refused(login, param, value):
    assert login("Viewer").get("/products", params={param: value}).status_code == 422


# ----------------------------------------------------------------------
# 4. Roles: who may do what
# ----------------------------------------------------------------------
PROTECTED_GETS = ["/products", "/retailers", "/branches", "/areas", "/orders",
                  "/dashboard", "/employees", "/activity-log", "/auth/me"]


@pytest.mark.parametrize("path", PROTECTED_GETS)
def test_everything_needs_a_login(client, path):
    assert client.get(path).status_code == 401


NEW_PRODUCT = {"category_id": 1, "name": "ZZ Role Test", "pack_size": 6, "unit_price": 10}


@pytest.mark.parametrize("role,method,path,body,expected", [
    ("Viewer",  "post",   "/products",     NEW_PRODUCT, 403),
    ("Viewer",  "get",    "/products",     None,        200),
    ("Editor",  "delete", "/products/1",   None,        403),
    ("Editor",  "get",    "/activity-log", None,        403),
    ("Editor",  "get",    "/employees",    None,        403),
    ("Manager", "get",    "/activity-log", None,        200),
    ("Manager", "get",    "/employees",    None,        403),
    ("Admin",   "get",    "/employees",    None,        200),
    ("Admin",   "get",    "/activity-log", None,        200),
])
def test_role_permissions(login, role, method, path, body, expected):
    client = login(role)
    r = getattr(client, method)(path, **({"json": body} if body else {}))
    assert r.status_code == expected


def test_admin_cannot_lock_themselves_out(login, client):
    login("Admin")
    me = client.get("/auth/me").json()
    assert client.patch(f"/employees/{me['employee_id']}", json={"is_active": False}).status_code == 400


# ----------------------------------------------------------------------
# 5. Safe editing and the activity log
# ----------------------------------------------------------------------
def test_stale_edit_is_refused(login):
    client = login("Editor")
    name = f"ZZ Stale {uuid.uuid4().hex[:6]}"
    product = client.post("/products", json={**NEW_PRODUCT, "name": name}).json()
    first = client.patch(f"/products/{product['product_id']}", json={"unit_price": 20, "version": 1})
    again = client.patch(f"/products/{product['product_id']}", json={"unit_price": 30, "version": 1})
    assert first.status_code == 200 and first.json()["version"] == 2
    assert again.status_code == 409


def test_failed_order_saves_nothing(login):
    client = login("Editor")
    before = client.get("/orders").json()["total"]
    r = client.post("/orders", json={
        "retailer_id": 1, "order_date": "2026-09-01",
        "items": [{"product_id": 1, "cartons": 1}, {"product_id": 999999, "cartons": 1}],
    })
    assert r.status_code == 422
    assert client.get("/orders").json()["total"] == before


def test_activity_log_records_who_made_the_change(login, client):
    editor = login("Editor")
    name = f"ZZ Log {uuid.uuid4().hex[:6]}"
    product = editor.post("/products", json={**NEW_PRODUCT, "name": name}).json()
    client.cookies.clear()
    login("Manager")
    log = client.get("/activity-log", params={
        "table_name": "products", "record_id": product["product_id"]}).json()
    assert log["items"][0]["action"] == "INSERT"
    assert log["items"][0]["employee"] == "Test Editor"


def test_activity_log_cannot_be_changed_or_deleted():
    with pool.connection() as conn:
        # the trigger says "append-only"; the limited app user is stopped even earlier
        with pytest.raises(psycopg.Error, match="append-only|permission denied"):
            conn.execute("DELETE FROM activity_log")


# ----------------------------------------------------------------------
# 6. Headers
# ----------------------------------------------------------------------
def test_security_headers_are_sent(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert r.headers["cache-control"] == "no-store"


# ----------------------------------------------------------------------
# 6b. The web pages themselves
# ----------------------------------------------------------------------
def test_pages_are_served_with_a_strict_policy(client):
    page = client.get("/")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    policy = page.headers["content-security-policy"]
    assert "script-src 'self'" in policy         # no scripts from other websites
    assert "frame-ancestors 'none'" in policy    # cannot be put in a hidden frame
    assert "unsafe-inline" not in policy         # no inline scripts or styles


def test_javascript_files_have_the_right_type(client):
    r = client.get("/js/app.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]


def test_pages_never_use_inline_scripts_or_handlers():
    from pathlib import Path
    folder = Path(__file__).resolve().parents[2] / "frontend"
    for file in list(folder.rglob("*.html")) + list(folder.rglob("*.js")):
        text = file.read_text(encoding="utf-8")
        assert "innerHTML" not in text, f"{file.name} uses innerHTML (XSS risk)"
        assert "eval(" not in text, f"{file.name} uses eval"
    index = (folder / "index.html").read_text(encoding="utf-8")
    assert " onclick=" not in index and "<style" not in index


def test_login_tells_the_page_what_the_user_may_do(client, users):
    r = client.post("/auth/login", json={"email": users["Viewer"], "password": PASSWORD})
    body = r.json()
    assert (body["can_edit"], body["can_delete"], body["can_manage"]) == (False, False, False)


# ----------------------------------------------------------------------
# 7. The app's own database user has limited power
#    (skipped while you still use the all-powerful "postgres" user)
# ----------------------------------------------------------------------
@pytest.mark.skipif(settings.db_user == "postgres", reason="app still uses the postgres superuser")
@pytest.mark.parametrize("sql", [
    "DROP TABLE products",
    "DELETE FROM products",
    "TRUNCATE orders",
    "UPDATE roles SET can_delete = TRUE",
    "UPDATE activity_log SET action = 'INSERT'",
    "CREATE TABLE hacked (id int)",
])
def test_app_database_user_is_limited(sql):
    with pool.connection() as conn:
        with pytest.raises(psycopg.Error, match="permission denied|must be owner"):
            conn.execute(sql)

# ----------------------------------------------------------------------
# 8. Request-origin and host protections (CSRF / DNS rebinding)
# ----------------------------------------------------------------------
def test_cross_site_write_is_refused(client):
    r = client.post("/auth/logout", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Cross-site request blocked."


def test_same_origin_write_is_allowed(client):
    r = client.post("/auth/logout", headers={"Origin": "http://testserver"})
    assert r.status_code == 200


def test_sec_fetch_site_cross_site_is_refused(client):
    r = client.post(
        "/auth/logout",
        headers={"Origin": "http://testserver", "Sec-Fetch-Site": "cross-site"},
    )
    assert r.status_code == 403


def test_unknown_host_header_is_rejected(client):
    r = client.get("/health", headers={"Host": "attacker.example"})
    assert r.status_code == 400


def test_extra_browser_protections_are_sent(client):
    r = client.get("/health")
    assert r.headers["cross-origin-opener-policy"] == "same-origin"
    assert r.headers["cross-origin-resource-policy"] == "same-origin"
    assert r.headers["x-permitted-cross-domain-policies"] == "none"


def test_hsts_is_sent_only_when_cookies_are_secure(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "cookie_secure", True)
    assert client.get("/health").headers["strict-transport-security"].startswith("max-age=")

    monkeypatch.setattr(settings, "cookie_secure", False)
    assert "strict-transport-security" not in client.get("/health").headers
