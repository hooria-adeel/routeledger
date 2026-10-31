"""
Generates 100% synthetic demo data for RouteLedger.

Every brand, product, retailer, area mix and price below is invented. Any resemblance to a
real company is coincidental. The random seed is fixed, so the output is reproducible:

    python generate_seed.py          # rewrites seed.sql and seed_demo_orders.sql
"""
import random, datetime as dt, pathlib

random.seed(7)
HERE = pathlib.Path(__file__).parent
q = lambda s: "'" + s.replace("'", "''") + "'"

# ---------------------------------------------------------------- catalogue
# (category, product line, [(size label, units per carton, base unit price in Rs)])
LINES = [
 # --- Beverages
 ("Beverages", "ZESTORA Lime Fizz",           [("345ml can",24,95),("1500ml PET",6,240)]),
 ("Beverages", "ZESTORA Orange Fizz",         [("345ml can",24,95),("1500ml PET",6,240)]),
 ("Beverages", "FROSTBITE Energy Drink",      [("250ml can",24,170),("500ml can",12,255)]),
 ("Beverages", "AQUARIA Spring Water",        [("500ml",12,45),("1500ml",6,88),("19L bottle",1,390)]),
 ("Beverages", "LEAFLY Green Tea Bags",       [("25 bags",48,210),("100 bags",12,760)]),
 ("Beverages", "LEAFLY Black Tea Loose",      [("190g",48,350),("950g",12,1650)]),
 ("Beverages", "MANGOLA Mango Drink",         [("250ml",24,60),("1000ml",12,215)]),
 ("Beverages", "MANGOLA Guava Drink",         [("250ml",24,60),("1000ml",12,215)]),
 ("Beverages", "SIPPLE Rose Syrup",           [("800ml",12,520),("1500ml",6,940)]),
 ("Beverages", "SIPPLE Instant Lemon Mix",    [("500g",12,610),("12g sachet x 20",24,280)]),
 # --- Snacks
 ("Snacks", "CRUNCHLY Potato Chips Salted",   [("30g",48,45),("65g",24,95),("150g",12,210)]),
 ("Snacks", "CRUNCHLY Potato Chips Masala",   [("30g",48,45),("65g",24,95),("150g",12,210)]),
 ("Snacks", "SPICEROAD Masala Puffs",         [("25g",60,28),("80g",24,85)]),
 ("Snacks", "NUTHAVEN Salted Peanuts",        [("40g",48,52),("200g",24,255)]),
 ("Snacks", "NUTHAVEN Mixed Nuts",            [("100g",24,420),("400g",12,1480)]),
 ("Snacks", "BISCOTTA Cream Biscuits Vanilla",[("6 pack",24,70),("12 pack",12,135)]),
 ("Snacks", "BISCOTTA Cream Biscuits Chocolate",[("6 pack",24,70),("12 pack",12,135)]),
 ("Snacks", "BISCOTTA Tea Rusk",              [("300g",24,230),("600g",12,430)]),
 ("Snacks", "CHOCOMILL Wafer Bar",            [("1 bar",72,35),("6 bar pack",24,205)]),
 ("Snacks", "CHOCOMILL Hazelnut Spread",      [("200g",24,450),("750g",12,1380)]),
 ("Snacks", "SWEETKIN Fruit Toffee",          [("50 pcs jar",12,320),("100 pcs bag",24,590)]),
 ("Snacks", "SWEETKIN Chewing Gum",           [("5 pcs",120,25),("12 pcs",48,70)]),
 # --- Home Care
 ("Home Care", "BRIGHTA Dish Liquid Lemon",   [("500ml",24,230),("1000ml",12,430),("3000ml",4,1190)]),
 ("Home Care", "SPARKLO Laundry Powder",      [("500g",24,260),("1000g",12,490),("4000g",4,1850)]),
 ("Home Care", "SPARKLO Laundry Liquid",      [("1000ml",12,720),("3000ml",4,2050)]),
 ("Home Care", "SOFTWAVE Fabric Softener",    [("1000ml",12,610),("2500ml",4,1390)]),
 ("Home Care", "FRESHNEST Floor Cleaner Pine",[("500ml",24,240),("1000ml",12,430),("3000ml",4,1160)]),
 ("Home Care", "FRESHNEST Glass Cleaner",     [("500ml",24,265)]),
 ("Home Care", "ZAPP Insect Spray",           [("300ml",24,395),("600ml",12,720)]),
 ("Home Care", "TISSUELY Facial Tissue Box",  [("100 pulls",36,120),("200 pulls",24,215)]),
 ("Home Care", "TISSUELY Kitchen Roll",       [("2 roll pack",24,260),("6 roll pack",8,740)]),
 ("Home Care", "NESTWELL Garbage Bags Medium",[("20 bags",36,190),("50 bags",18,420)]),
 # --- Personal Care
 ("Personal Care", "LUMENA Shampoo Silky",    [("180ml",24,370),("375ml",12,690),("700ml",8,1190)]),
 ("Personal Care", "LUMENA Shampoo Anti-Dandruff",[("180ml",24,395),("375ml",12,720)]),
 ("Personal Care", "LUMENA Conditioner",      [("180ml",24,390),("375ml",12,740)]),
 ("Personal Care", "DERMIQ Face Wash Neem",   [("100ml",36,285),("150ml",24,380)]),
 ("Personal Care", "DERMIQ Face Wash Charcoal",[("100ml",36,295),("150ml",24,395)]),
 ("Personal Care", "SMILEWORKS Toothpaste Mint",[("50g",72,95),("100g",48,170),("200g",24,310)]),
 ("Personal Care", "SMILEWORKS Toothbrush Medium",[("1 pc",144,70),("3 pc pack",36,195)]),
 ("Personal Care", "AQUAVEIL Body Lotion",    [("200ml",24,420),("400ml",12,760)]),
 ("Personal Care", "PURENEST Hand Wash",      [("250ml",24,230),("500ml refill",12,390)]),
 ("Personal Care", "PURENEST Beauty Soap",    [("100g",72,80),("3 pack",24,230)]),
 ("Personal Care", "GLIDEX Razor Twin Blade", [("1 pc",144,55),("5 pc pack",36,240)]),
]
CATEGORIES = list(dict.fromkeys(l[0] for l in LINES))
PRODUCTS = []
for cat, base, sizes in LINES:
    for label, pack, price in sizes:
        unit = round(price * random.uniform(0.92, 1.09), 2)
        PRODUCTS.append((cat, f"{base} {label}", pack, unit))
