from fastapi import Depends, HTTPException, Request

from app.database import get_db
from app.security import read_token

COOKIE_NAME = "access_token"


def get_current_user(request: Request, db=Depends(get_db)):
    """Finds out who is logged in. Use it on any page that needs a login."""
    token = request.cookies.get(COOKIE_NAME)
    employee_id = read_token(token) if token else None
    if employee_id is None:
        raise HTTPException(status_code=401, detail="Please log in.")

    user = db.execute(
        """
        SELECT e.employee_id, e.full_name, e.email, r.name AS role,
               r.can_edit, r.can_delete, r.can_manage
        FROM employees e JOIN roles r USING (role_id)
        WHERE e.employee_id = %s AND e.is_active
        """,
        (employee_id,),
    ).fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in.")
    return user


def require(permission: str):
    """Use it like:  Depends(require("can_edit"))
    The role check happens here in the backend, so hiding a button on the
    page is never the only protection."""
    if permission not in ("can_edit", "can_delete", "can_manage"):
        raise ValueError("Unknown permission")

    def checker(user=Depends(get_current_user), db=Depends(get_db)):
        if not user[permission]:
            raise HTTPException(
                status_code=403, detail="You do not have permission to do this."
            )
        # Tell the database WHO is making changes, so the triggers can write
        # the name into the activity log. "true" = only for this request.
        db.execute(
            "SELECT set_config('app.current_employee_id', %s, true)",
            (str(user["employee_id"]),),
        )
        return user

    return checker