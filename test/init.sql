DELETE
FROM order_line
WHERE TRUE;
DELETE
FROM "order"
WHERE TRUE;
DELETE
FROM product
WHERE TRUE;


INSERT INTO "order" (id, is_active, create_date, update_date, order_no)
VALUES (1, TRUE, now(), now(), '123');


INSERT INTO product (id, is_active, create_date, update_date, product_name, sku_name, standard_price)
VALUES (1, TRUE, now(), now(), 'test', 'test', 10);


INSERT INTO order_line (id, is_active, create_date, update_date, order_id, product_id, price, quantities)
VALUES (1, TRUE, now(), now(), 1, 1, 1, 1);