from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.dependencies import get_current_user, require
from app.schemas import ProductCreate, ProductUpdate
from app.utils import (
    friendly_db_errors,
    like_pattern,
    page_response,
    restore_row,
    soft_delete,
    update_row,
)

router = APIRouter(prefix="/products", tags=["Products"])

# Only these sort choices are allowed (this also blocks SQL injection through sorting).
SORT = {
    "name": "p.name",
    "price": "p.unit_price",
    "category": "c.name",
    "pack_size": "p.pack_size",
}


@router.get("")
def list_products(
    search: str | None = Query(None, max_length=100),
    category_id: int | None = None,
    sort: Literal["name", "price", "category", "pack_size"] = "name",
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    where, params = ["NOT p.is_deleted"], []
    if search:
        where.append("p.name ILIKE %s")
        params.append(like_pattern(search))
    if category_id:
        where.append("p.category_id = %s")
        params.append(category_id)
    where_sql = " AND ".join(where)

    total = db.execute(
        f"SELECT count(*) AS n FROM products p WHERE {where_sql}", params
    ).fetchone()["n"]

    direction = "DESC" if order == "desc" else "ASC"
    rows = db.execute(
        f"""
        SELECT p.product_id, p.name, c.name AS category, p.category_id,
               p.pack_size, p.unit_price,
               ROUND(p.unit_price * p.pack_size, 2) AS carton_price, p.version
        FROM products p JOIN categories c USING (category_id)
        WHERE {where_sql}
        ORDER BY {SORT[sort]} {direction}, p.product_id
        LIMIT %s OFFSET %s
        """,
        params + [page_size, (page - 1) * page_size],
    ).fetchall()
    return page_response(rows, total, page, page_size)


@router.get("/categories")
def list_categories(db=Depends(get_db), user=Depends(get_current_user)):
    """For the category drop-down."""
    return db.execute(
        "SELECT category_id, name FROM categories WHERE NOT is_deleted ORDER BY name"
    ).fetchall()


@router.get("/{product_id}")
def get_product(product_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    product = db.execute(
        """
        SELECT p.product_id, p.name, c.name AS category, p.category_id,
               p.pack_size, p.unit_price,
               ROUND(p.unit_price * p.pack_size, 2) AS carton_price, p.version
        FROM products p JOIN categories c USING (category_id)
        WHERE p.product_id = %s AND NOT p.is_deleted
        """,
        (product_id,),
    ).fetchone()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    product["price_history"] = db.execute(
        "SELECT old_price, new_price, changed_at FROM product_price_history "
        "WHERE product_id = %s ORDER BY changed_at DESC LIMIT 20",
        (product_id,),
    ).fetchall()
    return product


@router.post("", status_code=201)
def create_product(
    data: ProductCreate, db=Depends(get_db), user=Depends(require("can_edit"))
):
    with friendly_db_errors():
        new = db.execute(
            "INSERT INTO products (category_id, name, pack_size, unit_price) "
            "VALUES (%s, %s, %s, %s) RETURNING product_id",
            (data.category_id, data.name, data.pack_size, data.unit_price),
        ).fetchone()
    return get_product(new["product_id"], db, user)


@router.patch("/{product_id}")
def update_product(
    product_id: int,
    data: ProductUpdate,
    db=Depends(get_db),
    user=Depends(require("can_edit")),
):
    changes = data.model_dump(exclude_unset=True, exclude={"version"})
    changes = {k: v for k, v in changes.items() if v is not None}   # columns cannot be empty
    update_row(db, "products", "product_id", product_id, data.version, changes)
    return get_product(product_id, db, user)


@router.delete("/{product_id}")
def delete_product(
    product_id: int, db=Depends(get_db), user=Depends(require("can_delete"))
):
    soft_delete(db, "products", "product_id", product_id)
    return {"message": "Product deleted (it can be restored)."}


@router.post("/{product_id}/restore")
def restore_product(
    product_id: int, db=Depends(get_db), user=Depends(require("can_delete"))
):
    restore_row(db, "products", "product_id", product_id)
    return get_product(product_id, db, user)