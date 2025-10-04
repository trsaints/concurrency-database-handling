from fastapi import FastAPI
from app.routes.product_routes import router as product_router
from app.database.connection import DatabaseConnection

app = FastAPI(
    title="Concurrency Database Handling API",
    description="FastAPI application demonstrating database concurrency handling techniques",
    version="1.0.0"
)

# Include routers
app.include_router(product_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool on startup."""
    DatabaseConnection.initialize_pool()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection pool on shutdown."""
    DatabaseConnection.close_pool()


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Concurrency Database Handling API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
