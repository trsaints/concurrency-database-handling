"""
Comprehensive tests for database concurrency handling.

This module contains tests for various concurrency scenarios:
1. Optimistic locking conflicts
2. Race conditions in stock updates
3. Concurrent read/write operations
4. Deadlock scenarios
5. Connection pool stress testing
"""

import asyncio
import concurrent.futures
import threading
import time
from typing import List, Tuple
import pytest
from app.entities.product import Product
from app.repositories.product_repository import ProductRepository
from app.database.connection import DatabaseConnection


class TestDatabaseConcurrency:
    """Test suite for database concurrency scenarios."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and cleanup for each test."""
        # Setup: Create test product
        test_product = Product(
            name="Test Concurrency Product",
            description="Product for testing concurrency",
            price=100.0,
            stock_quantity=1000
        )
        self.test_product = ProductRepository.create(test_product)

        yield

        # Cleanup: Remove test product
        if self.test_product and self.test_product.id:
            ProductRepository.delete(self.test_product.id)

    def test_optimistic_locking_conflict(self):
        """
        Test that optimistic locking prevents lost updates.

        Scenario:
        1. Two threads read the same product
        2. Both try to update it simultaneously
        3. Only one should succeed, the other should fail
        """
        product_id = self.test_product.id
        results = []
        exceptions = []

        def update_product(new_name: str, delay: float = 0):
            """Update product with optional delay to simulate processing time."""
            try:
                if delay:
                    time.sleep(delay)

                # Read current product
                product = ProductRepository.find_by_id(product_id)
                assert product is not None

                # Simulate some processing time
                time.sleep(0.1)

                # Update product
                product.name = new_name
                product.price += 10.0

                updated_product = ProductRepository.update(product)
                results.append(updated_product)

            except Exception as e:
                exceptions.append(e)

        # Start two threads that will compete for the same product update
        thread1 = threading.Thread(
            target=update_product, args=("Updated by Thread 1",))
        thread2 = threading.Thread(
            target=update_product, args=("Updated by Thread 2",))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # One update should succeed, one should fail due to version mismatch
        successful_updates = [r for r in results if r is not None]
        failed_updates = [r for r in results if r is None]

        assert len(
            successful_updates) == 1, f"Expected 1 successful update, got {len(successful_updates)}"
        assert len(
            failed_updates) == 1, f"Expected 1 failed update, got {len(failed_updates)}"

        # Verify the successful update increased the version
        final_product = ProductRepository.find_by_id(product_id)
        assert final_product.version == self.test_product.version + 1

    def test_concurrent_stock_updates_race_condition(self):
        """
        Test race condition when multiple threads update stock simultaneously.

        This test demonstrates the need for atomic operations or proper locking
        when updating stock quantities.
        """
        product_id = self.test_product.id
        initial_stock = self.test_product.stock_quantity
        stock_decrease = 10
        num_threads = 5

        results = []

        def decrease_stock():
            """Decrease stock by a fixed amount."""
            try:
                # Read current product
                product = ProductRepository.find_by_id(product_id)

                # Simulate some processing time
                time.sleep(0.05)

                # Decrease stock
                product.stock_quantity -= stock_decrease

                # Update product
                updated_product = ProductRepository.update(product)
                results.append(updated_product)

            except Exception as e:
                results.append(None)

        # Start multiple threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=decrease_stock)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        successful_updates = [r for r in results if r is not None]
        failed_updates = [r for r in results if r is None]

        print(f"Successful updates: {len(successful_updates)}")
        print(f"Failed updates: {len(failed_updates)}")

        # Due to optimistic locking, only one update should succeed at a time
        # The exact number of successful updates depends on timing
        assert len(successful_updates) >= 1
        assert len(failed_updates) >= 1

        # Verify final stock is consistent
        final_product = ProductRepository.find_by_id(product_id)
        expected_final_stock = initial_stock - \
            (len(successful_updates) * stock_decrease)

        assert final_product.stock_quantity == expected_final_stock

    def test_concurrent_read_write_operations(self):
        """
        Test mixing concurrent read and write operations.

        This test verifies that reads can happen concurrently with writes
        and that the system remains consistent.
        """
        product_id = self.test_product.id
        num_readers = 10
        num_writers = 3
        read_results = []
        write_results = []

        def read_product():
            """Read product multiple times."""
            for _ in range(5):
                product = ProductRepository.find_by_id(product_id)
                read_results.append(product)
                time.sleep(0.01)

        def write_product(thread_id: int):
            """Update product price."""
            try:
                product = ProductRepository.find_by_id(product_id)
                product.price += thread_id * 1.0
                updated_product = ProductRepository.update(product)
                write_results.append(updated_product)
                time.sleep(0.02)
            except Exception:
                write_results.append(None)

        # Start reader threads
        reader_threads = []
        for _ in range(num_readers):
            thread = threading.Thread(target=read_product)
            reader_threads.append(thread)
            thread.start()

        # Start writer threads
        writer_threads = []
        for i in range(num_writers):
            thread = threading.Thread(target=write_product, args=(i + 1,))
            writer_threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in reader_threads + writer_threads:
            thread.join()

        # Verify results
        assert len(read_results) == num_readers * 5
        assert all(r is not None for r in read_results)

        successful_writes = [w for w in write_results if w is not None]
        assert len(successful_writes) >= 1

        # All read results should be valid Product instances
        for product in read_results:
            assert isinstance(product, Product)
            assert product.id == product_id

    def test_connection_pool_stress(self):
        """
        Test connection pool under stress with many concurrent operations.

        This test verifies that the connection pool can handle many
        concurrent database operations without exhausting connections.
        """
        num_threads = 20
        operations_per_thread = 5
        results = []

        def perform_database_operations(thread_id: int):
            """Perform multiple database operations."""
            thread_results = []
            try:
                for i in range(operations_per_thread):
                    # Mix of read and write operations
                    if i % 2 == 0:
                        # Read operation
                        product = ProductRepository.find_by_id(
                            self.test_product.id)
                        thread_results.append(f"Read-{thread_id}-{i}")
                    else:
                        # Write operation (create and delete)
                        temp_product = Product(
                            name=f"Temp Product {thread_id}-{i}",
                            price=10.0,
                            stock_quantity=1
                        )
                        created = ProductRepository.create(temp_product)
                        if created:
                            ProductRepository.delete(created.id)
                            thread_results.append(f"Write-{thread_id}-{i}")

                    # Small delay to avoid overwhelming
                    time.sleep(0.001)

            except Exception as e:
                thread_results.append(f"Error-{thread_id}: {str(e)}")

            results.extend(thread_results)

        # Start many threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(
                target=perform_database_operations, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify results
        expected_operations = num_threads * operations_per_thread
        successful_operations = [
            r for r in results if not r.startswith("Error")]

        print(f"Total operations attempted: {expected_operations}")
        print(f"Successful operations: {len(successful_operations)}")
        print(
            f"Failed operations: {len(results) - len(successful_operations)}")

        # Most operations should succeed
        success_rate = len(successful_operations) / expected_operations
        assert success_rate > 0.8, f"Success rate too low: {success_rate}"

    def test_async_concurrent_operations(self):
        """
        Test concurrent operations using asyncio and thread pools.

        This demonstrates how to test concurrent database operations
        in an async context, which is more realistic for FastAPI applications.
        """
        async def async_test():
            loop = asyncio.get_event_loop()
            product_id = self.test_product.id

            # Define sync operations to run in thread pool
            def read_operation():
                return ProductRepository.find_by_id(product_id)

            def write_operation(price_increase: float):
                try:
                    product = ProductRepository.find_by_id(product_id)
                    product.price += price_increase
                    return ProductRepository.update(product)
                except Exception:
                    return None

            # Run concurrent operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Schedule multiple read operations
                read_futures = [
                    loop.run_in_executor(executor, read_operation)
                    for _ in range(10)
                ]

                # Schedule multiple write operations
                write_futures = [
                    loop.run_in_executor(executor, write_operation, i * 0.1)
                    for i in range(5)
                ]

                # Wait for all operations to complete
                read_results = await asyncio.gather(*read_futures)
                write_results = await asyncio.gather(*write_futures)

            # Verify results
            assert all(r is not None for r in read_results)
            successful_writes = [w for w in write_results if w is not None]
            assert len(successful_writes) >= 1

            return len(read_results), len(successful_writes)

        # Run the async test
        read_count, write_count = asyncio.run(async_test())
        assert read_count == 10
        assert write_count >= 1

    def test_deadlock_scenario(self):
        """
        Test potential deadlock scenarios with multiple resource access.

        This test creates a scenario where deadlocks could occur if not
        properly handled by the database or connection management.
        """
        # Create a second test product
        second_product = Product(
            name="Second Test Product",
            description="Another test product",
            price=50.0,
            stock_quantity=500
        )
        second_product = ProductRepository.create(second_product)

        try:
            results = []

            def update_products_order_1():
                """Update products in order: first -> second."""
                try:
                    # Update first product
                    product1 = ProductRepository.find_by_id(
                        self.test_product.id)
                    product1.price += 1.0
                    time.sleep(0.1)  # Hold the lock longer
                    updated1 = ProductRepository.update(product1)

                    # Update second product
                    product2 = ProductRepository.find_by_id(second_product.id)
                    product2.price += 1.0
                    updated2 = ProductRepository.update(product2)

                    results.append(
                        ("order1", updated1 is not None, updated2 is not None))
                except Exception as e:
                    results.append(("order1", False, False, str(e)))

            def update_products_order_2():
                """Update products in order: second -> first."""
                try:
                    # Update second product
                    product2 = ProductRepository.find_by_id(second_product.id)
                    product2.price += 1.0
                    time.sleep(0.1)  # Hold the lock longer
                    updated2 = ProductRepository.update(product2)

                    # Update first product
                    product1 = ProductRepository.find_by_id(
                        self.test_product.id)
                    product1.price += 1.0
                    updated1 = ProductRepository.update(product1)

                    results.append(
                        ("order2", updated1 is not None, updated2 is not None))
                except Exception as e:
                    results.append(("order2", False, False, str(e)))

            # Start threads that could potentially deadlock
            thread1 = threading.Thread(target=update_products_order_1)
            thread2 = threading.Thread(target=update_products_order_2)

            thread1.start()
            thread2.start()

            thread1.join(timeout=5.0)  # Timeout to prevent hanging
            thread2.join(timeout=5.0)

            # Analyze results
            print(f"Deadlock test results: {results}")

            # At least one thread should complete successfully
            # The behavior depends on the database's deadlock detection
            assert len(results) >= 1

        finally:
            # Cleanup second product
            if second_product and second_product.id:
                ProductRepository.delete(second_product.id)

    def test_version_increment_consistency(self):
        """
        Test that version numbers are incremented consistently under concurrency.

        This verifies that the optimistic locking mechanism works correctly
        and version numbers are always incremented properly.
        """
        product_id = self.test_product.id
        initial_version = self.test_product.version
        num_updates = 10
        successful_updates = []

        def attempt_update(update_id: int):
            """Attempt to update the product."""
            for attempt in range(5):  # Retry up to 5 times
                try:
                    product = ProductRepository.find_by_id(product_id)
                    product.description = f"Updated by update {update_id}, attempt {attempt}"
                    updated = ProductRepository.update(product)

                    if updated:
                        successful_updates.append((update_id, updated.version))
                        break

                    # If update failed (returned None), wait and retry
                    time.sleep(0.01)

                except Exception as e:
                    print(f"Update {update_id}, attempt {attempt} failed: {e}")
                    time.sleep(0.01)

        # Start multiple update threads
        threads = []
        for i in range(num_updates):
            thread = threading.Thread(target=attempt_update, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify version consistency
        successful_updates.sort(key=lambda x: x[1])  # Sort by version

        print(f"Successful updates: {len(successful_updates)}")
        for update_id, version in successful_updates:
            print(f"Update {update_id}: version {version}")

        # Check that versions are sequential
        for i, (update_id, version) in enumerate(successful_updates):
            expected_version = initial_version + i + 1
            assert version == expected_version, f"Version mismatch: expected {expected_version}, got {version}"

        # Verify final state
        final_product = ProductRepository.find_by_id(product_id)
        expected_final_version = initial_version + len(successful_updates)
        assert final_product.version == expected_final_version

    def test_transaction_isolation(self):
        """
        Test transaction isolation by verifying that uncommitted changes
        are not visible to other transactions.

        Note: This test demonstrates transaction boundaries in the context
        of the current connection management system.
        """
        product_id = self.test_product.id
        original_price = self.test_product.price

        # This test demonstrates the importance of proper transaction handling
        # In the current implementation, each repository operation is auto-committed

        def read_during_update():
            """Read product while another thread is updating it."""
            time.sleep(0.05)  # Wait for update to start
            product = ProductRepository.find_by_id(product_id)
            return product.price

        def update_with_delay():
            """Update product with artificial delay."""
            product = ProductRepository.find_by_id(product_id)
            time.sleep(0.1)  # Simulate processing time
            product.price += 100.0
            return ProductRepository.update(product)

        # Start update thread
        update_thread = threading.Thread(target=update_with_delay)

        # Start read thread
        read_thread = threading.Thread(target=read_during_update)

        read_results = []

        def capture_read_result():
            result = read_during_update()
            read_results.append(result)

        read_thread = threading.Thread(target=capture_read_result)

        update_thread.start()
        read_thread.start()

        update_thread.join()
        read_thread.join()

        # Verify that the read operation saw a consistent state
        # The exact behavior depends on transaction isolation level
        assert len(read_results) == 1
        read_price = read_results[0]

        # The read should see either the original price or the updated price
        # but not an intermediate state
        final_product = ProductRepository.find_by_id(product_id)
        assert read_price in [original_price, final_product.price]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
