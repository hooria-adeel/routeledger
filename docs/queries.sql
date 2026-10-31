-- =====================================================================
-- RouteLedger | analytical queries used by the dashboard and reports
-- Run with:  psql -d routeledger -f docs/queries.sql
-- Every query reads the reporting views, so soft-deleted rows are absent.
-- =====================================================================

-- 1. Sales by area, with each area's share of the total (window function).
SELECT area,
       cartons,
       total_value,
       ROUND(100 * total_value / SUM(total_value) OVER (), 1) AS share_pct
FROM v_sales_by_area
ORDER BY total_value DESC;

-- 2. Month-over-month growth (LAG over an ordered window).
SELECT month,
       total_value,
       LAG(total_value) OVER (ORDER BY month) AS previous_month,
       ROUND(100 * (total_value - LAG(total_value) OVER (ORDER BY month))
             / NULLIF(LAG(total_value) OVER (ORDER BY month), 0), 1) AS growth_pct
FROM v_sales_by_month
ORDER BY month;

-- 3. Best-selling products by revenue, with carton volume.
SELECT product, cartons, total_value
FROM v_sales_by_product
ORDER BY total_value DESC
LIMIT 10;

-- 4. Retailer concentration: running share of total revenue.
SELECT retailer,
       total_value,
       ROUND(100 * SUM(total_value) OVER (ORDER BY total_value DESC)
             / SUM(total_value) OVER (), 1) AS cumulative_share_pct
FROM v_sales_by_retailer
ORDER BY total_value DESC;

-- 5. Category mix and average price per carton sold.
SELECT category,
       SUM(cartons) AS cartons,
       SUM(line_value) AS revenue,
       ROUND(SUM(line_value) / NULLIF(SUM(cartons), 0), 2) AS avg_carton_price
FROM v_sales_detail
GROUP BY category
ORDER BY revenue DESC;

-- 6. Every price change, newest first, with the employee who made it.
SELECT p.name AS product,
       h.old_price,
       h.new_price,
       ROUND(100 * (h.new_price - h.old_price) / NULLIF(h.old_price, 0), 1) AS change_pct,
       e.full_name AS changed_by,
       h.changed_at
FROM product_price_history h
JOIN products p USING (product_id)
LEFT JOIN employees e ON e.employee_id = h.changed_by
ORDER BY h.changed_at DESC
LIMIT 25;

-- 7. Audit trail for one record: what changed, by whom, and when.
SELECT logged_at AS changed_at,
       action,
       e.full_name AS employee,
       old_value ->> 'unit_price' AS old_price,
       new_value ->> 'unit_price' AS new_price
FROM activity_log l
LEFT JOIN employees e USING (employee_id)
WHERE l.table_name = 'products'
  AND l.record_id = 1                    -- change this id
ORDER BY logged_at DESC
LIMIT 20;

-- 8. Data-quality checks that should return zero rows.
--    a) order lines pointing at a deleted order
SELECT count(*) AS lines_on_deleted_orders
FROM order_items i JOIN orders o USING (order_id)
WHERE o.is_deleted;

--    b) orders whose branch belongs to a different retailer
SELECT count(*) AS branch_mismatches
FROM orders o JOIN branches b USING (branch_id)
WHERE b.retailer_id <> o.retailer_id;

-- Performance evidence: the GIN trigram index answers a contains-search
-- without a sequential scan once the catalogue is large.
EXPLAIN (ANALYZE, BUFFERS)
SELECT product_id, product
FROM v_product_list
WHERE product ILIKE '%tea%';
