from typing import List, Optional
from app.entities.product import Product
from app.repositories.product_repository import ProductRepository


class ProductService:
    """Service layer for Product business logic."""

    def __init__(self):
        self.repository = ProductRepository()

    def create_product(self,
                       name: str,
                       description: Optional[str],
                       price: float,
                       stock_quantity: int) -> Product:
        """Create a new product."""
        if price < 0:
            raise ValueError("Price cannot be negative")

        if stock_quantity < 0:
            raise ValueError("Stock quantity cannot be negative")

        product = Product(
            name=name,
            description=description,
            price=price,
            stock_quantity=stock_quantity
        )

        return self.repository.create(product)

    def get_product(self, product_id: int) -> Optional[Product]:
        """Get a product by ID."""
        return self.repository.find_by_id(product_id)

    def get_all_products(self,
                         limit: int = 100,
                         offset: int = 0) -> List[Product]:
        """Get all products with pagination."""
        return self.repository.find_all(limit, offset)

    def update_product(self,
                       product_id: int,
                       name: str,
                       description: Optional[str],
                       price: float,
                       stock_quantity: int,
                       version: int) -> Optional[Product]:
        """Update a product."""
        if price < 0:
            raise ValueError("Price cannot be negative")
        if stock_quantity < 0:
            raise ValueError("Stock quantity cannot be negative")

        product = Product(
            id=product_id,
            name=name,
            description=description,
            price=price,
            stock_quantity=stock_quantity,
            version=version
        )
        return self.repository.update(product)

    def delete_product(self, product_id: int) -> bool:
        """Delete a product."""
        return self.repository.delete(product_id)

    def get_total_count(self) -> int:
        """Get total number of products."""
        return self.repository.count()
