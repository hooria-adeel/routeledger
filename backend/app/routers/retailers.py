from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.dependencies import get_current_user, require
from app.schemas import BranchCreate, BranchUpdate, RetailerCreate, RetailerUpdate
from app.utils import (
    friendly_db_errors,
    like_pattern,
    page_response,
    restore_row,
    soft_delete,
    update_row,
)

router = APIRouter(tags=["Retailers and Branches"])

SORT = {"name": "r.name", "branches": "branch_count", "sales": "total_sales"}


@router.get("/retailers")
def list_retailers(
    search: str | None = Query(None, max_length=100),
    sort: Literal["name", "branches", "sales"] = "name",
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    where, params = ["NOT r.is_deleted"], []
    if search:
        where.append("r.name ILIKE %s")
        params.append(like_pattern(search))
    where_sql = " AND ".join(where)

    total = db.execute(
        f"SELECT count(*) AS n FROM retailers r WHERE {where_sql}", params
    ).fetchone()["n"]

    direction = "DESC" if order == "desc" else "ASC"
    rows = db.execute(
        f"""
        SELECT r.retailer_id, r.name, r.version,
               (SELECT count(*) FROM branches b
                 WHERE b.retailer_id = r.retailer_id AND NOT b.is_deleted) AS branch_count,
               COALESCE((SELECT SUM(i.line_value)
                           FROM orders o JOIN order_items i USING (order_id)
                          WHERE o.retailer_id = r.retailer_id AND NOT o.is_deleted), 0) AS total_sales
        FROM retailers r
        WHERE {where_sql}
        ORDER BY {SORT[sort]} {direction}, r.retailer_id
        LIMIT %s OFFSET %s
        """,
        params + [page_size, (page - 1) * page_size],
    ).fetchall()
    return page_response(rows, total, page, page_size)


@router.get("/retailers/{retailer_id}")
def get_retailer(retailer_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    retailer = db.execute(
        "SELECT retailer_id, name, version FROM retailers "
        "WHERE retailer_id = %s AND NOT is_deleted",
        (retailer_id,),
    ).fetchone()
    if retailer is None:
        raise HTTPException(status_code=404, detail="Retailer not found.")
    retailer["branches"] = db.execute(
        """
        SELECT b.branch_id, b.branch_name, a.area_id, a.name AS area, b.version
        FROM branches b JOIN areas a USING (area_id)
        WHERE b.retailer_id = %s AND NOT b.is_deleted
        ORDER BY a.name
        """,
        (retailer_id,),
    ).fetchall()
    return retailer


@router.get("/branches")
def list_branches(
    retailer_id: int | None = None,
    area_id: int | None = None,
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    where, params = ["NOT b.is_deleted", "NOT r.is_deleted"], []
    if retailer_id:
        where.append("b.retailer_id = %s")
        params.append(retailer_id)
    if area_id:
        where.append("b.area_id = %s")
        params.append(area_id)
    if search:
        where.append("(r.name ILIKE %s OR b.branch_name ILIKE %s OR a.name ILIKE %s)")
        params += [like_pattern(search)] * 3
    where_sql = " AND ".join(where)

    base = """FROM branches b JOIN retailers r USING (retailer_id)
              JOIN areas a ON a.area_id = b.area_id"""
    total = db.execute(f"SELECT count(*) AS n {base} WHERE {where_sql}", params).fetchone()["n"]
    rows = db.execute(
        f"""
        SELECT b.branch_id, r.retailer_id, r.name AS retailer, b.branch_name,
               a.area_id, a.name AS area, b.version
        {base} WHERE {where_sql}
        ORDER BY r.name, a.name
        LIMIT %s OFFSET %s
        """,
        params + [page_size, (page - 1) * page_size],
    ).fetchall()
    return page_response(rows, total, page, page_size)


def branch_row(db, branch_id: int):
    row = db.execute(
        """
        SELECT b.branch_id, r.retailer_id, r.name AS retailer, b.branch_name,
               a.area_id, a.name AS area, b.version
        FROM branches b JOIN retailers r USING (retailer_id)
        JOIN areas a ON a.area_id = b.area_id
        WHERE b.branch_id = %s AND NOT b.is_deleted
        """,
        (branch_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Branch not found.")
    return row


# ----------------------------- retailers -----------------------------
@router.post("/retailers", status_code=201)
def create_retailer(
    data: RetailerCreate, db=Depends(get_db), user=Depends(require("can_edit"))
):
    with friendly_db_errors():
        new = db.execute(
            "INSERT INTO retailers (name) VALUES (%s) RETURNING retailer_id", (data.name,)
        ).fetchone()
    return get_retailer(new["retailer_id"], db, user)


@router.patch("/retailers/{retailer_id}")
def update_retailer(
    retailer_id: int,
    data: RetailerUpdate,
    db=Depends(get_db),
    user=Depends(require("can_edit")),
):
    changes = {k: v for k, v in data.model_dump(exclude_unset=True, exclude={"version"}).items() if v is not None}
    update_row(db, "retailers", "retailer_id", retailer_id, data.version, changes)
    return get_retailer(retailer_id, db, user)


@router.delete("/retailers/{retailer_id}")
def delete_retailer(
    retailer_id: int, db=Depends(get_db), user=Depends(require("can_delete"))
):
    if db.execute(
        "SELECT 1 FROM branches WHERE retailer_id = %s AND NOT is_deleted", (retailer_id,)
    ).fetchone():
        raise HTTPException(
            status_code=409, detail="This retailer still has branches. Delete them first."
        )
    soft_delete(db, "retailers", "retailer_id", retailer_id)
    return {"message": "Retailer deleted (it can be restored)."}


@router.post("/retailers/{retailer_id}/restore")
def restore_retailer(
    retailer_id: int, db=Depends(get_db), user=Depends(require("can_delete"))
):
    restore_row(db, "retailers", "retailer_id", retailer_id)
    return get_retailer(retailer_id, db, user)


# ------------------------------ branches ------------------------------
@router.post("/branches", status_code=201)
def create_branch(
    data: BranchCreate, db=Depends(get_db), user=Depends(require("can_edit"))
):
    for table, col, value, label in (
        ("retailers", "retailer_id", data.retailer_id, "Retailer"),
        ("areas", "area_id", data.area_id, "Area"),
    ):
        if db.execute(
            f"SELECT 1 FROM {table} WHERE {col} = %s AND NOT is_deleted", (value,)
        ).fetchone() is None:
            raise HTTPException(status_code=422, detail=f"{label} not found.")
    with friendly_db_errors():
        new = db.execute(
            "INSERT INTO branches (retailer_id, area_id, branch_name) "
            "VALUES (%s, %s, %s) RETURNING branch_id",
            (data.retailer_id, data.area_id, data.branch_name),
        ).fetchone()
    return branch_row(db, new["branch_id"])


@router.patch("/branches/{branch_id}")
def update_branch(
    branch_id: int,
    data: BranchUpdate,
    db=Depends(get_db),
    user=Depends(require("can_edit")),
):
    changes = {k: v for k, v in data.model_dump(exclude_unset=True, exclude={"version"}).items() if v is not None}
    update_row(db, "branches", "branch_id", branch_id, data.version, changes)
    return branch_row(db, branch_id)


@router.delete("/branches/{branch_id}")
def delete_branch(
    branch_id: int, db=Depends(get_db), user=Depends(require("can_delete"))
):
    soft_delete(db, "branches", "branch_id", branch_id)
    return {"message": "Branch deleted (it can be restored)."}


@router.post("/branches/{branch_id}/restore")
def restore_branch(
    branch_id: int, db=Depends(get_db), user=Depends(require("can_delete"))
):
    restore_row(db, "branches", "branch_id", branch_id)
    return branch_row(db, branch_id)