assert len({p[1] for p in PRODUCTS}) == len(PRODUCTS)

# ---------------------------------------------------------------- places and retailers (invented chains)
AREAS = ["Gulberg","DHA Phase 5","Johar Town","Model Town","Iqbal Town","Shadman","Samanabad","Garden Town",
         "Wapda Town","Bahria Town","Cantt","Township","Faisal Town","Valencia Town","Askari","Ravi Road",
         "Mughalpura","Shalimar","Raiwind Road","Thokar Niaz Baig"]
RETAILERS = {   # invented chains -> branch areas
 "Minar Superstore":      ["Gulberg","DHA Phase 5","Model Town","Johar Town"],
 "Ravi Fresh Stores":     ["Ravi Road","Shalimar","Mughalpura"],
 "Lahori Basket":         ["Garden Town","Faisal Town"],
 "Haveli Provisions":     ["Cantt","Askari","Gulberg","Township","Samanabad"],
 "Jasmine Supermart":     ["Johar Town","Wapda Town"],
 "Kite Corner Stores":    ["Iqbal Town"],
 "Baradari Mart":         ["Shadman","Model Town"],
 "Mehtab Superstore":     ["DHA Phase 5","Bahria Town","Askari"],
 "Lotus Mini Mart":       ["Valencia Town","Wapda Town"],
 "Chenab Grocers":        ["Raiwind Road","Thokar Niaz Baig","Township"],
 "Karvaan Mart":          ["Cantt","Gulberg"],
 "Zeenat Family Store":   ["Samanabad","Iqbal Town","Faisal Town"],
 "Rahat Daily Needs":     ["Shalimar"],
 "Sitara Hypermart":      ["Bahria Town","DHA Phase 5","Johar Town","Valencia Town"],
}
RNAMES = list(RETAILERS)
WEIGHT = {r: 1/(i+1)**0.7 for i, r in enumerate(random.sample(RNAMES, len(RNAMES)))}   # a few big retailers, a long tail
FACTOR = {r: round(random.uniform(0.97, 1.03), 4) for r in RNAMES}                    # per-retailer price tweak

def make_orders(first_id, n, start, end):
    days = (end - start).days
    out = []
    for oid in range(first_id, first_id + n):
        r = random.choices(RNAMES, [WEIGHT[x] for x in RNAMES])[0]
        branch = random.choice(RETAILERS[r]) if random.random() < 0.85 else None
        d = start + dt.timedelta(days=random.randint(0, days))
        if d.weekday() == 4 and random.random() < .6: d -= dt.timedelta(days=1)   # fewer Friday orders
        items = random.sample(PRODUCTS, random.randint(1, 5))
        lines = []
        for cat, name, pack, unit in items:
            cartons = max(1, int(random.lognormvariate(2.2, 0.8)))
            cp = round(unit * pack * FACTOR[r], 2)
            lines.append((name, cartons, cp, round(cartons * cp, 2)))
        out.append((oid, r, branch, d, lines))
    return out

