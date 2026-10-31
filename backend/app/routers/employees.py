from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.dependencies import require
from app.schemas import EmployeeCreate, EmployeeUpdate
from app.security import check_password_strength, hash_password

# Every route here is for Admins only (the "can_manage" permission).
router = APIRouter(prefix="/employees", tags=["Employees (Admin)"])

SELECT_EMPLOYEE = """
    SELECT e.employee_id, e.full_name, e.email, r.name AS role, e.is_active,
           e.last_login_at, (e.locked_until IS NOT NULL AND e.locked_until > now()) AS is_locked
    FROM employees e JOIN roles r USING (role_id)
"""


def role_id_for(db, role_name: str) -> int:
    row = db.execute("SELECT role_id FROM roles WHERE name = %s", (role_name,)).fetchone()
    if row is None:
        raise HTTPException(status_code=422, detail=f"Unknown role: {role_name}")
    return row["role_id"]


@router.get("")
def list_employees(db=Depends(get_db), admin=Depends(require("can_manage"))):
    return db.execute(SELECT_EMPLOYEE + " ORDER BY e.full_name").fetchall()


@router.get("/roles")
def list_roles(db=Depends(get_db), admin=Depends(require("can_manage"))):
    return db.execute(
        "SELECT role_id, name, description, can_edit, can_delete, can_manage "
        "FROM roles ORDER BY role_id"
    ).fetchall()


@router.post("", status_code=201)
def create_employee(
    data: EmployeeCreate, db=Depends(get_db), admin=Depends(require("can_manage"))
):
    problem = check_password_strength(data.password)
    if problem:
        raise HTTPException(status_code=422, detail=problem)
    role_id = role_id_for(db, data.role)
    if db.execute(
        "SELECT 1 FROM employees WHERE lower(email) = lower(%s)", (data.email,)
    ).fetchone():
        raise HTTPException(status_code=409, detail="This email is already used.")
    new = db.execute(
        "INSERT INTO employees (role_id, full_name, email, password_hash) "
        "VALUES (%s, %s, %s, %s) RETURNING employee_id",
        (role_id, data.full_name.strip(), data.email.strip(), hash_password(data.password)),
    ).fetchone()
    return db.execute(
        SELECT_EMPLOYEE + " WHERE e.employee_id = %s", (new["employee_id"],)
    ).fetchone()


@router.patch("/{employee_id}")
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db=Depends(get_db),
    admin=Depends(require("can_manage")),
):
    if db.execute(
        "SELECT 1 FROM employees WHERE employee_id = %s", (employee_id,)
    ).fetchone() is None:
        raise HTTPException(status_code=404, detail="Employee not found.")

    # An admin must not lock themselves out by mistake.
    if employee_id == admin["employee_id"] and (
        data.is_active is False or (data.role and data.role != "Admin")
    ):
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate yourself or remove your own Admin role.",
        )

    if data.role is not None:
        db.execute(
            "UPDATE employees SET role_id = %s WHERE employee_id = %s",
            (role_id_for(db, data.role), employee_id),
        )
    if data.is_active is not None:
        db.execute(
            "UPDATE employees SET is_active = %s WHERE employee_id = %s",
            (data.is_active, employee_id),
        )
    if data.new_password is not None:
        problem = check_password_strength(data.new_password)
        if problem:
            raise HTTPException(status_code=422, detail=problem)
        db.execute(
            "UPDATE employees SET password_hash = %s, failed_attempts = 0, "
            "locked_until = NULL WHERE employee_id = %s",
            (hash_password(data.new_password), employee_id),
        )
    return db.execute(SELECT_EMPLOYEE + " WHERE e.employee_id = %s", (employee_id,)).fetchone()