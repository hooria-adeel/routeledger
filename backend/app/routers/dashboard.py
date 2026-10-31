from fastapi import APIRouter, Depends

from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
def dashboard(db=Depends(get_db), user=Depends(get_current_user)):
    """Everything the home page needs, in one request. The reports come from
    the database views we created in schema.sql."""
    totals = db.execute(
        """
        SELECT (SELECT count(*) FROM products  WHERE NOT is_deleted) AS products,
               (SELECT count(*) FROM retailers WHERE NOT is_deleted) AS retailers,
               (SELECT count(*) FROM branches  WHERE NOT is_deleted) AS branches,
               (SELECT count(*) FROM orders    WHERE NOT is_deleted) AS orders,
               (SELECT COALESCE(SUM(line_value), 0) FROM v_sales_detail) AS total_sales,
               (SELECT COALESCE(SUM(cartons), 0)    FROM v_sales_detail) AS total_cartons
        """
    ).fetchone()
    return {
        "totals": totals,
        "sales_by_month": db.execute(
            "SELECT month, cartons, total_value FROM v_sales_by_month ORDER BY month"
        ).fetchall(),
        "sales_by_area": db.execute(
            "SELECT area, cartons, total_value FROM v_sales_by_area ORDER BY total_value DESC"
        ).fetchall(),
        "sales_by_category": db.execute(
            "SELECT category, SUM(cartons) AS cartons, SUM(line_value) AS total_value "
            "FROM v_sales_detail GROUP BY category ORDER BY total_value DESC"
        ).fetchall(),
        "top_retailers": db.execute(
            "SELECT retailer, cartons, total_value FROM v_sales_by_retailer "
            "ORDER BY total_value DESC LIMIT 5"
        ).fetchall(),
        "top_products": db.execute(
            "SELECT product, cartons, total_value FROM v_sales_by_product "
            "ORDER BY total_value DESC LIMIT 5"
        ).fetchall(),
    }