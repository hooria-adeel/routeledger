"""Creates or updates the RouteLedger database from the SQL files.

Safe to run more than once: it only loads the schema and seed data when the
database is still empty, and it always makes sure the limited application
user exists with the password from the environment.

Run from the ``backend`` folder (or automatically in the Docker image)::

    python -m scripts.bootstrap_db

Environment:
    ADMIN_DATABASE_URL   full admin connection string (takes priority)
    or DB_HOST / DB_PORT / DB_NAME / ADMIN_DB_USER / ADMIN_DB_PASSWORD
    DB_USER              name of the limited application role (default routeledger_app)
    DB_PASSWORD          password for that limited role (required)
"""
import os
import sys
import time
from pathlib import Path

import psycopg
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo

ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = ROOT / "database"

APP_USER = os.environ.get("DB_USER", "routeledger_app")
APP_PASSWORD = os.environ.get("DB_PASSWORD", "")

# Least privilege: exactly the grants documented in database/create_app_user.sql.
GRANTS = (
    "GRANT USAGE ON SCHEMA public TO {role}",
    "GRANT SELECT ON ALL TABLES IN SCHEMA public TO {role}",
    "GRANT INSERT, UPDATE ON products, retailers, branches, areas, orders, "
    "order_items, employees TO {role}",
    "GRANT INSERT ON activity_log, product_price_history TO {role}",
    "GRANT DELETE ON order_items TO {role}",
    "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {role}",
)


def admin_conninfo() -> str:
    url = os.environ.get("ADMIN_DATABASE_URL")
    if url:
        return url
    password = os.environ.get("ADMIN_DB_PASSWORD")
    if not password:
        raise SystemExit(
            "Set ADMIN_DATABASE_URL or ADMIN_DB_PASSWORD so the schema can be loaded."
        )
    return make_conninfo(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "routeledger"),
        user=os.environ.get("ADMIN_DB_USER", "postgres"),
        password=password,
    )


def run_file(conn, name: str) -> None:
    path = DATABASE_DIR / name
    print(f"  loading {name} ...")
    conn.execute(path.read_text(encoding="utf-8"))


def connect_with_retry(conninfo: str, attempts: int = 30) -> psycopg.Connection:
    for attempt in range(1, attempts + 1):
        try:
            return psycopg.connect(conninfo, autocommit=True)
        except psycopg.OperationalError as error:
            if attempt == attempts:
                raise
            print(f"  database not ready ({error}); retrying in 2s ...")
            time.sleep(2)
    raise RuntimeError("unreachable")


def ensure_app_role(conn) -> None:
    try:
        conn.execute(
            sql.SQL(
                "CREATE ROLE {role} LOGIN PASSWORD {password} "
                "NOSUPERUSER NOCREATEDB NOCREATEROLE"
            ).format(role=sql.Identifier(APP_USER), password=sql.Literal(APP_PASSWORD))
        )
        print(f"  created limited role {APP_USER!r}")
    except errors.DuplicateObject:
        conn.execute(
            sql.SQL("ALTER ROLE {role} WITH LOGIN PASSWORD {password}").format(
                role=sql.Identifier(APP_USER), password=sql.Literal(APP_PASSWORD)
            )
        )
        print(f"  updated password for existing role {APP_USER!r}")

    for statement in GRANTS:
        conn.execute(sql.SQL(statement).format(role=sql.Identifier(APP_USER)))


def main() -> int:
    if not APP_PASSWORD:
        raise SystemExit("DB_PASSWORD is required (password for the limited app role).")

    with connect_with_retry(admin_conninfo()) as conn:
        schema_exists = conn.execute(
            "SELECT to_regclass('public.products') IS NOT NULL"
        ).fetchone()[0]

        if not schema_exists:
            run_file(conn, "schema.sql")

        products = conn.execute("SELECT count(*) FROM products").fetchone()[0]
        if products == 0:
            run_file(conn, "seed.sql")

        # seed.sql creates 60 orders (ids 1-60); the demo file adds 400 more
        # (ids 61+) so the dashboard has a realistic history. A production
        # install can set LOAD_DEMO_DATA=false and keep only the base seed.
        load_demo = os.environ.get("LOAD_DEMO_DATA", "true").lower() not in (
            "0", "false", "no",
        )
        demo_loaded = conn.execute(
            "SELECT COALESCE(max(order_id), 0) >= 61 FROM orders"
        ).fetchone()[0]
        if load_demo and not demo_loaded:
            run_file(conn, "seed_demo_orders.sql")

        ensure_app_role(conn)

        totals = conn.execute(
            "SELECT (SELECT count(*) FROM products), (SELECT count(*) FROM orders)"
        ).fetchone()
        print(f"  database ready: {totals[0]} products, {totals[1]} orders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
