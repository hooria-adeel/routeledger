"""Creates an employee from the terminal.
Run from the backend folder:   python -m scripts.create_admin
"""
import getpass

from app.database import pool
from app.security import check_password_strength, hash_password


def create_employee(conn, full_name, email, password, role_name):
    problem = check_password_strength(password)
    if problem:
        raise ValueError(problem)
    role = conn.execute("SELECT role_id FROM roles WHERE name = %s", (role_name,)).fetchone()
    if role is None:
        raise ValueError(f"Unknown role: {role_name}")
    if conn.execute("SELECT 1 FROM employees WHERE lower(email) = lower(%s)", (email,)).fetchone():
        raise ValueError("An employee with this email already exists.")
    row = conn.execute(
        "INSERT INTO employees (role_id, full_name, email, password_hash) "
        "VALUES (%s, %s, %s, %s) RETURNING employee_id",
        (role["role_id"], full_name, email, hash_password(password)),
    ).fetchone()
    return row["employee_id"]


def main():
    print("Create the first Admin employee")
    full_name = input("Full name: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password (hidden while typing): ")
    again = getpass.getpass("Type the password again: ")
    if password != again:
        print("The two passwords do not match.")
        return
    pool.open()
    try:
        with pool.connection() as conn:
            new_id = create_employee(conn, full_name, email, password, "Admin")
        print(f"Done. Admin created with employee_id {new_id}.")
    except ValueError as problem:
        print("Could not create the admin:", problem)
    finally:
        pool.close()


if __name__ == "__main__":
    main()