"""Tests for the database itself: constraints, triggers, views and transactions.

These tests talk to PostgreSQL directly (not through the API) so they prove
that the rules hold even if an endpoint forgets them.
"""
import uuid
from datetime import date

import psycopg.errors as pg
import pytest

from app.database import pool


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def scalar(sql, params=()):
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchone()


@pytest.fixture(scope="module")
def catalogue():
    """An area, retailer, branch, category and product that the tests may use."""
    suffix = uuid.uuid4().hex[:8]
    with pool.connection() as conn:
        category = conn.execute(
            "SELECT category_id FROM categories ORDER BY category_id LIMIT 1"
        ).fetchone()["category_id"]
        area = conn.execute(
            "INSERT INTO areas (name, district) VALUES (%s, 'Test District') RETURNING area_id",
            (unique(f"Test Area {suffix}"),),
        ).fetchone()["area_id"]
        retailer = conn.execute(
            "INSERT INTO retailers (name) VALUES (%s) RETURNING retailer_id",
            (unique(f"Test Retailer {suffix}"),),
        ).fetchone()["retailer_id"]
        branch = conn.execute(
            "INSERT INTO branches (retailer_id, area_id, branch_name) "
            "VALUES (%s, %s, 'Main') RETURNING branch_id",
            (retailer, area),
        ).fetchone()["branch_id"]
        product = conn.execute(
            "INSERT INTO products (category_id, name, pack_size, unit_price) "
            "VALUES (%s, %s, 12, 100) RETURNING product_id, version",
            (category, unique(f"Test Product {suffix}")),
        ).fetchone()
    return {
        "category": category,
        "area": area,
        "retailer": retailer,
        "branch": branch,
        "product": product["product_id"],
        "version": product["version"],
    }


# ----------------------------------------------------------------------
# Schema objects
# ----------------------------------------------------------------------
def test_expected_views_exist():
    rows = scalar(
        "SELECT count(*) FROM information_schema.views "
        "WHERE table_schema = 'public' AND table_name ~ '^v_'"
    )
    assert rows["count"] == 7


def test_every_business_table_has_an_audit_trigger():
    rows = scalar(
        "SELECT count(DISTINCT c.relname) AS count FROM pg_trigger t "
        "JOIN pg_class c ON c.oid = t.tgrelid "
        "WHERE NOT t.tgisinternal AND t.tgname ~ '^trg_audit_'"
    )
    assert rows["count"] == 7


def test_version_triggers_cover_every_mutable_table():
    rows = scalar(
        "SELECT count(DISTINCT c.relname) AS tables FROM pg_trigger t "
        "JOIN pg_class c ON c.oid = t.tgrelid "
        "WHERE NOT t.tgisinternal AND t.tgname ~ '^trg_touch_'"
    )
    assert rows["tables"] == 7


def test_trigram_extension_and_indexes_exist():
    ext = scalar("SELECT count(*) FROM pg_extension WHERE extname = 'pg_trgm'")
    assert ext["count"] == 1
    idx = scalar(
        "SELECT count(*) FROM pg_indexes WHERE schemaname = 'public' "
        "AND indexname IN ('idx_products_name_trgm', 'idx_retailers_name_trgm')"
    )
    assert idx["count"] == 2


def test_four_roles_are_seeded_with_the_right_flags():
    rows = scalar(
        "SELECT count(*) FILTER (WHERE can_edit) AS editors, "
        "count(*) FILTER (WHERE can_delete) AS deleters, "
        "count(*) FILTER (WHERE can_manage) AS managers FROM roles"
    )
    assert rows["editors"] == 3      # Editor, Manager, Admin
    assert rows["deleters"] == 2     # Manager, Admin
    assert rows["managers"] == 1     # Admin


# ----------------------------------------------------------------------
# Constraints
# ----------------------------------------------------------------------
def test_negative_price_is_refused(catalogue):
    with pytest.raises(pg.CheckViolation):
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO products (category_id, name, pack_size, unit_price) "
                "VALUES (%s, %s, 1, -1)",
                (catalogue["category"], unique("Negative")),
            )


