from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.dependencies import get_current_user, require
from app.schemas import AreaCreate, AreaUpdate
from app.utils import friendly_db_errors, restore_row, soft_delete, update_row

router = APIRouter(prefix="/areas", tags=["Areas"])


@router.get("")
def list_areas(db=Depends(get_db), user=Depends(get_current_user)):
    """All areas with how many shops are in each (about 20 rows, so no paging)."""
    return db.execute(
        """
        SELECT a.area_id, a.name, a.district, a.version,
               (SELECT count(*) FROM branches b
                 WHERE b.area_id = a.area_id AND NOT b.is_deleted) AS branch_count
        FROM areas a
        WHERE NOT a.is_deleted
        ORDER BY a.name
        """
    ).fetchall()


@router.get("/{area_id}")
def get_area(area_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    area = db.execute(
        "SELECT area_id, name, district, version FROM areas "
        "WHERE area_id = %s AND NOT is_deleted",
        (area_id,),
    ).fetchone()
    if area is None:
        raise HTTPException(status_code=404, detail="Area not found.")
    area["branches"] = db.execute(
        """
        SELECT b.branch_id, r.name AS retailer, b.branch_name
        FROM branches b JOIN retailers r USING (retailer_id)
        WHERE b.area_id = %s AND NOT b.is_deleted
        ORDER BY r.name
        """,
        (area_id,),
    ).fetchall()
    return area


@router.post("", status_code=201)
def create_area(data: AreaCreate, db=Depends(get_db), user=Depends(require("can_edit"))):
    with friendly_db_errors():
        new = db.execute(
            "INSERT INTO areas (name, district) VALUES (%s, %s) RETURNING area_id",
            (data.name, data.district),
        ).fetchone()
    return get_area(new["area_id"], db, user)


@router.patch("/{area_id}")
def update_area(
    area_id: int,
    data: AreaUpdate,
    db=Depends(get_db),
    user=Depends(require("can_edit")),
):
    changes = data.model_dump(exclude_unset=True, exclude={"version"})
    if changes.get("name", "x") is None:
        changes.pop("name")                      # the name cannot be empty
    update_row(db, "areas", "area_id", area_id, data.version, changes)
    return get_area(area_id, db, user)


@router.delete("/{area_id}")
def delete_area(area_id: int, db=Depends(get_db), user=Depends(require("can_delete"))):
    if db.execute(
        "SELECT 1 FROM branches WHERE area_id = %s AND NOT is_deleted", (area_id,)
    ).fetchone():
        raise HTTPException(
            status_code=409, detail="This area still has branches. Move or delete them first."
        )
    soft_delete(db, "areas", "area_id", area_id)
    return {"message": "Area deleted (it can be restored)."}


@router.post("/{area_id}/restore")
def restore_area(area_id: int, db=Depends(get_db), user=Depends(require("can_delete"))):
    restore_row(db, "areas", "area_id", area_id)
    return get_area(area_id, db, user)