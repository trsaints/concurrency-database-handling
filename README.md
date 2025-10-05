# Concurrency Database Handling

A Python/FastAPI application demonstrating database concurrency handling techniques with raw SQL queries, custom entity mapping, and CRUD operations.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **Raw SQL Queries**: Direct database interaction without ORM
- **Custom Entity Mapping**: Manual mapping of query results to entity classes
- **Layered Architecture**: Clean separation of concerns (entities, repositories, services, routes)
- **Connection Pooling**: Efficient database connection management
- **Optimistic Locking**: Concurrency control using versioning
- **Docker Support**: Containerized application and database
- **CRUD Operations**: Complete Create, Read, Update, Delete endpoints

## Project Structure

```
concurrency-database-handling/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py       # Database connection pooling
│   ├── entities/
│   │   ├── __init__.py
│   │   └── product.py          # Product entity class
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── product_repository.py  # Raw SQL queries
│   ├── services/
│   │   ├── __init__.py
│   │   └── product_service.py  # Business logic
│   └── routes/
│       ├── __init__.py
│       ├── schemas.py          # Pydantic models
│       └── product_routes.py   # API endpoints
├── docker-compose.yml          # Docker compose configuration
├── Dockerfile                  # Application container
├── init.sql                    # Database initialization
├── requirements.txt            # Python dependencies
└── .env.example               # Environment variables template
```

## Prerequisites

- Docker and Docker Compose (for containerized setup)
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local development)

## Getting Started

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/trsaints/concurrency-database-handling.git
cd concurrency-database-handling
```

2. Create and activate the virtual environment (venv):
    - Windows:
```ps1
py -m venv .venv
source .venv/bin/Activate.ps1
```
    - Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Start the services:
```bash
docker-compose up -d
```

4. The API will be available at:
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

5. Stop the services:
```bash
docker-compose down
```

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Ensure PostgreSQL is running and create the database:
```bash
psql -U postgres -c "CREATE DATABASE concurrency_db;"
psql -U postgres -d concurrency_db -f init.sql
```

5. Run the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Products

- **POST /api/products/** - Create a new product
  ```json
  {
    "name": "Product Name",
    "description": "Product Description",
    "price": 99.99,
    "stock_quantity": 100
  }
  ```

- **GET /api/products/** - Get all products (with pagination)
  - Query params: `limit` (default: 100), `offset` (default: 0)

- **GET /api/products/{id}** - Get a specific product

- **PUT /api/products/{id}** - Update a product (with optimistic locking)
  ```json
  {
    "name": "Updated Name",
    "description": "Updated Description",
    "price": 89.99,
    "stock_quantity": 150,
    "version": 0
  }
  ```

- **DELETE /api/products/{id}** - Delete a product

### Health Check

- **GET /health** - Check API health status

## Concurrency Handling

This application demonstrates optimistic locking for concurrency control:

1. Each product has a `version` field
2. On update, the version is checked
3. If the version doesn't match, the update fails with a 409 Conflict
4. This prevents lost updates in concurrent scenarios

## Database Schema

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Architecture Layers

### 1. Entities
Data classes representing database records with custom mapping methods.

### 2. Repositories
Database access layer with raw SQL queries and manual result mapping.

### 3. Services
Business logic layer with validation and data transformation.

### 4. Routes (Controllers)
HTTP request handlers using FastAPI's routing system.

## Testing the API

Using curl:

```bash
# Create a product
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "description": "A test product", "price": 49.99, "stock_quantity": 10}'

# Get all products
curl http://localhost:8000/api/products/

# Get a specific product
curl http://localhost:8000/api/products/1

# Update a product
curl -X PUT http://localhost:8000/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Product", "description": "Updated", "price": 59.99, "stock_quantity": 20, "version": 0}'

# Delete a product
curl -X DELETE http://localhost:8000/api/products/1
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
