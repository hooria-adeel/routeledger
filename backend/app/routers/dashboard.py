from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def month_range(month: str | None) -> tuple[date, date] | None:
    """Turns "2026-03" into [2026-03-01, 2026-04-01), or None for all time."""
    if not month:
        return None
    try:
        year, number = (int(part) for part in month.split("-"))
        start = date(year, number, 1)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=422, detail="Month must look like YYYY-MM."
        )
    end = date(year + 1, 1, 1) if number == 12 else date(year, number + 1, 1)
    return start, end


@router.get("")
def dashboard(
    month: str | None = Query(None, max_length=7),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    """Everything the home page needs, in one request. The reports come from
    the database views we created in schema.sql.

    ``month`` (YYYY-MM) narrows the KPI cards and every breakdown to that
    month. The monthly trend itself always returns every month, so the chart
    can show the selected bar in context.
    """
    period = month_range(month)

    if period is None:
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
    else:
        start, end = period
        totals = db.execute(
            """
            SELECT (SELECT count(*) FROM products  WHERE NOT is_deleted) AS products,
                   (SELECT count(*) FROM retailers WHERE NOT is_deleted) AS retailers,
                   (SELECT count(*) FROM branches  WHERE NOT is_deleted) AS branches,
                   (SELECT count(*) FROM orders
                     WHERE NOT is_deleted AND order_date >= %s AND order_date < %s) AS orders,
                   (SELECT COALESCE(SUM(line_value), 0) FROM v_sales_detail
                     WHERE order_date >= %s AND order_date < %s) AS total_sales,
                   (SELECT COALESCE(SUM(cartons), 0) FROM v_sales_detail
                     WHERE order_date >= %s AND order_date < %s) AS total_cartons
            """,
            (start, end, start, end, start, end),
        ).fetchone()

    where, params = "", ()
    if period is not None:
        where = " WHERE order_date >= %s AND order_date < %s"
        params = period

    return {
        "month": month or None,
        "totals": totals,
        "sales_by_month": db.execute(
            """
            SELECT date_trunc('month', order_date)::date AS month,
                   SUM(cartons) AS cartons,
                   SUM(line_value) AS total_value,
                   COUNT(DISTINCT order_id) AS orders
            FROM v_sales_detail
            GROUP BY 1
            ORDER BY 1
            """
        ).fetchall(),
        "sales_by_area": db.execute(
            "SELECT area, SUM(cartons) AS cartons, SUM(line_value) AS total_value "
            f"FROM v_sales_detail{where} GROUP BY 1 ORDER BY total_value DESC",
            params,
        ).fetchall(),
        "sales_by_category": db.execute(
            "SELECT category, SUM(cartons) AS cartons, SUM(line_value) AS total_value "
            f"FROM v_sales_detail{where} GROUP BY category ORDER BY total_value DESC",
            params,
        ).fetchall(),
        "top_retailers": db.execute(
            "SELECT retailer, SUM(cartons) AS cartons, SUM(line_value) AS total_value "
            f"FROM v_sales_detail{where} GROUP BY retailer "
            "ORDER BY total_value DESC LIMIT 5",
            params,
        ).fetchall(),
        "top_products": db.execute(
            "SELECT product, SUM(cartons) AS cartons, SUM(line_value) AS total_value "
            f"FROM v_sales_detail{where} GROUP BY product "
            "ORDER BY total_value DESC LIMIT 5",
            params,
        ).fetchall(),
    }