def test_pack_size_must_be_positive(catalogue):
    with pytest.raises(pg.CheckViolation):
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO products (category_id, name, pack_size, unit_price) "
                "VALUES (%s, %s, 0, 10)",
                (catalogue["category"], unique("Zero Pack")),
            )


def test_product_names_are_unique(catalogue):
    with pool.connection() as conn:
        name = conn.execute(
            "SELECT name FROM products WHERE product_id = %s", (catalogue["product"],)
        ).fetchone()["name"]
    with pytest.raises(pg.UniqueViolation):
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO products (category_id, name, pack_size, unit_price) "
                "VALUES (%s, %s, 1, 10)",
                (catalogue["category"], name),
            )


def test_branch_name_is_unique_only_within_a_retailer(catalogue):
    # same branch name for a different retailer is allowed
    with pool.connection() as conn:
        other = conn.execute(
            "INSERT INTO retailers (name) VALUES (%s) RETURNING retailer_id",
            (unique("Second Retailer"),),
        ).fetchone()["retailer_id"]
        conn.execute(
            "INSERT INTO branches (retailer_id, area_id, branch_name) VALUES (%s, %s, 'Main')",
            (other, catalogue["area"]),
        )
    # a duplicate inside the same retailer is not
    with pytest.raises(pg.UniqueViolation):
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO branches (retailer_id, area_id, branch_name) VALUES (%s, %s, 'Main')",
                (catalogue["retailer"], catalogue["area"]),
            )


def test_email_format_is_checked():
    with pytest.raises(pg.CheckViolation):
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO employees (role_id, full_name, email, password_hash) "
                "VALUES (1, 'Bad Email', 'not-an-email', 'x')"
            )


# ----------------------------------------------------------------------
# Triggers
# ----------------------------------------------------------------------
def test_version_increases_and_stale_edits_are_refused(catalogue):
    with pool.connection() as conn:
        conn.execute(
            "UPDATE products SET unit_price = unit_price, version = %s WHERE product_id = %s",
            (catalogue["version"], catalogue["product"]),
        )
        version = conn.execute(
            "SELECT version FROM products WHERE product_id = %s", (catalogue["product"],)
        ).fetchone()["version"]
    assert version == catalogue["version"] + 1

    # sending the OLD version again must fail
    with pytest.raises(pg.SerializationFailure):
        with pool.connection() as conn:
            conn.execute(
                "UPDATE products SET unit_price = 999, version = %s WHERE product_id = %s",
                (catalogue["version"], catalogue["product"]),
            )


def test_price_change_is_written_to_history(catalogue):
    with pool.connection() as conn:
        current = conn.execute(
            "SELECT unit_price, version FROM products WHERE product_id = %s",
            (catalogue["product"],),
        ).fetchone()
        new_price = current["unit_price"] + 5
        conn.execute(
            "UPDATE products SET unit_price = %s, version = %s WHERE product_id = %s",
            (new_price, current["version"], catalogue["product"]),
        )
        history = conn.execute(
            "SELECT old_price, new_price FROM product_price_history "
            "WHERE product_id = %s ORDER BY history_id DESC LIMIT 1",
            (catalogue["product"],),
        ).fetchone()
    assert history["old_price"] == current["unit_price"]
    assert history["new_price"] == new_price


def test_audit_log_records_insert_and_update_with_actor(catalogue):
    with pool.connection() as conn:
        actor = conn.execute("SELECT employee_id FROM employees LIMIT 1").fetchone()
        if actor is None:
            pytest.skip("no employees in the test database")
        conn.execute(
            "SELECT set_config('app.current_employee_id', %s, true)",
            (str(actor["employee_id"]),),
        )
        product = conn.execute(
            "INSERT INTO products (category_id, name, pack_size, unit_price) "
            "VALUES (%s, %s, 6, 50) RETURNING product_id, version",
            (catalogue["category"], unique("Audited Product")),
        ).fetchone()
        conn.execute(
            "UPDATE products SET unit_price = 55 WHERE product_id = %s AND version = %s",
            (product["product_id"], product["version"]),
        )
        logs = conn.execute(
            "SELECT action, employee_id, old_value, new_value FROM activity_log "
            "WHERE table_name = 'products' AND record_id = %s ORDER BY log_id",
            (product["product_id"],),
        ).fetchall()

    assert [row["action"] for row in logs] == ["INSERT", "UPDATE"]
    assert all(row["employee_id"] == actor["employee_id"] for row in logs)
    assert float(logs[1]["old_value"]["unit_price"]) == 50.0
    assert float(logs[1]["new_value"]["unit_price"]) == 55.0


