from fastapi import APIRouter, HTTPException, status, Query
from app.services.product_service import ProductService
from app.routes.schemas import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductListResponse
)

router = APIRouter(prefix="/api/products", tags=["products"])
product_service = ProductService()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(request: ProductCreateRequest):
    """Create a new product."""
    try:
        product = product_service.create_product(
            name=request.name,
            description=request.description,
            price=request.price,
            stock_quantity=request.stock_quantity
        )
        return product.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail=f"Error creating product: {str(e)}")


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    """Get a product by ID."""
    try:
        product = product_service.get_product(product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                              detail=f"Product with id {product_id} not found")
        return product.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Error retrieving product: {str(e)}")


@router.get("/", response_model=ProductListResponse)
def get_all_products(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """Get all products with pagination."""
    try:
        products = product_service.get_all_products(limit=limit, offset=offset)
        total = product_service.get_total_count()
        return {
            "products": [p.to_dict() for p in products],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Error retrieving products: {str(e)}")


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, request: ProductUpdateRequest):
    """Update a product with optimistic locking."""
    try:
        product = product_service.update_product(
            product_id=product_id,
            name=request.name,
            description=request.description,
            price=request.price,
            stock_quantity=request.stock_quantity,
            version=request.version
        )
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product version mismatch. The product may have been modified by another user."
            )
        return product.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Error updating product: {str(e)}")


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int):
    """Delete a product."""
    try:
        deleted = product_service.delete_product(product_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail=f"Product with id {product_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Error deleting product: {str(e)}")
