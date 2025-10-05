SELECT id, name, description, price, stock_quantity, version, created_at, updated_at
FROM products
ORDER BY id
LIMIT %s OFFSET %s