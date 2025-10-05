SELECT id, name, description, price, stock_quantity, version, created_at, updated_at
FROM products
WHERE id = %s