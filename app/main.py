from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes.product_routes import router as product_router
from app.database.connection import DatabaseConnection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database connection handling."""
    # Initialize database connection pool on startup
    DatabaseConnection.initialize_pool()
    yield
    # Close database connection pool on shutdown
    DatabaseConnection.close_pool()


app = FastAPI(
    title="Concurrency Database Handling API",
    description="FastAPI application demonstrating database concurrency handling techniques",
    version="0.1.0",
    lifespan=lifespan
)

# Include routers
app.include_router(product_router)


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
