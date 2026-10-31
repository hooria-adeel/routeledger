from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.dependencies import require
from app.utils import page_response

# Managers and Admins can read the log. Nobody can change it (database trigger).
router = APIRouter(prefix="/activity-log", tags=["Activity Log"])


@router.get("")
def list_activity(
    table_name: str | None = Query(None, max_length=50),
    record_id: int | None = None,
    employee_id: int | None = None,
    action: str | None = Query(None, pattern="^(INSERT|UPDATE|DELETE)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db=Depends(get_db),
    user=Depends(require("can_delete")),
):
    where, params = ["TRUE"], []
    if table_name:
        where.append("l.table_name = %s")
        params.append(table_name)
    if record_id:
        where.append("l.record_id = %s")
        params.append(record_id)
    if employee_id:
        where.append("l.employee_id = %s")
        params.append(employee_id)
    if action:
        where.append("l.action = %s")
        params.append(action)
    where_sql = " AND ".join(where)

    total = db.execute(
        f"SELECT count(*) AS n FROM activity_log l WHERE {where_sql}", params
    ).fetchone()["n"]
    rows = db.execute(
        f"""
        SELECT l.log_id, l.logged_at, e.full_name AS employee, l.table_name,
               l.record_id, l.action, l.old_value, l.new_value
        FROM activity_log l LEFT JOIN employees e USING (employee_id)
        WHERE {where_sql}
        ORDER BY l.log_id DESC
        LIMIT %s OFFSET %s
        """,
        params + [page_size, (page - 1) * page_size],
    ).fetchall()
    return page_response(rows, total, page, page_size)