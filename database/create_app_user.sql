
-- =====================================================================
-- A limited database user for the web application ("least privilege").
-- The app must NOT run as the all-powerful "postgres" user. If the app is
-- ever attacked, the attacker only gets what this user is allowed to do.
--
-- 1. Change the password on the line marked  <<< CHANGE THIS
-- 2. Run this file as "postgres" in EACH database: routeledger and routeledger_test
--    (running it twice is fine)
-- =====================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'routeledger_app') THEN
        CREATE ROLE routeledger_app LOGIN
            PASSWORD 'CHANGE_ME_use_a_long_random_password'  -- <<< CHANGE THIS
            NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
END $$;

-- It may use the tables, but cannot create or drop anything
GRANT USAGE ON SCHEMA public TO routeledger_app;

-- Read everything
GRANT SELECT ON ALL TABLES IN SCHEMA public TO routeledger_app;

-- Add and change data in the business tables (and employees, for the admin pages)
GRANT INSERT, UPDATE ON products, retailers, branches, areas, orders, order_items, employees
    TO routeledger_app;

-- The triggers write the activity log and price history for it
GRANT INSERT ON activity_log, product_price_history TO routeledger_app;

-- The only real DELETE: removing one item from an order
GRANT DELETE ON order_items TO routeledger_app;

-- Needed so new rows can get their automatic id numbers
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO routeledger_app;

-- Not granted on purpose: DROP, TRUNCATE, DELETE on other tables,
-- changing the roles table, and changing or deleting the activity log.