def order_sql(o):
    oid, r, b, d, lines = o
    rsel = f"(SELECT retailer_id FROM retailers WHERE name={q(r)})"
    bsel = "NULL" if b is None else f"(SELECT branch_id FROM branches WHERE retailer_id={rsel} AND branch_name={q(b)})"
    s = [f"INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES ({oid},{rsel},{bsel},'{d}');"]
    for name, c, cp, lv in lines:
        s.append(f"INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES "
                 f"({oid},(SELECT product_id FROM products WHERE name={q(name)}),{c},{cp},{lv});")
    return "\n".join(s)

# ---------------------------------------------------------------- seed.sql
H = """-- RouteLedger seed data: 100% synthetic (see generate_seed.py). No real company data.
BEGIN;
SELECT set_config('app.current_employee_id','',true);
ALTER TABLE activity_log DISABLE TRIGGER trg_log_readonly;  -- allow the import step only
ALTER TABLE products DISABLE TRIGGER USER; ALTER TABLE categories DISABLE TRIGGER USER; ALTER TABLE areas DISABLE TRIGGER USER;
ALTER TABLE retailers DISABLE TRIGGER USER; ALTER TABLE branches DISABLE TRIGGER USER; ALTER TABLE orders DISABLE TRIGGER USER; ALTER TABLE order_items DISABLE TRIGGER USER;
-- (triggers are switched off during the import so bulk rows do not flood the activity log)
"""
F = """SELECT setval(pg_get_serial_sequence('orders','order_id'),(SELECT MAX(order_id) FROM orders));
SELECT setval(pg_get_serial_sequence('order_items','item_id'),(SELECT MAX(item_id) FROM order_items));
ALTER TABLE products ENABLE TRIGGER USER; ALTER TABLE categories ENABLE TRIGGER USER; ALTER TABLE areas ENABLE TRIGGER USER;
ALTER TABLE retailers ENABLE TRIGGER USER; ALTER TABLE branches ENABLE TRIGGER USER; ALTER TABLE orders ENABLE TRIGGER USER; ALTER TABLE order_items ENABLE TRIGGER USER;
ALTER TABLE activity_log ENABLE TRIGGER trg_log_readonly;
COMMIT;
"""
cats = CATEGORIES
seed = [H, "INSERT INTO categories (name) VALUES " + ", ".join(f"({q(c)})" for c in cats) + ";",
        "INSERT INTO products (category_id,name,pack_size,unit_price) VALUES"]
seed.append(",\n".join(f"((SELECT category_id FROM categories WHERE name={q(c)}),{q(n)},{p},{u})" for c, n, p, u in PRODUCTS) + ";")
seed.append("INSERT INTO areas (name) VALUES " + ", ".join(f"({q(a)})" for a in AREAS) + ";")
seed.append("INSERT INTO retailers (name) VALUES " + ", ".join(f"({q(r)})" for r in RNAMES) + ";")
seed.append("INSERT INTO branches (retailer_id,area_id,branch_name) VALUES")
seed.append(",\n".join(f"((SELECT retailer_id FROM retailers WHERE name={q(r)}),(SELECT area_id FROM areas WHERE name={q(a)}),{q(a)})"
                       for r, areas in RETAILERS.items() for a in areas) + ";")
base_orders = make_orders(1, 60, dt.date(2026,7,1), dt.date(2026,8,31))
seed += [order_sql(o) for o in base_orders]
seed.append(F)
(HERE/"seed.sql").write_text("\n".join(seed), encoding="utf-8")

# ---------------------------------------------------------------- seed_demo_orders.sql
demo = make_orders(61, 400, dt.date(2026,6,1), dt.date(2026,10,28))
D = """-- DEMO DATA: 400 generated orders (Jun-Oct 2026) so dashboards and reports have something to show.
-- Run AFTER schema.sql and seed.sql. Everything here is synthetic.
BEGIN;
ALTER TABLE orders DISABLE TRIGGER USER; ALTER TABLE order_items DISABLE TRIGGER USER;
-- (triggers off during the bulk load so the activity log is not flooded)
"""
tail = """SELECT setval(pg_get_serial_sequence('orders','order_id'),(SELECT MAX(order_id) FROM orders));
SELECT setval(pg_get_serial_sequence('order_items','item_id'),(SELECT MAX(item_id) FROM order_items));
ALTER TABLE orders ENABLE TRIGGER USER; ALTER TABLE order_items ENABLE TRIGGER USER;
COMMIT;
"""
(HERE/"seed_demo_orders.sql").write_text(D + "\n".join(order_sql(o) for o in demo) + "\n" + tail, encoding="utf-8")
print(f"{len(PRODUCTS)} products, {len(RNAMES)} retailers, {len(AREAS)} areas, {len(base_orders)+len(demo)} orders")
