"""Sets a new password for an existing employee and unlocks the account.
Run from the backend folder:   python -m scripts.reset_password
"""
import getpass

from app.database import pool
from app.security import check_password_strength, hash_password


def main():
    print("Reset an employee's password")
    email = input("Email of the employee: ").strip()
    password = getpass.getpass("New password (hidden while typing): ")
    again = getpass.getpass("Type the new password again: ")
    if password != again:
        print("The two passwords do not match. Nothing was changed.")
        return
    problem = check_password_strength(password)
    if problem:
        print(problem, "Nothing was changed.")
        return
    pool.open()
    try:
        with pool.connection() as conn:
            changed = conn.execute(
                "UPDATE employees SET password_hash = %s, failed_attempts = 0, "
                "locked_until = NULL, is_active = TRUE WHERE lower(email) = lower(%s)",
                (hash_password(password), email),
            ).rowcount
        if changed:
            print("Done. The password was changed and the account is unlocked.")
        else:
            print("No employee has that email. Check the spelling and try again.")
    finally:
        pool.close()


if __name__ == "__main__":
    main()