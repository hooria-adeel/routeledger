"""Creates the first Administrator from environment variables, once.

Used by the Docker image so a fresh deployment has a working login without
an interactive prompt. If any employee already exists, it does nothing, so it
is safe to run on every container start.

Environment:
    ADMIN_EMAIL     (default admin@routeledger.example)
    ADMIN_PASSWORD  required to create the first account
    ADMIN_NAME      (default RouteLedger Admin)
"""
import os
import sys
import time

from app.database import pool
from app.security import check_password_strength, hash_password

EMAIL = os.environ.get("ADMIN_EMAIL", "admin@routeledger.example")
NAME = os.environ.get("ADMIN_NAME", "RouteLedger Admin")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


def main() -> int:
    if not PASSWORD:
        print("  ADMIN_PASSWORD not set; skipping admin creation.")
        return 0

    problem = check_password_strength(PASSWORD)
    if problem:
        raise SystemExit(f"ADMIN_PASSWORD is too weak: {problem}")

    pool.open()
    try:
        for attempt in range(1, 31):
            try:
                with pool.connection() as conn:
                    existing = conn.execute("SELECT count(*) FROM employees").fetchone()["count"]
                    if existing:
                        print("  employees already exist; admin creation skipped.")
                        return 0
                    role = conn.execute(
                        "SELECT role_id FROM roles WHERE name = 'Admin'"
                    ).fetchone()
                    if role is None:
                        raise SystemExit("The roles table is empty; run bootstrap_db first.")
                    conn.execute(
                        "INSERT INTO employees (role_id, full_name, email, password_hash) "
                        "VALUES (%s, %s, %s, %s)",
                        (role["role_id"], NAME, EMAIL, hash_password(PASSWORD)),
                    )
                    print(f"  created first admin: {EMAIL}")
                    return 0
            except Exception as error:  # database still starting up
                if attempt == 30:
                    raise
                print(f"  waiting for database ({error}); retrying in 2s ...")
                time.sleep(2)
    finally:
        pool.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