def test_activity_log_is_append_only():
    # The app role has no UPDATE/DELETE grant; the trigger is the second lock.
    with pytest.raises((pg.RaiseException, pg.InsufficientPrivilege)):
        with pool.connection() as conn:
            conn.execute("UPDATE activity_log SET action = 'DELETE' WHERE log_id = 1")
    with pytest.raises((pg.RaiseException, pg.InsufficientPrivilege)):
        with pool.connection() as conn:
            conn.execute("DELETE FROM activity_log WHERE log_id = 1")


# ----------------------------------------------------------------------
# Views and transactions
# ----------------------------------------------------------------------
def test_sales_detail_reconciles_with_order_items():
    detail = scalar(
        "SELECT COALESCE(SUM(line_value), 0) AS total FROM v_sales_detail"
    )["total"]
    raw = scalar(
        "SELECT COALESCE(SUM(i.line_value), 0) AS total FROM order_items i "
        "JOIN orders o USING (order_id) WHERE NOT o.is_deleted"
    )["total"]
    assert detail == raw


def test_monthly_view_totals_match_the_dashboard_source():
    months = scalar(
        "SELECT SUM(total_value) AS total, COUNT(*) AS months FROM v_sales_by_month"
    )
    detail = scalar("SELECT SUM(line_value) AS total FROM v_sales_detail")
    assert months["total"] == detail["total"]
    assert months["months"] > 0


def test_soft_deleted_orders_disappear_from_reports_but_stay_in_the_table():
    with pool.connection() as conn:
        order = conn.execute(
            "SELECT o.order_id, o.version FROM orders o "
            "WHERE NOT o.is_deleted AND EXISTS (SELECT 1 FROM order_items i WHERE i.order_id = o.order_id) "
            "LIMIT 1"
        ).fetchone()
        if order is None:
            pytest.skip("no orders in the test database")
        conn.execute(
            "UPDATE orders SET is_deleted = TRUE WHERE order_id = %s AND version = %s",
            (order["order_id"], order["version"]),
        )
        visible = conn.execute(
            "SELECT count(*) FROM v_sales_detail WHERE order_id = %s", (order["order_id"],)
        ).fetchone()["count"]
        still_there = conn.execute(
            "SELECT count(*) FROM orders WHERE order_id = %s", (order["order_id"],)
        ).fetchone()["count"]
        # restore so other tests and reruns see the same data
        conn.execute(
            "UPDATE orders SET is_deleted = FALSE WHERE order_id = %s",
            (order["order_id"],),
        )
    assert visible == 0
    assert still_there == 1


def test_failed_order_saves_no_rows(catalogue):
    before = scalar("SELECT count(*) AS n FROM orders")["n"]
    with pytest.raises(pg.CheckViolation):
        with pool.connection() as conn:
            with conn.transaction():
                order = conn.execute(
                    "INSERT INTO orders (retailer_id, branch_id, order_date) "
                    "VALUES (%s, %s, %s) RETURNING order_id",
                    (catalogue["retailer"], catalogue["branch"], date.today()),
                ).fetchone()
                conn.execute(
                    "INSERT INTO order_items (order_id, product_id, cartons, carton_price, line_value) "
                    "VALUES (%s, %s, 0, 100, 0)",
                    (order["order_id"], catalogue["product"]),
                )
    after = scalar("SELECT count(*) AS n FROM orders")["n"]
    assert after == before
