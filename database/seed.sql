-- RouteLedger seed data: 100% synthetic (see generate_seed.py). No real company data.
BEGIN;
SELECT set_config('app.current_employee_id','',true);
ALTER TABLE activity_log DISABLE TRIGGER trg_log_readonly;  -- allow the import step only
ALTER TABLE products DISABLE TRIGGER USER; ALTER TABLE categories DISABLE TRIGGER USER; ALTER TABLE areas DISABLE TRIGGER USER;
ALTER TABLE retailers DISABLE TRIGGER USER; ALTER TABLE branches DISABLE TRIGGER USER; ALTER TABLE orders DISABLE TRIGGER USER; ALTER TABLE order_items DISABLE TRIGGER USER;
-- (triggers are switched off during the import so bulk rows do not flood the activity log)

INSERT INTO categories (name) VALUES ('Beverages'), ('Snacks'), ('Home Care'), ('Personal Care');
INSERT INTO products (category_id,name,pack_size,unit_price) VALUES
((SELECT category_id FROM categories WHERE name='Beverages'),'ZESTORA Lime Fizz 345ml can',24,92.63),
((SELECT category_id FROM categories WHERE name='Beverages'),'ZESTORA Lime Fizz 1500ml PET',6,226.95),
((SELECT category_id FROM categories WHERE name='Beverages'),'ZESTORA Orange Fizz 345ml can',24,97.91),
((SELECT category_id FROM categories WHERE name='Beverages'),'ZESTORA Orange Fizz 1500ml PET',6,223.76),
((SELECT category_id FROM categories WHERE name='Beverages'),'FROSTBITE Energy Drink 250ml can',24,171.89),
((SELECT category_id FROM categories WHERE name='Beverages'),'FROSTBITE Energy Drink 500ml can',12,250.45),
((SELECT category_id FROM categories WHERE name='Beverages'),'AQUARIA Spring Water 500ml',12,41.84),
((SELECT category_id FROM categories WHERE name='Beverages'),'AQUARIA Spring Water 1500ml',6,88.55),
((SELECT category_id FROM categories WHERE name='Beverages'),'AQUARIA Spring Water 19L bottle',1,361.29),
((SELECT category_id FROM categories WHERE name='Beverages'),'LEAFLY Green Tea Bags 25 bags',48,208.68),
((SELECT category_id FROM categories WHERE name='Beverages'),'LEAFLY Green Tea Bags 100 bags',12,708.23),
((SELECT category_id FROM categories WHERE name='Beverages'),'LEAFLY Black Tea Loose 190g',48,327.4),
((SELECT category_id FROM categories WHERE name='Beverages'),'LEAFLY Black Tea Loose 950g',12,1637.08),
((SELECT category_id FROM categories WHERE name='Beverages'),'MANGOLA Mango Drink 250ml',24,63.63),
((SELECT category_id FROM categories WHERE name='Beverages'),'MANGOLA Mango Drink 1000ml',12,202.32),
((SELECT category_id FROM categories WHERE name='Beverages'),'MANGOLA Guava Drink 250ml',24,57.48),
((SELECT category_id FROM categories WHERE name='Beverages'),'MANGOLA Guava Drink 1000ml',12,220.73),
((SELECT category_id FROM categories WHERE name='Beverages'),'SIPPLE Rose Syrup 800ml',12,562.18),
((SELECT category_id FROM categories WHERE name='Beverages'),'SIPPLE Rose Syrup 1500ml',6,957.02),
((SELECT category_id FROM categories WHERE name='Beverages'),'SIPPLE Instant Lemon Mix 500g',12,602.34),
((SELECT category_id FROM categories WHERE name='Beverages'),'SIPPLE Instant Lemon Mix 12g sachet x 20',24,304.07),
((SELECT category_id FROM categories WHERE name='Snacks'),'CRUNCHLY Potato Chips Salted 30g',48,41.76),
((SELECT category_id FROM categories WHERE name='Snacks'),'CRUNCHLY Potato Chips Salted 65g',24,101.26),
((SELECT category_id FROM categories WHERE name='Snacks'),'CRUNCHLY Potato Chips Salted 150g',12,203.54),
((SELECT category_id FROM categories WHERE name='Snacks'),'CRUNCHLY Potato Chips Masala 30g',48,42.5),
((SELECT category_id FROM categories WHERE name='Snacks'),'CRUNCHLY Potato Chips Masala 65g',24,89.3),
((SELECT category_id FROM categories WHERE name='Snacks'),'CRUNCHLY Potato Chips Masala 150g',12,204.21),
((SELECT category_id FROM categories WHERE name='Snacks'),'SPICEROAD Masala Puffs 25g',60,29.64),
((SELECT category_id FROM categories WHERE name='Snacks'),'SPICEROAD Masala Puffs 80g',24,80.81),
((SELECT category_id FROM categories WHERE name='Snacks'),'NUTHAVEN Salted Peanuts 40g',48,52.98),
((SELECT category_id FROM categories WHERE name='Snacks'),'NUTHAVEN Salted Peanuts 200g',24,262.3),
((SELECT category_id FROM categories WHERE name='Snacks'),'NUTHAVEN Mixed Nuts 100g',24,412.99),
((SELECT category_id FROM categories WHERE name='Snacks'),'NUTHAVEN Mixed Nuts 400g',12,1499.41),
((SELECT category_id FROM categories WHERE name='Snacks'),'BISCOTTA Cream Biscuits Vanilla 6 pack',24,65.15),
((SELECT category_id FROM categories WHERE name='Snacks'),'BISCOTTA Cream Biscuits Vanilla 12 pack',12,125.57),
((SELECT category_id FROM categories WHERE name='Snacks'),'BISCOTTA Cream Biscuits Chocolate 6 pack',24,66.85),
((SELECT category_id FROM categories WHERE name='Snacks'),'BISCOTTA Cream Biscuits Chocolate 12 pack',12,139.82),
((SELECT category_id FROM categories WHERE name='Snacks'),'BISCOTTA Tea Rusk 300g',24,228.32),
((SELECT category_id FROM categories WHERE name='Snacks'),'BISCOTTA Tea Rusk 600g',12,418.56),
((SELECT category_id FROM categories WHERE name='Snacks'),'CHOCOMILL Wafer Bar 1 bar',72,35.68),
((SELECT category_id FROM categories WHERE name='Snacks'),'CHOCOMILL Wafer Bar 6 bar pack',24,204.39),
((SELECT category_id FROM categories WHERE name='Snacks'),'CHOCOMILL Hazelnut Spread 200g',24,436.93),
((SELECT category_id FROM categories WHERE name='Snacks'),'CHOCOMILL Hazelnut Spread 750g',12,1455.96),
((SELECT category_id FROM categories WHERE name='Snacks'),'SWEETKIN Fruit Toffee 50 pcs jar',12,332.43),
((SELECT category_id FROM categories WHERE name='Snacks'),'SWEETKIN Fruit Toffee 100 pcs bag',24,567.28),
((SELECT category_id FROM categories WHERE name='Snacks'),'SWEETKIN Chewing Gum 5 pcs',120,25.44),
((SELECT category_id FROM categories WHERE name='Snacks'),'SWEETKIN Chewing Gum 12 pcs',48,70.65),
((SELECT category_id FROM categories WHERE name='Home Care'),'BRIGHTA Dish Liquid Lemon 500ml',24,245.82),
((SELECT category_id FROM categories WHERE name='Home Care'),'BRIGHTA Dish Liquid Lemon 1000ml',12,448.92),
((SELECT category_id FROM categories WHERE name='Home Care'),'BRIGHTA Dish Liquid Lemon 3000ml',4,1153.05),
((SELECT category_id FROM categories WHERE name='Home Care'),'SPARKLO Laundry Powder 500g',24,282.52),
((SELECT category_id FROM categories WHERE name='Home Care'),'SPARKLO Laundry Powder 1000g',12,460.63),
((SELECT category_id FROM categories WHERE name='Home Care'),'SPARKLO Laundry Powder 4000g',4,1833.5),
((SELECT category_id FROM categories WHERE name='Home Care'),'SPARKLO Laundry Liquid 1000ml',12,755.07),
((SELECT category_id FROM categories WHERE name='Home Care'),'SPARKLO Laundry Liquid 3000ml',4,1938.97),
((SELECT category_id FROM categories WHERE name='Home Care'),'SOFTWAVE Fabric Softener 1000ml',12,611.91),
((SELECT category_id FROM categories WHERE name='Home Care'),'SOFTWAVE Fabric Softener 2500ml',4,1288.06),
((SELECT category_id FROM categories WHERE name='Home Care'),'FRESHNEST Floor Cleaner Pine 500ml',24,248.06),
((SELECT category_id FROM categories WHERE name='Home Care'),'FRESHNEST Floor Cleaner Pine 1000ml',12,451.49),
((SELECT category_id FROM categories WHERE name='Home Care'),'FRESHNEST Floor Cleaner Pine 3000ml',4,1180.2),
((SELECT category_id FROM categories WHERE name='Home Care'),'FRESHNEST Glass Cleaner 500ml',24,283.24),
((SELECT category_id FROM categories WHERE name='Home Care'),'ZAPP Insect Spray 300ml',24,384.47),
((SELECT category_id FROM categories WHERE name='Home Care'),'ZAPP Insect Spray 600ml',12,747.5),
((SELECT category_id FROM categories WHERE name='Home Care'),'TISSUELY Facial Tissue Box 100 pulls',36,122.53),
((SELECT category_id FROM categories WHERE name='Home Care'),'TISSUELY Facial Tissue Box 200 pulls',24,219.0),
((SELECT category_id FROM categories WHERE name='Home Care'),'TISSUELY Kitchen Roll 2 roll pack',24,259.36),
((SELECT category_id FROM categories WHERE name='Home Care'),'TISSUELY Kitchen Roll 6 roll pack',8,786.47),
((SELECT category_id FROM categories WHERE name='Home Care'),'NESTWELL Garbage Bags Medium 20 bags',36,205.31),
((SELECT category_id FROM categories WHERE name='Home Care'),'NESTWELL Garbage Bags Medium 50 bags',18,420.25),
((SELECT category_id FROM categories WHERE name='Personal Care'),'LUMENA Shampoo Silky 180ml',24,382.18),
((SELECT category_id FROM categories WHERE name='Personal Care'),'LUMENA Shampoo Silky 375ml',12,641.92),
((SELECT category_id FROM categories WHERE name='Personal Care'),'LUMENA Shampoo Silky 700ml',8,1236.71),
((SELECT category_id FROM categories WHERE name='Personal Care'),'LUMENA Shampoo Anti-Dandruff 180ml',24,406.85),
((SELECT category_id FROM categories WHERE name='Personal Care'),'LUMENA Shampoo Anti-Dandruff 375ml',12,783.95),
((SELECT category_id FROM categories WHERE name='Personal Care'),'LUMENA Conditioner 180ml',24,413.29),
((SELECT category_id FROM categories WHERE name='Personal Care'),'LUMENA Conditioner 375ml',12,716.6),
((SELECT category_id FROM categories WHERE name='Personal Care'),'DERMIQ Face Wash Neem 100ml',36,280.89),
((SELECT category_id FROM categories WHERE name='Personal Care'),'DERMIQ Face Wash Neem 150ml',24,392.79),
((SELECT category_id FROM categories WHERE name='Personal Care'),'DERMIQ Face Wash Charcoal 100ml',36,272.53),
((SELECT category_id FROM categories WHERE name='Personal Care'),'DERMIQ Face Wash Charcoal 150ml',24,394.4),
((SELECT category_id FROM categories WHERE name='Personal Care'),'SMILEWORKS Toothpaste Mint 50g',72,90.11),
((SELECT category_id FROM categories WHERE name='Personal Care'),'SMILEWORKS Toothpaste Mint 100g',48,159.78),
((SELECT category_id FROM categories WHERE name='Personal Care'),'SMILEWORKS Toothpaste Mint 200g',24,288.31),
((SELECT category_id FROM categories WHERE name='Personal Care'),'SMILEWORKS Toothbrush Medium 1 pc',144,73.54),
((SELECT category_id FROM categories WHERE name='Personal Care'),'SMILEWORKS Toothbrush Medium 3 pc pack',36,183.69),
((SELECT category_id FROM categories WHERE name='Personal Care'),'AQUAVEIL Body Lotion 200ml',24,404.08),
((SELECT category_id FROM categories WHERE name='Personal Care'),'AQUAVEIL Body Lotion 400ml',12,749.71),
((SELECT category_id FROM categories WHERE name='Personal Care'),'PURENEST Hand Wash 250ml',24,245.67),
((SELECT category_id FROM categories WHERE name='Personal Care'),'PURENEST Hand Wash 500ml refill',12,364.14),
((SELECT category_id FROM categories WHERE name='Personal Care'),'PURENEST Beauty Soap 100g',72,79.71),
((SELECT category_id FROM categories WHERE name='Personal Care'),'PURENEST Beauty Soap 3 pack',24,233.08),
((SELECT category_id FROM categories WHERE name='Personal Care'),'GLIDEX Razor Twin Blade 1 pc',144,58.86),
((SELECT category_id FROM categories WHERE name='Personal Care'),'GLIDEX Razor Twin Blade 5 pc pack',36,254.23);
INSERT INTO areas (name) VALUES ('Gulberg'), ('DHA Phase 5'), ('Johar Town'), ('Model Town'), ('Iqbal Town'), ('Shadman'), ('Samanabad'), ('Garden Town'), ('Wapda Town'), ('Bahria Town'), ('Cantt'), ('Township'), ('Faisal Town'), ('Valencia Town'), ('Askari'), ('Ravi Road'), ('Mughalpura'), ('Shalimar'), ('Raiwind Road'), ('Thokar Niaz Baig');
INSERT INTO retailers (name) VALUES ('Minar Superstore'), ('Ravi Fresh Stores'), ('Lahori Basket'), ('Haveli Provisions'), ('Jasmine Supermart'), ('Kite Corner Stores'), ('Baradari Mart'), ('Mehtab Superstore'), ('Lotus Mini Mart'), ('Chenab Grocers'), ('Karvaan Mart'), ('Zeenat Family Store'), ('Rahat Daily Needs'), ('Sitara Hypermart');
INSERT INTO branches (retailer_id,area_id,branch_name) VALUES
((SELECT retailer_id FROM retailers WHERE name='Minar Superstore'),(SELECT area_id FROM areas WHERE name='Gulberg'),'Gulberg'),
((SELECT retailer_id FROM retailers WHERE name='Minar Superstore'),(SELECT area_id FROM areas WHERE name='DHA Phase 5'),'DHA Phase 5'),
((SELECT retailer_id FROM retailers WHERE name='Minar Superstore'),(SELECT area_id FROM areas WHERE name='Model Town'),'Model Town'),
((SELECT retailer_id FROM retailers WHERE name='Minar Superstore'),(SELECT area_id FROM areas WHERE name='Johar Town'),'Johar Town'),
((SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores'),(SELECT area_id FROM areas WHERE name='Ravi Road'),'Ravi Road'),
((SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores'),(SELECT area_id FROM areas WHERE name='Shalimar'),'Shalimar'),
((SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores'),(SELECT area_id FROM areas WHERE name='Mughalpura'),'Mughalpura'),
((SELECT retailer_id FROM retailers WHERE name='Lahori Basket'),(SELECT area_id FROM areas WHERE name='Garden Town'),'Garden Town'),
((SELECT retailer_id FROM retailers WHERE name='Lahori Basket'),(SELECT area_id FROM areas WHERE name='Faisal Town'),'Faisal Town'),
((SELECT retailer_id FROM retailers WHERE name='Haveli Provisions'),(SELECT area_id FROM areas WHERE name='Cantt'),'Cantt'),
((SELECT retailer_id FROM retailers WHERE name='Haveli Provisions'),(SELECT area_id FROM areas WHERE name='Askari'),'Askari'),
((SELECT retailer_id FROM retailers WHERE name='Haveli Provisions'),(SELECT area_id FROM areas WHERE name='Gulberg'),'Gulberg'),
((SELECT retailer_id FROM retailers WHERE name='Haveli Provisions'),(SELECT area_id FROM areas WHERE name='Township'),'Township'),
((SELECT retailer_id FROM retailers WHERE name='Haveli Provisions'),(SELECT area_id FROM areas WHERE name='Samanabad'),'Samanabad'),
((SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),(SELECT area_id FROM areas WHERE name='Johar Town'),'Johar Town'),
((SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),(SELECT area_id FROM areas WHERE name='Wapda Town'),'Wapda Town'),
((SELECT retailer_id FROM retailers WHERE name='Kite Corner Stores'),(SELECT area_id FROM areas WHERE name='Iqbal Town'),'Iqbal Town'),
((SELECT retailer_id FROM retailers WHERE name='Baradari Mart'),(SELECT area_id FROM areas WHERE name='Shadman'),'Shadman'),
((SELECT retailer_id FROM retailers WHERE name='Baradari Mart'),(SELECT area_id FROM areas WHERE name='Model Town'),'Model Town'),
((SELECT retailer_id FROM retailers WHERE name='Mehtab Superstore'),(SELECT area_id FROM areas WHERE name='DHA Phase 5'),'DHA Phase 5'),
((SELECT retailer_id FROM retailers WHERE name='Mehtab Superstore'),(SELECT area_id FROM areas WHERE name='Bahria Town'),'Bahria Town'),
((SELECT retailer_id FROM retailers WHERE name='Mehtab Superstore'),(SELECT area_id FROM areas WHERE name='Askari'),'Askari'),
((SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart'),(SELECT area_id FROM areas WHERE name='Valencia Town'),'Valencia Town'),
((SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart'),(SELECT area_id FROM areas WHERE name='Wapda Town'),'Wapda Town'),
((SELECT retailer_id FROM retailers WHERE name='Chenab Grocers'),(SELECT area_id FROM areas WHERE name='Raiwind Road'),'Raiwind Road'),
((SELECT retailer_id FROM retailers WHERE name='Chenab Grocers'),(SELECT area_id FROM areas WHERE name='Thokar Niaz Baig'),'Thokar Niaz Baig'),
((SELECT retailer_id FROM retailers WHERE name='Chenab Grocers'),(SELECT area_id FROM areas WHERE name='Township'),'Township'),
((SELECT retailer_id FROM retailers WHERE name='Karvaan Mart'),(SELECT area_id FROM areas WHERE name='Cantt'),'Cantt'),
((SELECT retailer_id FROM retailers WHERE name='Karvaan Mart'),(SELECT area_id FROM areas WHERE name='Gulberg'),'Gulberg'),
((SELECT retailer_id FROM retailers WHERE name='Zeenat Family Store'),(SELECT area_id FROM areas WHERE name='Samanabad'),'Samanabad'),
((SELECT retailer_id FROM retailers WHERE name='Zeenat Family Store'),(SELECT area_id FROM areas WHERE name='Iqbal Town'),'Iqbal Town'),
((SELECT retailer_id FROM retailers WHERE name='Zeenat Family Store'),(SELECT area_id FROM areas WHERE name='Faisal Town'),'Faisal Town'),
((SELECT retailer_id FROM retailers WHERE name='Rahat Daily Needs'),(SELECT area_id FROM areas WHERE name='Shalimar'),'Shalimar'),
((SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT area_id FROM areas WHERE name='Bahria Town'),'Bahria Town'),
((SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT area_id FROM areas WHERE name='DHA Phase 5'),'DHA Phase 5'),
((SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT area_id FROM areas WHERE name='Johar Town'),'Johar Town'),
((SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT area_id FROM areas WHERE name='Valencia Town'),'Valencia Town');
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (1,(SELECT retailer_id FROM retailers WHERE name='Rahat Daily Needs'),NULL,'2026-08-20');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (1,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 1000g'),10,5379.42,53794.2);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (1,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 500g'),4,6598.76,26395.04);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (1,(SELECT product_id FROM products WHERE name='MANGOLA Mango Drink 250ml'),4,1486.19,5944.76);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (1,(SELECT product_id FROM products WHERE name='ZAPP Insect Spray 300ml'),7,8979.99,62859.93);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (2,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='DHA Phase 5'),'2026-08-10');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (2,(SELECT product_id FROM products WHERE name='SWEETKIN Fruit Toffee 100 pcs bag'),8,13941.47,111531.76);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (2,(SELECT product_id FROM products WHERE name='DERMIQ Face Wash Neem 150ml'),4,9653.21,38612.84);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (2,(SELECT product_id FROM products WHERE name='SWEETKIN Chewing Gum 12 pcs'),8,3472.59,27780.72);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (3,(SELECT retailer_id FROM retailers WHERE name='Haveli Provisions'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Haveli Provisions') AND branch_name='Gulberg'),'2026-07-31');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (3,(SELECT product_id FROM products WHERE name='TISSUELY Kitchen Roll 6 roll pack'),4,6104.27,24417.08);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (3,(SELECT product_id FROM products WHERE name='ZESTORA Orange Fizz 345ml can'),4,2279.81,9119.24);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (4,(SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores') AND branch_name='Mughalpura'),'2026-07-24');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (4,(SELECT product_id FROM products WHERE name='SPICEROAD Masala Puffs 80g'),15,1949.72,29245.8);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (4,(SELECT product_id FROM products WHERE name='NESTWELL Garbage Bags Medium 50 bags'),1,7604.59,7604.59);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (4,(SELECT product_id FROM products WHERE name='LUMENA Shampoo Silky 180ml'),13,9220.93,119872.09);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (5,(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart') AND branch_name='Valencia Town'),'2026-07-02');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (5,(SELECT product_id FROM products WHERE name='FRESHNEST Glass Cleaner 500ml'),2,6875.25,13750.5);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (5,(SELECT product_id FROM products WHERE name='BISCOTTA Cream Biscuits Vanilla 6 pack'),7,1581.43,11070.01);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (5,(SELECT product_id FROM products WHERE name='CRUNCHLY Potato Chips Masala 30g'),5,2063.26,10316.3);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (6,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart') AND branch_name='Johar Town'),'2026-07-31');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (6,(SELECT product_id FROM products WHERE name='SMILEWORKS Toothpaste Mint 200g'),3,6885.53,20656.59);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (6,(SELECT product_id FROM products WHERE name='LEAFLY Green Tea Bags 100 bags'),12,8457.12,101485.44);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (6,(SELECT product_id FROM products WHERE name='SMILEWORKS Toothbrush Medium 3 pc pack'),23,6580.44,151350.12);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (7,(SELECT retailer_id FROM retailers WHERE name='Chenab Grocers'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Chenab Grocers') AND branch_name='Township'),'2026-07-26');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (7,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 1000g'),5,5532.53,27662.65);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (7,(SELECT product_id FROM products WHERE name='LEAFLY Green Tea Bags 100 bags'),14,8506.41,119089.74);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (7,(SELECT product_id FROM products WHERE name='GLIDEX Razor Twin Blade 5 pc pack'),12,9160.52,109926.24);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (7,(SELECT product_id FROM products WHERE name='SIPPLE Instant Lemon Mix 12g sachet x 20'),9,7304.25,65738.25);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (8,(SELECT retailer_id FROM retailers WHERE name='Minar Superstore'),NULL,'2026-08-11');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (8,(SELECT product_id FROM products WHERE name='NESTWELL Garbage Bags Medium 20 bags'),13,7384.51,95998.63);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (9,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='DHA Phase 5'),'2026-07-02');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (9,(SELECT product_id FROM products WHERE name='SPICEROAD Masala Puffs 25g'),3,1821.08,5463.24);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (9,(SELECT product_id FROM products WHERE name='BISCOTTA Tea Rusk 300g'),5,5611.19,28055.95);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (9,(SELECT product_id FROM products WHERE name='TISSUELY Facial Tissue Box 200 pulls'),6,5382.14,32292.84);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (10,(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart'),NULL,'2026-07-27');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (10,(SELECT product_id FROM products WHERE name='MANGOLA Guava Drink 1000ml'),2,2678.96,5357.92);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (10,(SELECT product_id FROM products WHERE name='NESTWELL Garbage Bags Medium 50 bags'),14,7650.74,107110.36);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (10,(SELECT product_id FROM products WHERE name='SIPPLE Instant Lemon Mix 500g'),7,7310.48,51173.36);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (10,(SELECT product_id FROM products WHERE name='NESTWELL Garbage Bags Medium 20 bags'),10,7475.42,74754.2);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (10,(SELECT product_id FROM products WHERE name='TISSUELY Kitchen Roll 2 roll pack'),9,6295.6,56660.4);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (11,(SELECT retailer_id FROM retailers WHERE name='Rahat Daily Needs'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Rahat Daily Needs') AND branch_name='Shalimar'),'2026-07-16');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (11,(SELECT product_id FROM products WHERE name='BISCOTTA Cream Biscuits Chocolate 6 pack'),19,1561.4,29666.6);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (11,(SELECT product_id FROM products WHERE name='FROSTBITE Energy Drink 500ml can'),12,2924.86,35098.32);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (12,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='DHA Phase 5'),'2026-08-13');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (12,(SELECT product_id FROM products WHERE name='NESTWELL Garbage Bags Medium 50 bags'),11,7746.05,85206.55);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (12,(SELECT product_id FROM products WHERE name='ZAPP Insect Spray 300ml'),17,9448.73,160628.41);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (12,(SELECT product_id FROM products WHERE name='TISSUELY Facial Tissue Box 200 pulls'),7,5382.14,37674.98);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (12,(SELECT product_id FROM products WHERE name='NUTHAVEN Mixed Nuts 100g'),7,10149.64,71047.48);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (12,(SELECT product_id FROM products WHERE name='PURENEST Beauty Soap 100g'),13,5876.86,76399.18);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (13,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart') AND branch_name='Johar Town'),'2026-08-27');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (13,(SELECT product_id FROM products WHERE name='GLIDEX Razor Twin Blade 1 pc'),11,8434.31,92777.41);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (13,(SELECT product_id FROM products WHERE name='SMILEWORKS Toothpaste Mint 200g'),6,6885.53,41313.18);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (14,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='DHA Phase 5'),'2026-08-15');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (14,(SELECT product_id FROM products WHERE name='TISSUELY Kitchen Roll 2 roll pack'),4,6374.03,25496.12);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (14,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 1000g'),10,5660.22,56602.2);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (14,(SELECT product_id FROM products WHERE name='SWEETKIN Fruit Toffee 50 pcs jar'),3,4084.9,12254.7);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (14,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Liquid 1000ml'),12,9278.3,111339.6);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (15,(SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores'),NULL,'2026-08-20');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (15,(SELECT product_id FROM products WHERE name='MANGOLA Mango Drink 250ml'),15,1535.21,23028.15);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (15,(SELECT product_id FROM products WHERE name='LEAFLY Green Tea Bags 100 bags'),3,8543.8,25631.4);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (16,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='Johar Town'),'2026-07-26');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (16,(SELECT product_id FROM products WHERE name='NESTWELL Garbage Bags Medium 50 bags'),12,7746.05,92952.6);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (16,(SELECT product_id FROM products WHERE name='TISSUELY Kitchen Roll 2 roll pack'),14,6374.03,89236.42);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (17,(SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores'),NULL,'2026-08-10');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (17,(SELECT product_id FROM products WHERE name='BISCOTTA Cream Biscuits Vanilla 6 pack'),8,1571.89,12575.12);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (18,(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart'),NULL,'2026-07-18');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (18,(SELECT product_id FROM products WHERE name='MANGOLA Guava Drink 1000ml'),6,2678.96,16073.76);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (18,(SELECT product_id FROM products WHERE name='FROSTBITE Energy Drink 500ml can'),9,3039.66,27356.94);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (18,(SELECT product_id FROM products WHERE name='NESTWELL Garbage Bags Medium 20 bags'),7,7475.42,52327.94);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (18,(SELECT product_id FROM products WHERE name='PURENEST Beauty Soap 3 pack'),1,5657.69,5657.69);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (18,(SELECT product_id FROM products WHERE name='NUTHAVEN Salted Peanuts 200g'),2,6366.97,12733.94);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (19,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='DHA Phase 5'),'2026-08-29');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (19,(SELECT product_id FROM products WHERE name='MANGOLA Mango Drink 250ml'),14,1563.77,21892.78);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (19,(SELECT product_id FROM products WHERE name='SMILEWORKS Toothbrush Medium 3 pc pack'),6,6771.55,40629.3);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (19,(SELECT product_id FROM products WHERE name='SMILEWORKS Toothbrush Medium 1 pc'),5,10843.91,54219.55);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (19,(SELECT product_id FROM products WHERE name='SOFTWAVE Fabric Softener 1000ml'),22,7519.15,165421.3);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (20,(SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores') AND branch_name='Shalimar'),'2026-08-25');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (20,(SELECT product_id FROM products WHERE name='AQUAVEIL Body Lotion 200ml'),5,9749.32,48746.6);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (20,(SELECT product_id FROM products WHERE name='BISCOTTA Cream Biscuits Chocolate 12 pack'),3,1686.73,5060.19);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (20,(SELECT product_id FROM products WHERE name='DERMIQ Face Wash Neem 100ml'),6,10165.63,60993.78);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (20,(SELECT product_id FROM products WHERE name='NUTHAVEN Mixed Nuts 100g'),2,9964.29,19928.58);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (20,(SELECT product_id FROM products WHERE name='PURENEST Hand Wash 500ml refill'),8,4392.84,35142.72);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (21,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart') AND branch_name='Johar Town'),'2026-07-06');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (21,(SELECT product_id FROM products WHERE name='LEAFLY Black Tea Loose 190g'),10,15638.2,156382.0);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (21,(SELECT product_id FROM products WHERE name='SIPPLE Rose Syrup 1500ml'),4,5713.98,22855.92);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (21,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 1000g'),16,5500.47,88007.52);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (22,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='Valencia Town'),'2026-08-18');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (22,(SELECT product_id FROM products WHERE name='GLIDEX Razor Twin Blade 5 pc pack'),4,9371.93,37487.72);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (22,(SELECT product_id FROM products WHERE name='TISSUELY Facial Tissue Box 100 pulls'),16,4516.95,72271.2);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (22,(SELECT product_id FROM products WHERE name='SIPPLE Instant Lemon Mix 500g'),6,7401.55,44409.3);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (23,(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart'),NULL,'2026-08-18');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (23,(SELECT product_id FROM products WHERE name='LUMENA Shampoo Anti-Dandruff 180ml'),20,9875.71,197514.2);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (23,(SELECT product_id FROM products WHERE name='ZESTORA Orange Fizz 345ml can'),4,2376.63,9506.52);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (23,(SELECT product_id FROM products WHERE name='PURENEST Hand Wash 250ml'),11,5963.3,65596.3);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (23,(SELECT product_id FROM products WHERE name='LUMENA Conditioner 180ml'),15,10032.04,150480.6);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (23,(SELECT product_id FROM products WHERE name='GLIDEX Razor Twin Blade 1 pc'),8,8572.46,68579.68);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (24,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='Bahria Town'),'2026-08-12');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (24,(SELECT product_id FROM products WHERE name='AQUARIA Spring Water 19L bottle'),2,369.96,739.92);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (24,(SELECT product_id FROM products WHERE name='FRESHNEST Glass Cleaner 500ml'),3,6960.91,20882.73);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (24,(SELECT product_id FROM products WHERE name='NUTHAVEN Mixed Nuts 400g'),6,18424.75,110548.5);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (24,(SELECT product_id FROM products WHERE name='LEAFLY Green Tea Bags 25 bags'),6,10257.04,61542.24);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (24,(SELECT product_id FROM products WHERE name='BISCOTTA Cream Biscuits Vanilla 6 pack'),11,1601.13,17612.43);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (25,(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart') AND branch_name='Wapda Town'),'2026-08-09');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (25,(SELECT product_id FROM products WHERE name='SIPPLE Rose Syrup 800ml'),3,6823.07,20469.21);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (25,(SELECT product_id FROM products WHERE name='ZESTORA Lime Fizz 1500ml PET'),20,1377.22,27544.4);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (25,(SELECT product_id FROM products WHERE name='ZAPP Insect Spray 300ml'),4,9332.47,37329.88);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (25,(SELECT product_id FROM products WHERE name='AQUARIA Spring Water 1500ml'),8,537.36,4298.88);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (25,(SELECT product_id FROM products WHERE name='ZAPP Insect Spray 600ml'),6,9072.26,54433.56);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (26,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='Johar Town'),'2026-07-25');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (26,(SELECT product_id FROM products WHERE name='CRUNCHLY Potato Chips Masala 150g'),10,2509.33,25093.3);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (26,(SELECT product_id FROM products WHERE name='LEAFLY Green Tea Bags 25 bags'),18,10257.04,184626.72);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (27,(SELECT retailer_id FROM retailers WHERE name='Haveli Provisions'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Haveli Provisions') AND branch_name='Samanabad'),'2026-07-18');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (27,(SELECT product_id FROM products WHERE name='PURENEST Beauty Soap 3 pack'),6,5427.22,32563.32);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (28,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='DHA Phase 5'),'2026-07-01');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (28,(SELECT product_id FROM products WHERE name='PURENEST Hand Wash 250ml'),15,6037.59,90563.85);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (28,(SELECT product_id FROM products WHERE name='FRESHNEST Floor Cleaner Pine 500ml'),7,6096.32,42674.24);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (28,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 1000g'),6,5660.22,33961.32);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (28,(SELECT product_id FROM products WHERE name='BISCOTTA Tea Rusk 600g'),6,5143.27,30859.62);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (29,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='Bahria Town'),'2026-08-27');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (29,(SELECT product_id FROM products WHERE name='NUTHAVEN Mixed Nuts 400g'),10,18424.75,184247.5);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (29,(SELECT product_id FROM products WHERE name='BRIGHTA Dish Liquid Lemon 500ml'),7,6041.27,42288.89);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (29,(SELECT product_id FROM products WHERE name='AQUARIA Spring Water 19L bottle'),17,369.96,6289.32);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (30,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='Johar Town'),'2026-07-28');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (30,(SELECT product_id FROM products WHERE name='CHOCOMILL Wafer Bar 6 bar pack'),28,5023.09,140646.52);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (30,(SELECT product_id FROM products WHERE name='CRUNCHLY Potato Chips Masala 30g'),11,2088.96,22978.56);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (30,(SELECT product_id FROM products WHERE name='BRIGHTA Dish Liquid Lemon 500ml'),6,6041.27,36247.62);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (30,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Liquid 3000ml'),11,7942.02,87362.22);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (30,(SELECT product_id FROM products WHERE name='ZESTORA Orange Fizz 1500ml PET'),3,1374.78,4124.34);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (31,(SELECT retailer_id FROM retailers WHERE name='Kite Corner Stores'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Kite Corner Stores') AND branch_name='Iqbal Town'),'2026-07-26');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (31,(SELECT product_id FROM products WHERE name='BISCOTTA Tea Rusk 600g'),10,4983.54,49835.4);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (31,(SELECT product_id FROM products WHERE name='ZAPP Insect Spray 300ml'),5,9155.31,45776.55);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (32,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),NULL,'2026-08-01');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (32,(SELECT product_id FROM products WHERE name='SPICEROAD Masala Puffs 80g'),9,1929.94,17369.46);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (32,(SELECT product_id FROM products WHERE name='FRESHNEST Floor Cleaner Pine 500ml'),3,5924.27,17772.81);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (32,(SELECT product_id FROM products WHERE name='CHOCOMILL Hazelnut Spread 750g'),6,17385.91,104315.46);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (32,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Liquid 3000ml'),15,7717.88,115768.2);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (32,(SELECT product_id FROM products WHERE name='SIPPLE Rose Syrup 800ml'),4,6713.1,26852.4);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (33,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart') AND branch_name='Johar Town'),'2026-08-01');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (33,(SELECT product_id FROM products WHERE name='LUMENA Shampoo Anti-Dandruff 375ml'),15,9361.3,140419.5);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (33,(SELECT product_id FROM products WHERE name='SWEETKIN Chewing Gum 12 pcs'),5,3374.58,16872.9);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (33,(SELECT product_id FROM products WHERE name='MANGOLA Guava Drink 1000ml'),7,2635.78,18450.46);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (34,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),NULL,'2026-07-09');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (34,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Liquid 3000ml'),8,7942.02,63536.16);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (35,(SELECT retailer_id FROM retailers WHERE name='Minar Superstore'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Minar Superstore') AND branch_name='Johar Town'),'2026-07-29');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (35,(SELECT product_id FROM products WHERE name='MANGOLA Mango Drink 250ml'),3,1525.75,4577.25);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (35,(SELECT product_id FROM products WHERE name='SPICEROAD Masala Puffs 80g'),21,1937.69,40691.49);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (36,(SELECT retailer_id FROM retailers WHERE name='Rahat Daily Needs'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Rahat Daily Needs') AND branch_name='Shalimar'),'2026-07-01');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (36,(SELECT product_id FROM products WHERE name='NUTHAVEN Salted Peanuts 40g'),45,2474.89,111370.05);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (36,(SELECT product_id FROM products WHERE name='LUMENA Shampoo Anti-Dandruff 180ml'),6,9502.71,57016.26);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (37,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart') AND branch_name='Johar Town'),'2026-07-07');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (37,(SELECT product_id FROM products WHERE name='BISCOTTA Tea Rusk 600g'),9,4998.11,44982.99);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (38,(SELECT retailer_id FROM retailers WHERE name='Baradari Mart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Baradari Mart') AND branch_name='Shadman'),'2026-07-01');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (38,(SELECT product_id FROM products WHERE name='BISCOTTA Tea Rusk 600g'),16,5042.81,80684.96);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (38,(SELECT product_id FROM products WHERE name='FRESHNEST Floor Cleaner Pine 1000ml'),9,5439.55,48955.95);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (38,(SELECT product_id FROM products WHERE name='BISCOTTA Cream Biscuits Chocolate 6 pack'),3,1610.82,4832.46);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (38,(SELECT product_id FROM products WHERE name='CHOCOMILL Wafer Bar 6 bar pack'),11,4924.98,54174.78);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (38,(SELECT product_id FROM products WHERE name='SMILEWORKS Toothpaste Mint 200g'),11,6947.12,76418.32);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (39,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart') AND branch_name='Wapda Town'),'2026-07-15');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (39,(SELECT product_id FROM products WHERE name='FROSTBITE Energy Drink 250ml can'),6,4105.15,24630.9);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (39,(SELECT product_id FROM products WHERE name='PURENEST Beauty Soap 100g'),17,5711.0,97087.0);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (39,(SELECT product_id FROM products WHERE name='SWEETKIN Fruit Toffee 50 pcs jar'),2,3969.61,7939.22);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (39,(SELECT product_id FROM products WHERE name='GLIDEX Razor Twin Blade 1 pc'),5,8434.31,42171.55);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (40,(SELECT retailer_id FROM retailers WHERE name='Rahat Daily Needs'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Rahat Daily Needs') AND branch_name='Shalimar'),'2026-08-09');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (40,(SELECT product_id FROM products WHERE name='SPICEROAD Masala Puffs 80g'),6,1887.46,11324.76);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (40,(SELECT product_id FROM products WHERE name='ZAPP Insect Spray 600ml'),7,8729.6,61107.2);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (41,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='Bahria Town'),'2026-08-15');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (41,(SELECT product_id FROM products WHERE name='CRUNCHLY Potato Chips Salted 150g'),2,2501.1,5002.2);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (42,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='Bahria Town'),'2026-08-29');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (42,(SELECT product_id FROM products WHERE name='CHOCOMILL Hazelnut Spread 750g'),12,17890.84,214690.08);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (42,(SELECT product_id FROM products WHERE name='CRUNCHLY Potato Chips Masala 30g'),6,2088.96,12533.76);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (43,(SELECT retailer_id FROM retailers WHERE name='Haveli Provisions'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Haveli Provisions') AND branch_name='Gulberg'),'2026-07-06');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (43,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Liquid 1000ml'),2,8790.83,17581.66);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (43,(SELECT product_id FROM products WHERE name='MANGOLA Guava Drink 250ml'),19,1338.41,25429.79);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (43,(SELECT product_id FROM products WHERE name='LUMENA Shampoo Silky 700ml'),2,9598.85,19197.7);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (44,(SELECT retailer_id FROM retailers WHERE name='Baradari Mart'),NULL,'2026-07-13');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (44,(SELECT product_id FROM products WHERE name='SWEETKIN Chewing Gum 12 pcs'),11,3404.76,37452.36);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (44,(SELECT product_id FROM products WHERE name='FRESHNEST Glass Cleaner 500ml'),12,6824.95,81899.4);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (44,(SELECT product_id FROM products WHERE name='ZESTORA Orange Fizz 1500ml PET'),6,1347.93,8087.58);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (45,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='DHA Phase 5'),'2026-08-17');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (45,(SELECT product_id FROM products WHERE name='DERMIQ Face Wash Neem 150ml'),6,9653.21,57919.26);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (46,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='Johar Town'),'2026-08-17');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (46,(SELECT product_id FROM products WHERE name='BISCOTTA Cream Biscuits Chocolate 6 pack'),19,1642.91,31215.29);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (46,(SELECT product_id FROM products WHERE name='BISCOTTA Tea Rusk 600g'),7,5143.27,36002.89);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (46,(SELECT product_id FROM products WHERE name='ZESTORA Lime Fizz 345ml can'),14,2276.47,31870.58);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (47,(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart') AND branch_name='Wapda Town'),'2026-08-22');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (47,(SELECT product_id FROM products WHERE name='DERMIQ Face Wash Neem 150ml'),6,9534.43,57206.58);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (47,(SELECT product_id FROM products WHERE name='NUTHAVEN Salted Peanuts 200g'),3,6366.97,19100.91);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (48,(SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Ravi Fresh Stores') AND branch_name='Ravi Road'),'2026-07-16');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (48,(SELECT product_id FROM products WHERE name='AQUARIA Spring Water 19L bottle'),10,363.2,3632.0);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (48,(SELECT product_id FROM products WHERE name='SMILEWORKS Toothbrush Medium 1 pc'),8,10645.89,85167.12);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (48,(SELECT product_id FROM products WHERE name='FROSTBITE Energy Drink 250ml can'),8,4147.22,33177.76);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (48,(SELECT product_id FROM products WHERE name='ZAPP Insect Spray 300ml'),6,9276.18,55657.08);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (49,(SELECT retailer_id FROM retailers WHERE name='Karvaan Mart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Karvaan Mart') AND branch_name='Cantt'),'2026-08-19');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (49,(SELECT product_id FROM products WHERE name='BISCOTTA Tea Rusk 300g'),5,5518.59,27592.95);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (49,(SELECT product_id FROM products WHERE name='BISCOTTA Cream Biscuits Chocolate 6 pack'),5,1615.79,8078.95);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (49,(SELECT product_id FROM products WHERE name='LUMENA Shampoo Anti-Dandruff 180ml'),5,9833.73,49168.65);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (50,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),NULL,'2026-07-13');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (50,(SELECT product_id FROM products WHERE name='AQUARIA Spring Water 19L bottle'),1,359.52,359.52);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (50,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 500g'),3,6747.26,20241.78);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (50,(SELECT product_id FROM products WHERE name='NUTHAVEN Mixed Nuts 400g'),6,17904.75,107428.5);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (51,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),NULL,'2026-08-06');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (51,(SELECT product_id FROM products WHERE name='BRIGHTA Dish Liquid Lemon 500ml'),9,5870.77,52836.93);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (52,(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart') AND branch_name='Valencia Town'),'2026-07-07');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (52,(SELECT product_id FROM products WHERE name='PURENEST Beauty Soap 3 pack'),7,5657.69,39603.83);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (52,(SELECT product_id FROM products WHERE name='DERMIQ Face Wash Charcoal 150ml'),5,9573.51,47867.55);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (52,(SELECT product_id FROM products WHERE name='SWEETKIN Fruit Toffee 100 pcs bag'),13,13769.93,179009.09);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (52,(SELECT product_id FROM products WHERE name='SPICEROAD Masala Puffs 25g'),4,1798.67,7194.68);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (52,(SELECT product_id FROM products WHERE name='FROSTBITE Energy Drink 250ml can'),4,4172.39,16689.56);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (53,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart') AND branch_name='Wapda Town'),'2026-07-05');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (53,(SELECT product_id FROM products WHERE name='LEAFLY Black Tea Loose 950g'),3,19548.7,58646.1);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (53,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 500g'),12,6747.26,80967.12);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (53,(SELECT product_id FROM products WHERE name='SMILEWORKS Toothbrush Medium 3 pc pack'),13,6580.44,85545.72);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (53,(SELECT product_id FROM products WHERE name='LUMENA Shampoo Silky 375ml'),22,7665.3,168636.6);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (54,(SELECT retailer_id FROM retailers WHERE name='Minar Superstore'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Minar Superstore') AND branch_name='Model Town'),'2026-08-11');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (54,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 500g'),23,6774.38,155810.74);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (54,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 1000g'),18,5522.59,99406.62);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (55,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='DHA Phase 5'),'2026-07-09');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (55,(SELECT product_id FROM products WHERE name='AQUARIA Spring Water 500ml'),10,514.13,5141.3);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (56,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='Johar Town'),'2026-08-17');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (56,(SELECT product_id FROM products WHERE name='CRUNCHLY Potato Chips Salted 30g'),13,2052.59,26683.67);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (56,(SELECT product_id FROM products WHERE name='SIPPLE Rose Syrup 1500ml'),3,5879.93,17639.79);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (56,(SELECT product_id FROM products WHERE name='SWEETKIN Fruit Toffee 100 pcs bag'),5,13941.47,69707.35);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (56,(SELECT product_id FROM products WHERE name='BISCOTTA Cream Biscuits Chocolate 12 pack'),8,1718.11,13744.88);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (56,(SELECT product_id FROM products WHERE name='SIPPLE Instant Lemon Mix 12g sachet x 20'),23,7472.82,171874.86);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (57,(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Sitara Hypermart') AND branch_name='DHA Phase 5'),'2026-08-10');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (57,(SELECT product_id FROM products WHERE name='DERMIQ Face Wash Charcoal 150ml'),10,9692.77,96927.7);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (57,(SELECT product_id FROM products WHERE name='SPARKLO Laundry Powder 1000g'),8,5660.22,45281.76);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (58,(SELECT retailer_id FROM retailers WHERE name='Minar Superstore'),NULL,'2026-07-11');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (58,(SELECT product_id FROM products WHERE name='SWEETKIN Chewing Gum 5 pcs'),37,3050.05,112851.85);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (58,(SELECT product_id FROM products WHERE name='MANGOLA Guava Drink 250ml'),12,1378.28,16539.36);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (58,(SELECT product_id FROM products WHERE name='SIPPLE Instant Lemon Mix 500g'),6,7221.57,43329.42);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (58,(SELECT product_id FROM products WHERE name='NUTHAVEN Mixed Nuts 100g'),12,9902.84,118834.08);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (59,(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Jasmine Supermart') AND branch_name='Wapda Town'),'2026-07-29');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (59,(SELECT product_id FROM products WHERE name='SOFTWAVE Fabric Softener 2500ml'),31,5126.99,158936.69);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (59,(SELECT product_id FROM products WHERE name='CRUNCHLY Potato Chips Salted 65g'),7,2418.33,16928.31);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (59,(SELECT product_id FROM products WHERE name='ZESTORA Orange Fizz 345ml can'),18,2338.33,42089.94);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (59,(SELECT product_id FROM products WHERE name='ZESTORA Lime Fizz 345ml can'),3,2212.23,6636.69);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (59,(SELECT product_id FROM products WHERE name='DERMIQ Face Wash Charcoal 150ml'),3,9419.22,28257.66);
INSERT INTO orders (order_id,retailer_id,branch_id,order_date) VALUES (60,(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart'),(SELECT branch_id FROM branches WHERE retailer_id=(SELECT retailer_id FROM retailers WHERE name='Lotus Mini Mart') AND branch_name='Valencia Town'),'2026-08-10');
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (60,(SELECT product_id FROM products WHERE name='LEAFLY Green Tea Bags 100 bags'),19,8595.65,163317.35);
INSERT INTO order_items (order_id,product_id,cartons,carton_price,line_value) VALUES (60,(SELECT product_id FROM products WHERE name='CHOCOMILL Wafer Bar 6 bar pack'),2,4961.28,9922.56);
SELECT setval(pg_get_serial_sequence('orders','order_id'),(SELECT MAX(order_id) FROM orders));
SELECT setval(pg_get_serial_sequence('order_items','item_id'),(SELECT MAX(item_id) FROM order_items));
ALTER TABLE products ENABLE TRIGGER USER; ALTER TABLE categories ENABLE TRIGGER USER; ALTER TABLE areas ENABLE TRIGGER USER;
ALTER TABLE retailers ENABLE TRIGGER USER; ALTER TABLE branches ENABLE TRIGGER USER; ALTER TABLE orders ENABLE TRIGGER USER; ALTER TABLE order_items ENABLE TRIGGER USER;
ALTER TABLE activity_log ENABLE TRIGGER trg_log_readonly;
COMMIT;
