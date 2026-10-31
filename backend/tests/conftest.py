import os
import uuid

# SAFETY: the tests must never touch the real "routeledger" database.
os.environ["DB_NAME"] = "routeledger_test"

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import pool
from app.main import app
from app.middleware import login_limiter
from scripts.create_admin import create_employee

assert settings.db_name == "routeledger_test", "Tests may only run on the routeledger_test database"

PASSWORD = "Test-Pass-2026-Ok"
ROLES = ("Admin", "Manager", "Editor", "Viewer")


@pytest.fixture(scope="session", autouse=True)
def open_pool():
    pool.open()
    yield
    pool.close()


@pytest.fixture(scope="session")
def users(open_pool):
    """One test employee per role (new email each run, so the tests can be repeated)."""
    suffix = uuid.uuid4().hex[:8]
    made = {}
    with pool.connection() as conn:
        for role in ROLES:
            email = f"test-{role.lower()}-{suffix}@routeledger.test"
            create_employee(conn, f"Test {role}", email, PASSWORD, role)
            made[role] = email
    return made


@pytest.fixture(autouse=True)
def reset_rate_limit():
    login_limiter.calls.clear()
    yield
    login_limiter.calls.clear()


@pytest.fixture
def client():
    return TestClient(app)          # a new browser with no cookies


@pytest.fixture
def login(client, users):
    def do(role):
        r = client.post("/auth/login", json={"email": users[role], "password": PASSWORD})
        assert r.status_code == 200, r.text
        return client
    return do


@pytest.fixture
def new_user():
    """Makes a throw-away employee, for tests that lock or deactivate accounts."""
    def make(role="Viewer"):
        email = f"temp-{uuid.uuid4().hex[:10]}@routeledger.test"
        with pool.connection() as conn:
            employee_id = create_employee(conn, "Temp User", email, PASSWORD, role)
        return employee_id, email
    return make