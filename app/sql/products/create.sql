INSERT INTO products (name, description, price, stock_quantity)
VALUES (%s, %s, %s, %s)
RETURNING id, name, description, price, stock_quantity, version, created_at, updated_at