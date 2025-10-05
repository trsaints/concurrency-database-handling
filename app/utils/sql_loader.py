"""
SQL Query Loader Utility

This module provides a utility for loading SQL queries from external .sql files.
It supports caching to avoid repeated file I/O operations and provides a clean
interface for managing SQL queries in a structured manner.
"""

import os
from pathlib import Path
from typing import Dict, Optional
from functools import lru_cache


class SQLLoader:
    """
    A utility class for loading and caching SQL queries from external files.

    This class provides a centralized way to manage SQL queries by loading them
    from .sql files in a structured directory hierarchy. It includes caching
    to improve performance by avoiding repeated file reads.
    """

    _instance: Optional['SQLLoader'] = None
    _sql_cache: Dict[str, str] = {}

    def __new__(cls) -> 'SQLLoader':
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the SQL loader with the base SQL directory path."""
        if not hasattr(self, 'initialized'):
            # Navigate from utils/ to app/ to sql/
            self.sql_base_path = Path(__file__).parent.parent / 'sql'
            self.initialized = True

    @lru_cache(maxsize=128)
    def load_query(self, entity: str, operation: str) -> str:
        """
        Load a SQL query from a file.

        Args:
            entity (str): The entity name (e.g., 'products', 'users')
            operation (str): The operation name (e.g., 'create', 'find_by_id', 'update')

        Returns:
            str: The SQL query content

        Raises:
            FileNotFoundError: If the SQL file doesn't exist
            IOError: If there's an error reading the file

        Example:
            loader = SQLLoader()
            query = loader.load_query('products', 'create')
        """
        # Create cache key
        cache_key = f"{entity}.{operation}"

        # Check if query is already cached
        if cache_key in self._sql_cache:
            return self._sql_cache[cache_key]

        # Construct file path
        sql_file_path = self.sql_base_path / entity / f"{operation}.sql"

        # Check if file exists
        if not sql_file_path.exists():
            raise FileNotFoundError(
                f"SQL file not found: {sql_file_path}. "
                f"Expected file for entity '{entity}' and operation '{operation}'"
            )

        try:
            # Read and cache the query
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                query_content = file.read().strip()
                self._sql_cache[cache_key] = query_content
                return query_content

        except IOError as e:
            raise IOError(f"Error reading SQL file {sql_file_path}: {e}")

    def reload_query(self, entity: str, operation: str) -> str:
        """
        Force reload a query from file, bypassing cache.

        Args:
            entity (str): The entity name
            operation (str): The operation name

        Returns:
            str: The SQL query content
        """
        cache_key = f"{entity}.{operation}"

        # Remove from cache if it exists
        if cache_key in self._sql_cache:
            del self._sql_cache[cache_key]

        # Clear the lru_cache for this specific query
        self.load_query.cache_clear()

        # Load fresh from file
        return self.load_query(entity, operation)

    def clear_cache(self) -> None:
        """Clear all cached queries."""
        self._sql_cache.clear()
        self.load_query.cache_clear()

    def get_cached_queries(self) -> Dict[str, str]:
        """
        Get a copy of all currently cached queries.

        Returns:
            Dict[str, str]: A dictionary of cached queries
        """
        return self._sql_cache.copy()

    def list_available_queries(self, entity: str) -> list:
        """
        List all available query operations for a given entity.

        Args:
            entity (str): The entity name

        Returns:
            list: List of available operation names
        """
        entity_path = self.sql_base_path / entity

        if not entity_path.exists() or not entity_path.is_dir():
            return []

        # Get all .sql files in the entity directory
        sql_files = [f.stem for f in entity_path.glob("*.sql")]
        return sorted(sql_files)

    def list_available_entities(self) -> list:
        """
        List all available entities (directories) in the SQL base path.

        Returns:
            list: List of available entity names
        """
        if not self.sql_base_path.exists():
            return []

        # Get all directories in the SQL base path
        entities = [d.name for d in self.sql_base_path.iterdir() if d.is_dir()]
        return sorted(entities)


# Global instance for easy access
sql_loader = SQLLoader()
