from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.dependencies import get_current_user, require
from app.schemas import OrderCreate, OrderItemIn, OrderItemUpdate, OrderUpdate
from app.utils import friendly_db_errors, page_response, restore_row, soft_delete, update_row

router = APIRouter(prefix="/orders", tags=["Orders"])

SORT = {
    "date": "o.order_date",
    "retailer": "r.name",
    "total": "SUM(i.line_value)",
    "cartons": "SUM(i.cartons)",
}


@router.get("")
def list_orders(
    retailer_id: int | None = None,
    area_id: int | None = None,
    product_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort: Literal["date", "retailer", "total", "cartons"] = "date",
    order: Literal["asc", "desc"] = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    where, params = ["NOT o.is_deleted"], []
    if retailer_id:
        where.append("o.retailer_id = %s")
        params.append(retailer_id)
    if area_id:
        where.append("b.area_id = %s")
        params.append(area_id)
    if product_id:
        where.append(
            "EXISTS (SELECT 1 FROM order_items x "
            "WHERE x.order_id = o.order_id AND x.product_id = %s)"
        )
        params.append(product_id)
    if date_from:
        where.append("o.order_date >= %s")
        params.append(date_from)
    if date_to:
        where.append("o.order_date <= %s")
        params.append(date_to)
    where_sql = " AND ".join(where)

    joins = """FROM orders o
               JOIN retailers r ON r.retailer_id = o.retailer_id
               LEFT JOIN branches b ON b.branch_id = o.branch_id
               LEFT JOIN areas a ON a.area_id = b.area_id"""
    total = db.execute(
        f"SELECT count(*) AS n {joins} WHERE {where_sql}", params
    ).fetchone()["n"]

    direction = "DESC" if order == "desc" else "ASC"
    rows = db.execute(
        f"""
        SELECT o.order_id, o.order_date, r.name AS retailer, a.name AS area,
               COUNT(i.item_id) AS item_count, SUM(i.cartons) AS cartons,
               SUM(i.line_value) AS total_value, o.version
        {joins}
        JOIN order_items i ON i.order_id = o.order_id
        WHERE {where_sql}
        GROUP BY o.order_id, r.name, a.name
        ORDER BY {SORT[sort]} {direction}, o.order_id
        LIMIT %s OFFSET %s
        """,
        params + [page_size, (page - 1) * page_size],
    ).fetchall()
    return page_response(rows, total, page, page_size)


@router.get("/{order_id}")
def get_order(order_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    order = db.execute(
        """
        SELECT o.order_id, o.order_date, o.retailer_id, r.name AS retailer,
               o.branch_id, b.branch_name, a.name AS area, o.version
        FROM orders o
        JOIN retailers r ON r.retailer_id = o.retailer_id
        LEFT JOIN branches b ON b.branch_id = o.branch_id
        LEFT JOIN areas a ON a.area_id = b.area_id
        WHERE o.order_id = %s AND NOT o.is_deleted
        """,
        (order_id,),
    ).fetchone()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    order["items"] = db.execute(
        """
        SELECT i.item_id, p.product_id, p.name AS product, i.cartons,
               i.carton_price, i.line_value, i.version
        FROM order_items i JOIN products p USING (product_id)
        WHERE i.order_id = %s
        ORDER BY p.name
        """,
        (order_id,),
    ).fetchall()
    order["total_value"] = sum(item["line_value"] for item in order["items"])
    return order


# ----------------------------------------------------------------------
# Checks used by the add / edit endpoints
# ----------------------------------------------------------------------
def check_date(order_date: date):
    if order_date > date.today():
        raise HTTPException(status_code=422, detail="Order date cannot be in the future.")


def check_branch(db, retailer_id: int, branch_id: int | None):
    if db.execute(
        "SELECT 1 FROM retailers WHERE retailer_id = %s AND NOT is_deleted", (retailer_id,)
    ).fetchone() is None:
        raise HTTPException(status_code=422, detail="Retailer not found.")
    if branch_id is not None and db.execute(
        "SELECT 1 FROM branches WHERE branch_id = %s AND retailer_id = %s AND NOT is_deleted",
        (branch_id, retailer_id),
    ).fetchone() is None:
        raise HTTPException(
            status_code=422, detail="This branch does not belong to the chosen retailer."
        )


def list_price(db, product_ids: list[int]) -> dict:
    """Normal carton price of each product (price per unit x pack size)."""
    rows = db.execute(
        "SELECT product_id, ROUND(unit_price * pack_size, 2) AS carton_price "
        "FROM products WHERE product_id = ANY(%s) AND NOT is_deleted",
        (product_ids,),
    ).fetchall()
    return {r["product_id"]: r["carton_price"] for r in rows}


# ----------------------------------------------------------------------
# Orders
# ----------------------------------------------------------------------
@router.post("", status_code=201)
def create_order(
    data: OrderCreate, db=Depends(get_db), user=Depends(require("can_edit"))
):
    """The order and ALL its items are saved together. If anything is wrong,
    nothing is saved (this is a database transaction)."""
    check_date(data.order_date)
    check_branch(db, data.retailer_id, data.branch_id)

    ids = [item.product_id for item in data.items]
    if len(set(ids)) != len(ids):
        raise HTTPException(status_code=422, detail="The same product appears twice.")
    prices = list_price(db, ids)
    missing = [i for i in ids if i not in prices]
    if missing:
        raise HTTPException(status_code=422, detail=f"Product not found: {missing}")

    order = db.execute(
        "INSERT INTO orders (retailer_id, branch_id, order_date, created_by) "
        "VALUES (%s, %s, %s, %s) RETURNING order_id",
        (data.retailer_id, data.branch_id, data.order_date, user["employee_id"]),
    ).fetchone()
    with friendly_db_errors():
        for item in data.items:
            price = item.carton_price if item.carton_price is not None else prices[item.product_id]
            db.execute(
                "INSERT INTO order_items (order_id, product_id, cartons, carton_price, line_value) "
                "VALUES (%s, %s, %s, %s, %s)",
                (order["order_id"], item.product_id, item.cartons, price,
                 round(price * item.cartons, 2)),
            )
    return get_order(order["order_id"], db, user)


@router.patch("/{order_id}")
def update_order(
    order_id: int,
    data: OrderUpdate,
    db=Depends(get_db),
    user=Depends(require("can_edit")),
):
    current = db.execute(
        "SELECT retailer_id, branch_id FROM orders WHERE order_id = %s AND NOT is_deleted",
        (order_id,),
    ).fetchone()
    if current is None:
        raise HTTPException(status_code=404, detail="Order not found.")

    changes = data.model_dump(exclude_unset=True, exclude={"version"})
    for column in ("order_date", "retailer_id"):         # these cannot be empty
        if column in changes and changes[column] is None:
            changes.pop(column)
    if "retailer_id" in changes and "branch_id" not in changes:
        changes["branch_id"] = None                      # old branch belonged to the old retailer

    retailer_id = changes.get("retailer_id", current["retailer_id"])
    branch_id = changes["branch_id"] if "branch_id" in changes else current["branch_id"]
    check_branch(db, retailer_id, branch_id)
    if "order_date" in changes:
        check_date(changes["order_date"])

    update_row(db, "orders", "order_id", order_id, data.version, changes)
    return get_order(order_id, db, user)


@router.delete("/{order_id}")
def delete_order(order_id: int, db=Depends(get_db), user=Depends(require("can_delete"))):
    soft_delete(db, "orders", "order_id", order_id)
    return {"message": "Order deleted (it can be restored)."}


@router.post("/{order_id}/restore")
def restore_order(order_id: int, db=Depends(get_db), user=Depends(require("can_delete"))):
    restore_row(db, "orders", "order_id", order_id)
    return get_order(order_id, db, user)


# ----------------------------------------------------------------------
# Items inside an order
# ----------------------------------------------------------------------
@router.post("/{order_id}/items", status_code=201)
def add_item(
    order_id: int,
    item: OrderItemIn,
    db=Depends(get_db),
    user=Depends(require("can_edit")),
):
    if db.execute(
        "SELECT 1 FROM orders WHERE order_id = %s AND NOT is_deleted", (order_id,)
    ).fetchone() is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    prices = list_price(db, [item.product_id])
    if item.product_id not in prices:
        raise HTTPException(status_code=422, detail="Product not found.")
    price = item.carton_price if item.carton_price is not None else prices[item.product_id]
    with friendly_db_errors():
        db.execute(
            "INSERT INTO order_items (order_id, product_id, cartons, carton_price, line_value) "
            "VALUES (%s, %s, %s, %s, %s)",
            (order_id, item.product_id, item.cartons, price, round(price * item.cartons, 2)),
        )
    return get_order(order_id, db, user)


@router.patch("/{order_id}/items/{item_id}")
def update_item(
    order_id: int,
    item_id: int,
    data: OrderItemUpdate,
    db=Depends(get_db),
    user=Depends(require("can_edit")),
):
    current = db.execute(
        "SELECT i.cartons, i.carton_price FROM order_items i "
        "JOIN orders o USING (order_id) "
        "WHERE i.item_id = %s AND i.order_id = %s AND NOT o.is_deleted",
        (item_id, order_id),
    ).fetchone()
    if current is None:
        raise HTTPException(status_code=404, detail="Order item not found.")
    cartons = data.cartons if data.cartons is not None else current["cartons"]
    price = data.carton_price if data.carton_price is not None else current["carton_price"]
    changes = {"cartons": cartons, "carton_price": price, "line_value": round(price * cartons, 2)}
    update_row(db, "order_items", "item_id", item_id, data.version, changes,
               soft_delete_column=False)
    return get_order(order_id, db, user)


@router.delete("/{order_id}/items/{item_id}")
def delete_item(
    order_id: int,
    item_id: int,
    db=Depends(get_db),
    user=Depends(require("can_delete")),
):
    count = db.execute(
        "SELECT count(*) AS n FROM order_items WHERE order_id = %s", (order_id,)
    ).fetchone()["n"]
    if count <= 1:
        raise HTTPException(
            status_code=400,
            detail="An order needs at least one item. Delete the whole order instead.",
        )
    cur = db.execute(
        "DELETE FROM order_items WHERE item_id = %s AND order_id = %s", (item_id, order_id)
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Order item not found.")
    return get_order(order_id, db, user)