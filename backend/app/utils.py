from contextlib import contextmanager

import psycopg.errors as pg
from fastapi import HTTPException


def like_pattern(text: str) -> str:
    """Prepares search text for 'contains' searching.
    The symbols % and _ are treated as normal letters, not as wildcards."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def page_response(items, total, page, page_size):
    """Every list returns the same shape, so the frontend can reuse one table."""
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@contextmanager
def friendly_db_errors():
    """Turns database complaints into clear messages for the user."""
    try:
        yield
    except pg.SerializationFailure:
        # raised by our version trigger in schema.sql
        raise HTTPException(
            status_code=409,
            detail="Someone else changed this record while you were editing. "
                   "Reload it and try again.",
        )
    except pg.UniqueViolation:
        raise HTTPException(status_code=409, detail="This value already exists.")
    except pg.ForeignKeyViolation:
        raise HTTPException(status_code=422, detail="A linked record does not exist.")
    except (pg.CheckViolation, pg.NotNullViolation):
        raise HTTPException(status_code=422, detail="A value is missing or not allowed.")


def update_row(db, table, id_col, row_id, version, changes, soft_delete_column=True):
    """Changes one row. Table and column names come from our own code, never
    from the user. The user's version is sent along: if the row was changed
    by someone else in the meantime, the database trigger refuses the update."""
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to change.")
    sets = ", ".join(f"{col} = %s" for col in changes) + ", version = %s"
    extra = " AND NOT is_deleted" if soft_delete_column else ""
    with friendly_db_errors():
        cur = db.execute(
            f"UPDATE {table} SET {sets} WHERE {id_col} = %s{extra}",
            [*changes.values(), version, row_id],
        )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Record not found.")


def soft_delete(db, table, id_col, row_id):
    """Hides a record instead of destroying it, so it can be restored."""
    cur = db.execute(
        f"UPDATE {table} SET is_deleted = TRUE WHERE {id_col} = %s AND NOT is_deleted",
        (row_id,),
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Record not found.")


def restore_row(db, table, id_col, row_id):
    cur = db.execute(
        f"UPDATE {table} SET is_deleted = FALSE WHERE {id_col} = %s AND is_deleted",
        (row_id,),
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="No deleted record with this id.")