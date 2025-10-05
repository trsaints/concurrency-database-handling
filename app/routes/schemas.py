from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    stock_quantity: int = Field(..., ge=0)


class ProductUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    stock_quantity: int = Field(..., ge=0)
    version: int = Field(..., ge=0)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int
    version: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    total: int
    limit: int
    offset: int
