import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Generator
from app.config.settings import settings


class DatabaseConnection:
    _connection_pool = None
    
    @classmethod
    def initialize_pool(cls, minconn: int = 1, maxconn: int = 10):
        """Initialize the connection pool."""
        if cls._connection_pool is None:
            cls._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn,
                maxconn,
                host=settings.database_host,
                port=settings.database_port,
                database=settings.database_name,
                user=settings.database_user,
                password=settings.database_password
            )
    
    @classmethod
    def close_pool(cls):
        """Close all connections in the pool."""
        if cls._connection_pool is not None:
            cls._connection_pool.closeall()
            cls._connection_pool = None
    
    @classmethod
    @contextmanager
    def get_connection(cls) -> Generator:
        """Get a connection from the pool."""
        if cls._connection_pool is None:
            cls.initialize_pool()
        
        connection = cls._connection_pool.getconn()
        try:
            yield connection
        finally:
            cls._connection_pool.putconn(connection)
    
    @classmethod
    @contextmanager
    def get_cursor(cls, commit: bool = False) -> Generator:
        """Get a cursor from a pooled connection."""
        with cls.get_connection() as connection:
            cursor = connection.cursor()
            try:
                yield cursor
                if commit:
                    connection.commit()
            except Exception as e:
                connection.rollback()
                raise e
            finally:
                cursor.close()


# Initialize the connection pool on module import
DatabaseConnection.initialize_pool()
