-- =====================================================================
-- RouteLedger Distribution Management System  |  PostgreSQL schema
-- Replaces the shared Excel sheets with one central, secured database.
-- Run order: schema.sql  ->  seed.sql
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. ACCESS CONTROL: roles and employees
-- ---------------------------------------------------------------------
CREATE TABLE roles (
    role_id      SMALLSERIAL PRIMARY KEY,
    name         VARCHAR(20)  NOT NULL UNIQUE,
    description  VARCHAR(200) NOT NULL,
    can_edit     BOOLEAN NOT NULL DEFAULT FALSE,   -- may add / change data
    can_delete   BOOLEAN NOT NULL DEFAULT FALSE,   -- may (soft) delete data
    can_manage   BOOLEAN NOT NULL DEFAULT FALSE    -- may manage employees
);

CREATE TABLE employees (
    employee_id      SERIAL PRIMARY KEY,
    role_id          SMALLINT     NOT NULL REFERENCES roles(role_id),
    full_name        VARCHAR(100) NOT NULL,
    email            VARCHAR(150) NOT NULL UNIQUE,
    password_hash    TEXT         NOT NULL,          -- Argon2 hash, never the password
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    failed_attempts  SMALLINT     NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0),
    locked_until     TIMESTAMPTZ,                    -- set after too many wrong passwords
    last_login_at    TIMESTAMPTZ,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT chk_email_format CHECK (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$')
);

