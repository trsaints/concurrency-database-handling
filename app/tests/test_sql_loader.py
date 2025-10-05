"""
Test the SQL loader functionality to ensure external SQL files are loaded correctly.
"""

import pytest
from pathlib import Path
from app.utils.sql_loader import SQLLoader, sql_loader


class TestSQLLoader:
    """Test cases for the SQL loader utility."""

    def test_singleton_behavior(self):
        """Test that SQLLoader follows singleton pattern."""
        loader1 = SQLLoader()
        loader2 = SQLLoader()
        assert loader1 is loader2
        assert loader1 is sql_loader

    def test_load_existing_query(self):
        """Test loading an existing SQL query."""
        query = sql_loader.load_query('products', 'create')

        # Verify query content
        assert isinstance(query, str)
        assert len(query.strip()) > 0
        assert 'INSERT INTO products' in query
        assert 'VALUES' in query
        assert 'RETURNING' in query

    def test_load_all_product_queries(self):
        """Test loading all product-related queries."""
        operations = ['create', 'find_by_id',
                      'find_all', 'update', 'delete', 'count']

        for operation in operations:
            query = sql_loader.load_query('products', operation)
            assert isinstance(query, str)
            assert len(query.strip()) > 0
            print(f"✓ Loaded {operation}.sql: {len(query)} characters")

    def test_query_caching(self):
        """Test that queries are cached properly."""
        # Clear cache first
        sql_loader.clear_cache()

        # Load query twice
        query1 = sql_loader.load_query('products', 'create')
        query2 = sql_loader.load_query('products', 'create')

        # Should be identical (cached)
        assert query1 == query2

        # Check cache contains the query
        cached = sql_loader.get_cached_queries()
        assert 'products.create' in cached

    def test_list_available_queries(self):
        """Test listing available queries for products entity."""
        queries = sql_loader.list_available_queries('products')

        expected_queries = ['count', 'create', 'delete',
                            'find_all', 'find_by_id', 'update']
        assert sorted(queries) == expected_queries

    def test_list_available_entities(self):
        """Test listing available entities."""
        entities = sql_loader.list_available_entities()

        assert 'products' in entities
        assert isinstance(entities, list)

    def test_file_not_found_error(self):
        """Test error handling for non-existent SQL files."""
        with pytest.raises(FileNotFoundError) as exc_info:
            sql_loader.load_query('nonexistent', 'operation')

        assert 'SQL file not found' in str(exc_info.value)

    def test_reload_query(self):
        """Test reloading a query bypasses cache."""
        # Load and cache a query
        original_query = sql_loader.load_query('products', 'count')

        # Reload the query
        reloaded_query = sql_loader.reload_query('products', 'count')

        # Should be the same content but freshly loaded
        assert original_query == reloaded_query

    def test_clear_cache(self):
        """Test clearing the query cache."""
        # Load some queries
        sql_loader.load_query('products', 'create')
        sql_loader.load_query('products', 'find_by_id')

        # Verify cache has items
        cached_before = sql_loader.get_cached_queries()
        assert len(cached_before) > 0

        # Clear cache
        sql_loader.clear_cache()

        # Verify cache is empty
        cached_after = sql_loader.get_cached_queries()
        assert len(cached_after) == 0

    def test_sql_file_paths(self):
        """Test that SQL file paths are constructed correctly."""
        # This tests the internal path construction
        base_path = sql_loader.sql_base_path

        assert base_path.exists()
        assert (base_path / 'products').exists()
        assert (base_path / 'products' / 'create.sql').exists()
        assert (base_path / 'products' / 'find_by_id.sql').exists()

    def test_query_content_validation(self):
        """Test that loaded queries contain expected SQL patterns."""
        test_cases = [
            ('create', ['INSERT INTO products', 'VALUES', 'RETURNING']),
            ('find_by_id', ['SELECT', 'FROM products', 'WHERE id']),
            ('find_all', ['SELECT', 'FROM products', 'ORDER BY', 'LIMIT']),
            ('update', ['UPDATE products', 'SET', 'WHERE id', 'RETURNING']),
            ('delete', ['DELETE FROM products', 'WHERE id']),
            ('count', ['SELECT COUNT(*)', 'FROM products'])
        ]

        for operation, expected_patterns in test_cases:
            query = sql_loader.load_query('products', operation)

            for pattern in expected_patterns:
                assert pattern in query, f"Pattern '{pattern}' not found in {operation}.sql"

            print(f"✓ {operation}.sql contains all expected patterns")


if __name__ == "__main__":
    # Run a quick test
    test_loader = TestSQLLoader()
    test_loader.test_load_all_product_queries()
    test_loader.test_query_content_validation()
    print("All SQL loader tests passed!")
