"""
Clean concurrency tests with minimal, readable output.

These tests focus on validating concurrency behavior with clear assertions
and minimal console output for better readability.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest
from app.entities.product import Product
from app.repositories.product_repository import ProductRepository


class TestConcurrencyPatterns:
    """Test specific concurrency patterns with clean, focused output."""

    @pytest.fixture
    def test_product(self):
        """Create a test product for each test."""
        product = Product(
            name="Concurrency Test Product",
            description="Test product for concurrency scenarios",
            price=100.0,
            stock_quantity=1000
        )
        created_product = ProductRepository.create(product)
        yield created_product

        # Cleanup
        if created_product and created_product.id:
            ProductRepository.delete(created_product.id)

    def test_lost_update_prevention(self, test_product: Product):
        """
        Test optimistic locking prevents lost updates when multiple users edit the same record.

        Expected: Only one of two concurrent updates should succeed.
        """
        assert test_product.id is not None, "Test product should have an ID"
        product_id = test_product.id
        results = {"success": [], "failures": []}

        def simulate_user_update(user_name: str, price_change: float):
            """Simulate a user updating the product."""
            try:
                # Read current product
                product = ProductRepository.find_by_id(product_id)
                assert product is not None, f"Product {product_id} should exist"

                original_version = product.version

                # Simulate processing time
                time.sleep(0.1)

                # Update product
                product.price += price_change
                product.description = f"Updated by {user_name}"

                updated_product = ProductRepository.update(product)

                if updated_product:
                    results["success"].append({
                        "user": user_name,
                        "original_version": original_version,
                        "new_version": updated_product.version
                    })
                else:
                    results["failures"].append({
                        "user": user_name,
                        "reason": "Version conflict"
                    })

            except Exception as e:
                results["failures"].append({
                    "user": user_name,
                    "error": str(e)
                })

        # Start two concurrent updates
        thread1 = threading.Thread(
            target=simulate_user_update, args=("Alice", 10.0))
        thread2 = threading.Thread(
            target=simulate_user_update, args=("Bob", 20.0))

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # Validate results
        successful_updates = len(results["success"])
        failed_updates = len(results["failures"])

        assert successful_updates == 1, f"Expected 1 successful update, got {successful_updates}"
        assert failed_updates == 1, f"Expected 1 failed update, got {failed_updates}"

        # Verify version increment
        final_product = ProductRepository.find_by_id(product_id)
        assert final_product is not None, "Product should still exist"
        assert final_product.version == test_product.version + \
            1, "Version should increment by 1"

    def test_stock_depletion_race_condition(self, test_product: Product):
        """
        Test that race conditions in stock management don't cause overselling.

        Expected: Stock should never go negative, even with concurrent purchases.
        """
        assert test_product.id is not None, "Test product should have an ID"

        # Set low stock to trigger race condition
        test_product.stock_quantity = 3
        updated_product = ProductRepository.update(test_product)

        assert updated_product is not None, "Stock update should succeed"

        product_id = test_product.id
        purchase_results = []

        def attempt_purchase(customer_id: int):
            """Simulate a customer purchase attempt."""
            try:
                product = ProductRepository.find_by_id(product_id)
                assert product is not None, f"Product {product_id} should exist"

                if product.stock_quantity > 0:
                    # Simulate decision time
                    time.sleep(0.05)

                    # Attempt purchase
                    product.stock_quantity -= 1
                    updated = ProductRepository.update(product)

                    if updated:
                        purchase_results.append(
                            {"customer": customer_id, "success": True})
                    else:
                        purchase_results.append(
                            {"customer": customer_id, "success": False, "reason": "conflict"})
                else:
                    purchase_results.append(
                        {"customer": customer_id, "success": False, "reason": "out_of_stock"})

            except Exception as e:
                purchase_results.append(
                    {"customer": customer_id, "success": False, "error": str(e)})

        # 5 customers try to buy 3 items
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(attempt_purchase, i) for i in range(5)]
            for future in as_completed(futures):
                future.result()

        # Validate no overselling occurred
        successful_purchases = [p for p in purchase_results if p["success"]]

        final_product = ProductRepository.find_by_id(product_id)

        assert final_product is not None, "Product should still exist"

        assert final_product.stock_quantity >= 0, "Stock should never be negative"

        assert len(
            successful_purchases) <= 3, "Cannot sell more than available stock"

        assert final_product.stock_quantity == 3 - \
            len(successful_purchases), "Stock math should be correct"

    def test_high_concurrency_operations(self, test_product: Product):
        """
        Test system stability under high concurrency load.

        Expected: Most operations should succeed, system should remain stable.
        """
        assert test_product.id is not None, "Test product should have an ID"

        product_id = test_product.id

        operation_results = []

        def perform_operations(thread_id: int):
            """Perform mixed read/write operations."""
            for i in range(5):
                try:
                    if i % 2 == 0:
                        # Read operation
                        product = ProductRepository.find_by_id(product_id)

                        if product:
                            operation_results.append(
                                f"read_success_{thread_id}_{i}")
                    else:
                        # Write operation
                        product = ProductRepository.find_by_id(product_id)

                        if product:
                            product.price += 0.01
                            updated = ProductRepository.update(product)

                            if updated:
                                operation_results.append(
                                    f"write_success_{thread_id}_{i}")
                except Exception:
                    operation_results.append(f"error_{thread_id}_{i}")

                time.sleep(0.001)  # Small delay

        # Run 10 threads with 5 operations each
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(perform_operations, i)
                       for i in range(10)]

            for future in as_completed(futures):
                future.result()

        # Validate system stability
        total_operations = 50  # 10 threads * 5 operations
        successful_operations = len(
            [r for r in operation_results if "success" in r])
        error_operations = len([r for r in operation_results if "error" in r])

        success_rate = successful_operations / total_operations

        assert success_rate >= 0.6, f"Success rate too low: {success_rate:.2f}"

        assert error_operations < total_operations * \
            0.1, f"Too many errors: {error_operations}"

    def test_optimistic_locking_retry_pattern(self, test_product: Product):
        """
        Test retry pattern for handling optimistic locking conflicts.

        Expected: Most threads should succeed with retries.
        """
        assert test_product.id is not None, "Test product should have an ID"
        product_id = test_product.id
        results = []

        def update_with_retry(thread_id: int, max_retries: int = 3):
            """Update with retry logic."""
            for attempt in range(max_retries):
                try:
                    product = ProductRepository.find_by_id(product_id)
                    assert product is not None, f"Product {product_id} should exist"

                    # Simulate processing
                    time.sleep(0.02)

                    # Attempt update
                    product.price += 0.1
                    updated = ProductRepository.update(product)

                    if updated:
                        results.append(
                            {"thread": thread_id, "attempt": attempt, "success": True})

                        return

                    else:
                        # Retry with backoff
                        time.sleep(0.01 * (attempt + 1))

                except Exception as e:
                    results.append(
                        {"thread": thread_id, "error": str(e), "success": False})
                    return

            # All retries exhausted
            results.append(
                {"thread": thread_id, "max_retries_exceeded": True, "success": False})

        # 6 threads competing for updates
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(update_with_retry, i) for i in range(6)]

            for future in as_completed(futures):
                future.result()

        # Validate retry effectiveness
        successful_updates = [r for r in results if r.get("success")]

        # Most should succeed with retries
        assert len(
            successful_updates) >= 3, f"Expected at least 3 successes, got {len(successful_updates)}"

        # Verify final state
        final_product = ProductRepository.find_by_id(product_id)

        assert final_product is not None, "Product should still exist"

        expected_version = test_product.version + len(successful_updates)

        assert final_product.version == expected_version, f"Version should be {expected_version}, got {final_product.version}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
