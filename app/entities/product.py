from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Product:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    price: float = 0.0
    stock_quantity: int = 0
    version: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> "Product":
        """Create a Product instance from a database row."""
        if row is None:
            return None
        return cls(
            id=row[0],
            name=row[1],
            description=row[2],
            price=float(row[3]),
            stock_quantity=row[4],
            version=row[5],
            created_at=row[6],
            updated_at=row[7]
        )

    def to_dict(self) -> dict:
        """Convert Product to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
