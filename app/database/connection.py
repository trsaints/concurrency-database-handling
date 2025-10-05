from contextlib import contextmanager
from typing import Generator, Optional
from app.config.settings import settings
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extensions import connection as pg_connection, cursor as pg_cursor


class DatabaseConnection:
    _connection_pool: Optional[ThreadedConnectionPool] = None
    _pool_initialized: bool = False

    @classmethod
    def initialize_pool(cls, minconn: int = 1, maxconn: int = 10):
        """Initialize the connection pool."""
        if not cls._pool_initialized:
            cls._connection_pool = ThreadedConnectionPool(
                minconn,
                maxconn,
                host=settings.database_host,
                port=settings.database_port,
                database=settings.database_name,
                user=settings.database_user,
                password=settings.database_password
            )
            cls._pool_initialized = True

    @classmethod
    def close_pool(cls):
        """Close all connections in the pool."""
        if cls._connection_pool:
            cls._connection_pool.closeall()
            cls._connection_pool = None
            cls._pool_initialized = False

    @classmethod
    @contextmanager
    def get_connection(cls) -> Generator[pg_connection, None, None]:
        """Get a connection from the pool."""
        if not cls._pool_initialized:
            cls.initialize_pool()

        if cls._connection_pool is None:
            raise RuntimeError("Connection pool is not initialized")

        connection = cls._connection_pool.getconn()

        try:
            yield connection

        finally:
            if cls._connection_pool is not None:
                cls._connection_pool.putconn(connection)

    @classmethod
    @contextmanager
    def get_cursor(cls, commit: bool = False) -> Generator[pg_cursor, None, None]:
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
