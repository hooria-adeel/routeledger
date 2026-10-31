from fastapi import APIRouter, Depends, HTTPException, Response

from app.config import settings
from app.database import get_db
from app.dependencies import COOKIE_NAME, get_current_user
from app.middleware import login_limiter
from app.schemas import EmployeeOut, LoginRequest
from app.security import DUMMY_HASH, create_token, verify_password

MAX_ATTEMPTS = 5      # wrong passwords allowed
LOCK_MINUTES = 15     # how long the account stays locked

router = APIRouter(prefix="/auth", tags=["Login"])


def bad_login() -> HTTPException:
    # Same message for "no such email" and "wrong password" on purpose.
    return HTTPException(status_code=401, detail="Invalid email or password.")


@router.post("/login", response_model=EmployeeOut, dependencies=[Depends(login_limiter)])
def login(data: LoginRequest, response: Response, db=Depends(get_db)):
    emp = db.execute(
        """
        SELECT e.employee_id, e.full_name, e.email, e.password_hash,
               e.is_active, e.failed_attempts, r.name AS role,
               r.can_edit, r.can_delete, r.can_manage,
               (e.locked_until IS NOT NULL AND e.locked_until > now()) AS is_locked
        FROM employees e JOIN roles r USING (role_id)
        WHERE lower(e.email) = lower(%s)
        """,
        (data.email,),
    ).fetchone()

    if emp is None or not emp["is_active"]:
        verify_password(data.password, DUMMY_HASH)   # keeps the timing equal
        raise bad_login()

    if emp["is_locked"]:
        raise HTTPException(
            status_code=423,
            detail=f"Too many wrong attempts. Account locked for {LOCK_MINUTES} minutes.",
        )

    if not verify_password(data.password, emp["password_hash"]):
        attempts = emp["failed_attempts"] + 1
        if attempts >= MAX_ATTEMPTS:
            db.execute(
                "UPDATE employees SET failed_attempts = 0, "
                "locked_until = now() + (%s * interval '1 minute') WHERE employee_id = %s",
                (LOCK_MINUTES, emp["employee_id"]),
            )
        else:
            db.execute(
                "UPDATE employees SET failed_attempts = %s WHERE employee_id = %s",
                (attempts, emp["employee_id"]),
            )
        db.commit()          # save the counter BEFORE raising the error
        raise bad_login()

    db.execute(
        "UPDATE employees SET failed_attempts = 0, locked_until = NULL, "
        "last_login_at = now() WHERE employee_id = %s",
        (emp["employee_id"],),
    )
    response.set_cookie(
        key=COOKIE_NAME,
        value=create_token(emp["employee_id"]),
        httponly=True,                       # JavaScript cannot read it
        samesite="lax",                      # not sent from other websites
        secure=settings.cookie_secure,       # https only when deployed
        max_age=settings.token_minutes * 60,
    )
    return {
        "employee_id": emp["employee_id"],
        "full_name": emp["full_name"],
        "email": emp["email"],
        "role": emp["role"],
        "can_edit": emp["can_edit"],
        "can_delete": emp["can_delete"],
        "can_manage": emp["can_manage"],
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"message": "Logged out."}


@router.get("/me", response_model=EmployeeOut)
def me(user=Depends(get_current_user)):
    """Who am I? The pages use this to show the name and decide which buttons to show."""
    return user
