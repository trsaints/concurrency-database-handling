from typing import List, Optional
from app.database.connection import DatabaseConnection
from app.entities.product import Product
from app.utils.sql_loader import sql_loader


class ProductRepository:
    """Repository for Product entity with raw SQL queries."""

    @staticmethod
    def create(product: Product) -> Product:
        """Create a new product in the database."""
        query = sql_loader.load_query('products', 'create')
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
        query = sql_loader.load_query('products', 'find_by_id')
        with DatabaseConnection.get_cursor() as cursor:
            cursor.execute(query, (product_id,))
            row = cursor.fetchone()
            return Product.from_db_row(row) if row else None

    @staticmethod
    def find_all(limit: int = 100, offset: int = 0) -> List[Product]:
        """Find all products with pagination."""
        query = sql_loader.load_query('products', 'find_all')
        with DatabaseConnection.get_cursor() as cursor:
            cursor.execute(query, (limit, offset))
            rows = cursor.fetchall()
            return [Product.from_db_row(row) for row in rows]

    @staticmethod
    def update(product: Product) -> Optional[Product]:
        """Update a product with optimistic locking."""
        query = sql_loader.load_query('products', 'update')
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
        query = sql_loader.load_query('products', 'delete')
        with DatabaseConnection.get_cursor(commit=True) as cursor:
            cursor.execute(query, (product_id,))
            return cursor.rowcount > 0

    @staticmethod
    def count() -> int:
        """Count total number of products."""
        query = sql_loader.load_query('products', 'count')
        with DatabaseConnection.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]
