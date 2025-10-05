UPDATE products
SET name = %s, description = %s, price = %s, stock_quantity = %s, 
    version = version + 1, updated_at = CURRENT_TIMESTAMP
WHERE id = %s AND version = %s
RETURNING id, name, description, price, stock_quantity, version, created_at, updated_at