-- ---------------------------------------------------------------------
-- 2. BUSINESS DATA
--    Every business table has: version (safe editing), is_deleted (soft
--    delete), created_at / updated_at.
-- ---------------------------------------------------------------------
CREATE TABLE categories (
    category_id  SMALLSERIAL PRIMARY KEY,
    name         VARCHAR(50) NOT NULL UNIQUE,
    version      INTEGER     NOT NULL DEFAULT 1,
    is_deleted   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE products (
    product_id    SERIAL PRIMARY KEY,
    category_id   SMALLINT     NOT NULL REFERENCES categories(category_id),
    name          VARCHAR(150) NOT NULL UNIQUE,
    pack_size     INTEGER      NOT NULL CHECK (pack_size > 0),      -- units per carton
    unit_price    NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),   -- net amount per unit
    version       INTEGER      NOT NULL DEFAULT 1,
    is_deleted    BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE product_price_history (
    history_id   BIGSERIAL PRIMARY KEY,
    product_id   INTEGER       NOT NULL REFERENCES products(product_id),
    old_price    NUMERIC(12,2) NOT NULL,
    new_price    NUMERIC(12,2) NOT NULL,
    changed_by   INTEGER REFERENCES employees(employee_id),
    changed_at   TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE TABLE areas (
    area_id     SERIAL PRIMARY KEY,
    name        VARCHAR(80) NOT NULL UNIQUE,
    district    VARCHAR(80),                 -- city district, optional
    version     INTEGER     NOT NULL DEFAULT 1,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE retailers (
    retailer_id  SERIAL PRIMARY KEY,
    name         VARCHAR(120) NOT NULL UNIQUE,
    version      INTEGER      NOT NULL DEFAULT 1,
    is_deleted   BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE branches (
    branch_id    SERIAL PRIMARY KEY,
    retailer_id  INTEGER     NOT NULL REFERENCES retailers(retailer_id),
    area_id      INTEGER     NOT NULL REFERENCES areas(area_id),
    branch_name  VARCHAR(80) NOT NULL,
    version      INTEGER     NOT NULL DEFAULT 1,
    is_deleted   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_branch UNIQUE (retailer_id, branch_name)
);

-- The Excel order sheet only names the retailer, not the branch, so
-- branch_id is optional (it is filled when the retailer has one branch).
CREATE TABLE orders (
    order_id     SERIAL PRIMARY KEY,
    retailer_id  INTEGER NOT NULL REFERENCES retailers(retailer_id),
    branch_id    INTEGER REFERENCES branches(branch_id),
    order_date   DATE    NOT NULL CHECK (order_date >= DATE '2000-01-01'),
    created_by   INTEGER REFERENCES employees(employee_id),  -- NULL = imported from Excel
    version      INTEGER     NOT NULL DEFAULT 1,
    is_deleted   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    item_id         SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    cartons         INTEGER NOT NULL CHECK (cartons > 0),
    carton_price    NUMERIC(14,2) NOT NULL CHECK (carton_price >= 0),  -- price at time of sale
    line_value      NUMERIC(16,2) NOT NULL CHECK (line_value >= 0),
    version         INTEGER     NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_item UNIQUE (order_id, product_id)
);

-- ---------------------------------------------------------------------
-- 3. ACTIVITY LOG (who changed what, and when)
-- ---------------------------------------------------------------------
CREATE TABLE activity_log (
    log_id       BIGSERIAL PRIMARY KEY,
    employee_id  INTEGER REFERENCES employees(employee_id),
    table_name   VARCHAR(50) NOT NULL,
    record_id    INTEGER,
    action       VARCHAR(10) NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
    old_value    JSONB,
    new_value    JSONB,
    logged_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 4. INDEXES (speed up the searches employees actually do)
-- ---------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- lets "contains" search be fast
CREATE INDEX idx_products_name_trgm   ON products  USING gin (name gin_trgm_ops);
CREATE INDEX idx_retailers_name_trgm  ON retailers USING gin (name gin_trgm_ops);
CREATE INDEX idx_products_category    ON products (category_id);
CREATE INDEX idx_branches_retailer    ON branches (retailer_id);
CREATE INDEX idx_branches_area        ON branches (area_id);
CREATE INDEX idx_orders_date          ON orders (order_date);
CREATE INDEX idx_orders_retailer      ON orders (retailer_id);
CREATE INDEX idx_items_order          ON order_items (order_id);
CREATE INDEX idx_items_product        ON order_items (product_id);
CREATE INDEX idx_log_table_record     ON activity_log (table_name, record_id);
CREATE INDEX idx_log_time             ON activity_log (logged_at);

-- ---------------------------------------------------------------------
-- 5. TRIGGERS
-- ---------------------------------------------------------------------

-- 5a. Safe editing (optimistic locking): the app sends the version it
--     read. If someone else saved first, the version no longer matches
--     and the update is refused, so nobody overwrites a colleague's work.
CREATE OR REPLACE FUNCTION fn_touch_row() RETURNS trigger AS $$
BEGIN
    IF NEW.version <> OLD.version THEN
        RAISE EXCEPTION 'Stale edit: this record was changed by someone else (expected version %, found %). Reload and try again.',
            NEW.version, OLD.version USING ERRCODE = '40001';
    END IF;
    NEW.version    := OLD.version + 1;
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5b. Activity log. The backend runs
--        SELECT set_config('app.current_employee_id', '<id>', true);
--     at the start of each request so the log knows who did it.
CREATE OR REPLACE FUNCTION fn_audit() RETURNS trigger AS $$
DECLARE
    v_emp   INTEGER := NULLIF(current_setting('app.current_employee_id', true), '')::INTEGER;
    v_id    INTEGER;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        INSERT INTO activity_log (employee_id, table_name, record_id, action, new_value)
        VALUES (v_emp, TG_TABLE_NAME, v_id, 'INSERT', to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        v_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        INSERT INTO activity_log (employee_id, table_name, record_id, action, old_value, new_value)
        VALUES (v_emp, TG_TABLE_NAME, v_id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSE
        v_id := (to_jsonb(OLD) ->> TG_ARGV[0])::INTEGER;
        INSERT INTO activity_log (employee_id, table_name, record_id, action, old_value)
        VALUES (v_emp, TG_TABLE_NAME, v_id, 'DELETE', to_jsonb(OLD));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 5c. Price history: every price change is remembered.
CREATE OR REPLACE FUNCTION fn_price_history() RETURNS trigger AS $$
BEGIN
    IF NEW.unit_price IS DISTINCT FROM OLD.unit_price THEN
        INSERT INTO product_price_history (product_id, old_price, new_price, changed_by)
        VALUES (OLD.product_id, OLD.unit_price, NEW.unit_price,
                NULLIF(current_setting('app.current_employee_id', true), '')::INTEGER);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach the triggers (one line per table)
CREATE TRIGGER trg_touch_categories  BEFORE UPDATE ON categories  FOR EACH ROW EXECUTE FUNCTION fn_touch_row();
CREATE TRIGGER trg_touch_products    BEFORE UPDATE ON products    FOR EACH ROW EXECUTE FUNCTION fn_touch_row();
CREATE TRIGGER trg_touch_areas       BEFORE UPDATE ON areas       FOR EACH ROW EXECUTE FUNCTION fn_touch_row();
CREATE TRIGGER trg_touch_retailers   BEFORE UPDATE ON retailers   FOR EACH ROW EXECUTE FUNCTION fn_touch_row();
CREATE TRIGGER trg_touch_branches    BEFORE UPDATE ON branches    FOR EACH ROW EXECUTE FUNCTION fn_touch_row();
CREATE TRIGGER trg_touch_orders      BEFORE UPDATE ON orders      FOR EACH ROW EXECUTE FUNCTION fn_touch_row();
CREATE TRIGGER trg_touch_order_items BEFORE UPDATE ON order_items FOR EACH ROW EXECUTE FUNCTION fn_touch_row();

CREATE TRIGGER trg_price_history AFTER UPDATE ON products FOR EACH ROW EXECUTE FUNCTION fn_price_history();

CREATE TRIGGER trg_audit_categories  AFTER INSERT OR UPDATE OR DELETE ON categories  FOR EACH ROW EXECUTE FUNCTION fn_audit('category_id');
CREATE TRIGGER trg_audit_products    AFTER INSERT OR UPDATE OR DELETE ON products    FOR EACH ROW EXECUTE FUNCTION fn_audit('product_id');
CREATE TRIGGER trg_audit_areas       AFTER INSERT OR UPDATE OR DELETE ON areas       FOR EACH ROW EXECUTE FUNCTION fn_audit('area_id');
CREATE TRIGGER trg_audit_retailers   AFTER INSERT OR UPDATE OR DELETE ON retailers   FOR EACH ROW EXECUTE FUNCTION fn_audit('retailer_id');
CREATE TRIGGER trg_audit_branches    AFTER INSERT OR UPDATE OR DELETE ON branches    FOR EACH ROW EXECUTE FUNCTION fn_audit('branch_id');
CREATE TRIGGER trg_audit_orders      AFTER INSERT OR UPDATE OR DELETE ON orders      FOR EACH ROW EXECUTE FUNCTION fn_audit('order_id');
CREATE TRIGGER trg_audit_order_items AFTER INSERT OR UPDATE OR DELETE ON order_items FOR EACH ROW EXECUTE FUNCTION fn_audit('item_id');

-- The log itself must never be edited or deleted
CREATE OR REPLACE FUNCTION fn_log_readonly() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'activity_log is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_readonly BEFORE UPDATE OR DELETE ON activity_log
    FOR EACH ROW EXECUTE FUNCTION fn_log_readonly();

-- ---------------------------------------------------------------------
-- 6. VIEWS (ready-made reports the dashboard reads from)
-- ---------------------------------------------------------------------
CREATE VIEW v_product_list AS
SELECT p.product_id, c.name AS category, p.name AS product, p.pack_size,
       p.unit_price, ROUND(p.unit_price * p.pack_size, 2) AS carton_list_price
FROM products p JOIN categories c USING (category_id)
WHERE NOT p.is_deleted;

CREATE VIEW v_branch_list AS
SELECT b.branch_id, r.name AS retailer, b.branch_name, a.name AS area
FROM branches b
JOIN retailers r USING (retailer_id)
JOIN areas a USING (area_id)
WHERE NOT b.is_deleted AND NOT r.is_deleted;

CREATE VIEW v_sales_detail AS
SELECT o.order_id, o.order_date, r.name AS retailer, a.name AS area,
       c.name AS category, p.name AS product, i.cartons, i.carton_price, i.line_value
FROM orders o
JOIN order_items i USING (order_id)
JOIN products p    USING (product_id)
JOIN categories c  ON c.category_id = p.category_id
JOIN retailers r   ON r.retailer_id = o.retailer_id
LEFT JOIN branches b ON b.branch_id = o.branch_id
LEFT JOIN areas a    ON a.area_id   = b.area_id
WHERE NOT o.is_deleted;

CREATE VIEW v_sales_by_retailer AS
SELECT retailer, SUM(cartons) AS cartons, SUM(line_value) AS total_value
FROM v_sales_detail GROUP BY retailer;

CREATE VIEW v_sales_by_product AS
SELECT product, SUM(cartons) AS cartons, SUM(line_value) AS total_value
FROM v_sales_detail GROUP BY product;

CREATE VIEW v_sales_by_month AS
SELECT date_trunc('month', order_date)::date AS month,
       SUM(cartons) AS cartons, SUM(line_value) AS total_value
FROM v_sales_detail GROUP BY 1;

CREATE VIEW v_sales_by_area AS
SELECT COALESCE(area, 'Not recorded') AS area,
       SUM(cartons) AS cartons, SUM(line_value) AS total_value
FROM v_sales_detail GROUP BY 1;

-- ---------------------------------------------------------------------
-- 7. TRANSACTION EXAMPLE (an order and its items are saved together or
--    not at all). The backend does the same thing in code.
-- ---------------------------------------------------------------------
-- BEGIN;
--   INSERT INTO orders (retailer_id, branch_id, order_date, created_by) VALUES (...) RETURNING order_id;
--   INSERT INTO order_items (order_id, product_id, cartons, carton_price, line_value) VALUES (...);
-- COMMIT;   -- or ROLLBACK if anything fails

-- ---------------------------------------------------------------------
-- 8. STARTING DATA: the four roles
-- ---------------------------------------------------------------------
INSERT INTO roles (name, description, can_edit, can_delete, can_manage) VALUES
 ('Viewer',  'Can look at and search all data',                       FALSE, FALSE, FALSE),
 ('Editor',  'Can add and change products, retailers and orders',     TRUE,  FALSE, FALSE),
 ('Manager', 'Can also delete records and see the activity log',      TRUE,  TRUE,  FALSE),
 ('Admin',   'Full access, including creating and managing employees', TRUE,  TRUE,  TRUE);

COMMIT;
