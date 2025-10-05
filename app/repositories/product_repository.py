from typing import List, Optional
from app.database.connection import DatabaseConnection
from app.entities.product import Product


class ProductRepository:
    """Repository for Product entity with raw SQL queries."""

    @staticmethod
    def create(product: Product) -> Product:
        """Create a new product in the database."""
        query = """
            INSERT INTO products (name, description, price, stock_quantity)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, description, price, stock_quantity, version, created_at, updated_at
        """
        with DatabaseConnection.get_cursor(commit=True) as cursor:
            cursor.execute(query, (
                product.name,
                product.description,
                product.price,
                product.stock_quantity
            ))
            row = cursor.fetchone()
            return Product.from_db_row(row)

    @staticmethod
    def find_by_id(product_id: int) -> Optional[Product]:
        """Find a product by ID."""
        query = """
            SELECT id, name, description, price, stock_quantity, version, created_at, updated_at
            FROM products
            WHERE id = %s
        """
        with DatabaseConnection.get_cursor() as cursor:
            cursor.execute(query, (product_id,))
            row = cursor.fetchone()
            return Product.from_db_row(row) if row else None

    @staticmethod
    def find_all(limit: int = 100, offset: int = 0) -> List[Product]:
        """Find all products with pagination."""
        query = """
            SELECT id, name, description, price, stock_quantity, version, created_at, updated_at
            FROM products
            ORDER BY id
            LIMIT %s OFFSET %s
        """
        with DatabaseConnection.get_cursor() as cursor:
            cursor.execute(query, (limit, offset))
            rows = cursor.fetchall()
            return [Product.from_db_row(row) for row in rows]

    @staticmethod
    def update(product: Product) -> Optional[Product]:
        """Update a product with optimistic locking."""
        query = """
            UPDATE products
            SET name = %s, description = %s, price = %s, stock_quantity = %s, 
                version = version + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND version = %s
            RETURNING id, name, description, price, stock_quantity, version, created_at, updated_at
        """
        with DatabaseConnection.get_cursor(commit=True) as cursor:
            cursor.execute(query, (
                product.name,
                product.description,
                product.price,
                product.stock_quantity,
                product.id,
                product.version
            ))
            row = cursor.fetchone()
            return Product.from_db_row(row) if row else None

    @staticmethod
    def delete(product_id: int) -> bool:
        """Delete a product by ID."""
        query = "DELETE FROM products WHERE id = %s"
        with DatabaseConnection.get_cursor(commit=True) as cursor:
            cursor.execute(query, (product_id,))
            return cursor.rowcount > 0

    @staticmethod
    def count() -> int:
        """Count total number of products."""
        query = "SELECT COUNT(*) FROM products"
        with DatabaseConnection.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]
