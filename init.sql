-- Create products table with optimistic locking support
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on name for faster lookups
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

-- Insert sample data
INSERT INTO products (name, description, price, stock_quantity) VALUES
    ('Laptop', 'High-performance laptop for developers', 1299.99, 50),
    ('Wireless Mouse', 'Ergonomic wireless mouse', 29.99, 150),
    ('Mechanical Keyboard', 'RGB mechanical keyboard', 89.99, 75),
    ('USB-C Hub', 'Multi-port USB-C hub', 49.99, 100),
    ('Monitor', '27-inch 4K monitor', 399.99, 30)
ON CONFLICT DO NOTHING;
