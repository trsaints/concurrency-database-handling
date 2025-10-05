"""
Focused concurrency tests demonstrating specific patterns.

These tests are designed to clearly show different concurrency handling
techniques and their effects.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest
from app.entities.product import Product
from app.repositories.product_repository import ProductRepository


class TestConcurrencyPatterns:
    """Test specific concurrency patterns with clear demonstrations."""

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
        Demonstrate how optimistic locking prevents lost updates.

        The Lost Update Problem:
        1. Transaction A reads a record
        2. Transaction B reads the same record
        3. Transaction A modifies and commits
        4. Transaction B modifies and commits (overwrites A's changes)

        Our solution uses versioning to prevent this.
        """
        product_id = test_product.id
        results = {"success": [], "failures": []}

        def simulate_user_update(user_name: str, price_change: float):
            """Simulate a user updating the product."""
            try:
                # Step 1: User loads the product page (read current state)
                product = ProductRepository.find_by_id(product_id)
                original_version = product.version

                # Step 2: User thinks about the change (simulate time)
                time.sleep(0.1)

                # Step 3: User submits the form (attempt update)
                product.price += price_change
                product.description = f"Updated by {user_name}"

                updated_product = ProductRepository.update(product)

                if updated_product:
                    results["success"].append({
                        "user": user_name,
                        "original_version": original_version,
                        "new_version": updated_product.version,
                        "price": updated_product.price
                    })
                else:
                    results["failures"].append({
                        "user": user_name,
                        "original_version": original_version,
                        "reason": "Version conflict"
                    })

            except Exception as e:
                results["failures"].append({
                    "user": user_name,
                    "error": str(e)
                })

        # Simulate two users trying to update the same product simultaneously
        thread1 = threading.Thread(
            target=simulate_user_update, args=("Alice", 10.0))
        thread2 = threading.Thread(
            target=simulate_user_update, args=("Bob", 20.0))

        # Start both threads at nearly the same time
        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Verify results - clean output focused on test validation
        successful_updates = len(results["success"])
        failed_updates = len(results["failures"])

        # Assertions with informative error messages
        assert successful_updates == 1, f"Expected 1 successful update, got {successful_updates}"
        assert failed_updates == 1, f"Expected 1 failed update, got {failed_updates}"

        # Verify the version was incremented correctly
        final_product = ProductRepository.find_by_id(product_id)
        assert final_product.version == test_product.version + 1

    def test_stock_depletion_race_condition(self, test_product):
        """
        Demonstrate race conditions in stock management.

        Scenario: Multiple customers try to buy the last few items simultaneously.
        Without proper handling, this could lead to overselling.
        """
        # Set initial stock to a small number to make race condition more likely
        test_product.stock_quantity = 5
        ProductRepository.update(test_product)

        product_id = test_product.id
        purchase_attempts = []

        def attempt_purchase(customer_id: int, quantity: int = 1):
            """Simulate a customer trying to purchase items."""
            try:
                # Step 1: Check availability (read current stock)
                product = ProductRepository.find_by_id(product_id)

                # Step 2: Customer decides to buy (simulate decision time)
                time.sleep(0.05)

                # Step 3: Process purchase (update stock)
                if product.stock_quantity >= quantity:
                    product.stock_quantity -= quantity
                    updated_product = ProductRepository.update(product)

                    if updated_product:
                        purchase_attempts.append({
                            "customer": customer_id,
                            "status": "success",
                            "quantity": quantity,
                            "remaining_stock": updated_product.stock_quantity
                        })
                    else:
                        purchase_attempts.append({
                            "customer": customer_id,
                            "status": "version_conflict",
                            "quantity": quantity
                        })
                else:
                    purchase_attempts.append({
                        "customer": customer_id,
                        "status": "insufficient_stock",
                        "quantity": quantity,
                        "available": product.stock_quantity
                    })

            except Exception as e:
                purchase_attempts.append({
                    "customer": customer_id,
                    "status": "error",
                    "error": str(e)
                })

        # Simulate 10 customers trying to buy 1 item each (but only 5 items available)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(attempt_purchase, customer_id, 1)
                for customer_id in range(10)
            ]

            # Wait for all attempts to complete
            for future in as_completed(futures):
                future.result()

        # Analyze results
        successful_purchases = [
            p for p in purchase_attempts if p["status"] == "success"]
        failed_purchases = [
            p for p in purchase_attempts if p["status"] != "success"]

        print("\n=== Stock Depletion Race Condition Test Results ===")
        print(f"Total purchase attempts: {len(purchase_attempts)}")
        print(f"Successful purchases: {len(successful_purchases)}")
        print(f"Failed purchases: {len(failed_purchases)}")

        # Print detailed results
        for attempt in purchase_attempts:
            status_symbol = "✓" if attempt["status"] == "success" else "✗"
            print(
                f"{status_symbol} Customer {attempt['customer']}: {attempt['status']}")

        # Verify no overselling occurred
        final_product = ProductRepository.find_by_id(product_id)
        total_sold = sum(p["quantity"] for p in successful_purchases)

        print("Initial stock: 5")
        print(f"Total sold: {total_sold}")
        print(f"Remaining stock: {final_product.stock_quantity}")

        assert final_product.stock_quantity >= 0, "Stock should never go negative"
        assert final_product.stock_quantity == 5 - \
            total_sold, "Stock calculation should be correct"
        assert total_sold <= 5, "Should not sell more than available stock"

    def test_high_concurrency_stress(self, test_product):
        """
        Test system behavior under high concurrency load.

        This test simulates a high-traffic scenario with many concurrent
        database operations to verify system stability.
        """
        product_id = test_product.id
        num_threads = 20
        operations_per_thread = 10
        results = {"reads": [], "writes": [], "errors": []}

        def perform_mixed_operations(thread_id: int):
            """Perform a mix of read and write operations."""
            for op_id in range(operations_per_thread):
                try:
                    if op_id % 3 == 0:
                        # Write operation: update price
                        product = ProductRepository.find_by_id(product_id)
                        product.price += 0.01  # Small increment
                        updated = ProductRepository.update(product)

                        if updated:
                            results["writes"].append(
                                f"Thread-{thread_id}-Op-{op_id}")
                    else:
                        # Read operation
                        product = ProductRepository.find_by_id(product_id)
                        if product:
                            results["reads"].append(
                                f"Thread-{thread_id}-Op-{op_id}")

                except Exception as e:
                    results["errors"].append(
                        f"Thread-{thread_id}-Op-{op_id}: {str(e)}")

                # Small delay to prevent overwhelming the system
                time.sleep(0.001)

        # Execute high concurrency test
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(perform_mixed_operations, thread_id)
                for thread_id in range(num_threads)
            ]

            # Wait for all operations to complete
            for future in as_completed(futures):
                future.result()

        end_time = time.time()
        duration = end_time - start_time

        # Analyze performance
        total_operations = num_threads * operations_per_thread
        successful_operations = len(results["reads"]) + len(results["writes"])
        error_count = len(results["errors"])

        print("\n=== High Concurrency Stress Test Results ===")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total operations attempted: {total_operations}")
        print(f"Successful reads: {len(results['reads'])}")
        print(f"Successful writes: {len(results['writes'])}")
        print(f"Errors: {error_count}")
        print(
            f"Success rate: {(successful_operations/total_operations)*100:.1f}%")
        print(f"Operations per second: {total_operations/duration:.1f}")

        # Assertions
        assert successful_operations > 0, "Some operations should succeed"
        success_rate = successful_operations / total_operations
        assert success_rate > 0.7, f"Success rate too low: {success_rate:.2f}"

        # Verify database consistency
        final_product = ProductRepository.find_by_id(product_id)
        assert final_product is not None, "Product should still exist"
        assert final_product.version >= test_product.version, "Version should have increased"

    def test_concurrent_creation_and_deletion(self):
        """
        Test concurrent creation and deletion of products.

        This test verifies that the system can handle many concurrent
        create and delete operations without issues.
        """
        results = {"created": [], "deleted": [], "errors": []}
        created_product_ids: list[int] = []
        creation_lock = threading.Lock()

        def create_and_delete_product(thread_id: int):
            """Create a product, wait, then delete it."""
            try:
                # Create product
                product = Product(
                    name=f"Temp Product {thread_id}",
                    description=f"Created by thread {thread_id}",
                    price=10.0 + thread_id,
                    stock_quantity=1
                )

                created_product = ProductRepository.create(product)

                if created_product:
                    with creation_lock:
                        created_product_ids.append(created_product.id)

                    results["created"].append(created_product.id)

                    # Wait a bit before deletion
                    time.sleep(0.05)

                    # Delete product
                    deleted = ProductRepository.delete(created_product.id)
                    if deleted:
                        results["deleted"].append(created_product.id)

            except Exception as e:
                results["errors"].append(f"Thread-{thread_id}: {str(e)}")

        # Run concurrent create/delete operations
        num_threads = 15

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(create_and_delete_product, thread_id)
                for thread_id in range(num_threads)
            ]

            for future in as_completed(futures):
                future.result()

        # Verify results
        print("\n=== Concurrent Creation/Deletion Test Results ===")
        print(f"Products created: {len(results['created'])}")
        print(f"Products deleted: {len(results['deleted'])}")
        print(f"Errors: {len(results['errors'])}")

        # Most operations should succeed
        assert len(results["created"]) > 0, "Some products should be created"
        assert len(
            results["errors"]) == 0, f"No errors expected, got: {results['errors']}"

        # Verify cleanup - check that deleted products don't exist
        for product_id in results["deleted"]:
            product = ProductRepository.find_by_id(product_id)

            assert product is None, f"Product {product_id} should be deleted"

    def test_optimistic_locking_retry_pattern(self, test_product: Product):
        """
        Demonstrate a retry pattern for handling optimistic locking conflicts.

        This shows how applications can implement retry logic to handle
        version conflicts gracefully.
        """
        product_id = test_product.id
        results = []

        def update_with_retry(thread_id: int, max_retries: int = 5):
            """Update product with retry logic for version conflicts."""
            for attempt in range(max_retries):
                try:
                    # Read current state
                    product = ProductRepository.find_by_id(product_id)

                    # Simulate processing time
                    time.sleep(0.02)

                    # Make modification
                    product.price += 1.0
                    product.description = f"Updated by thread {thread_id}, attempt {attempt}"

                    # Attempt update
                    updated_product = ProductRepository.update(product)

                    if updated_product:
                        results.append({
                            "thread": thread_id,
                            "attempt": attempt,
                            "status": "success",
                            "version": updated_product.version
                        })
                        return  # Success, exit retry loop
                    else:
                        # Version conflict, will retry
                        time.sleep(0.01 * (attempt + 1))  # Exponential backoff

                except Exception as e:
                    results.append({
                        "thread": thread_id,
                        "attempt": attempt,
                        "status": "error",
                        "error": str(e)
                    })
                    return

            # All retries exhausted
            results.append({
                "thread": thread_id,
                "status": "max_retries_exceeded",
                "attempts": max_retries
            })

        # Start multiple threads that will compete for updates
        num_threads = 8

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(update_with_retry, thread_id)
                for thread_id in range(num_threads)
            ]

            for future in as_completed(futures):
                future.result()

        # Analyze retry patterns
        successful_updates = [
            r for r in results if r.get("status") == "success"]
        failed_updates = [r for r in results if r.get("status") != "success"]

        print("\n=== Optimistic Locking Retry Pattern Results ===")
        print(f"Total threads: {num_threads}")
        print(f"Successful updates: {len(successful_updates)}")
        print(f"Failed updates: {len(failed_updates)}")

        # Show retry patterns
        for result in successful_updates:
            print(
                f"✓ Thread {result['thread']}: succeeded on attempt {result['attempt']}")

        for result in failed_updates:
            print(f"✗ Thread {result['thread']}: {result['status']}")

        # Most threads should eventually succeed with retries
        assert len(successful_updates) >= num_threads * \
            0.6, "Most updates should succeed with retries"

        # Verify final state
        final_product = ProductRepository.find_by_id(product_id)
        expected_version = test_product.version + len(successful_updates)

        assert final_product.version == expected_version


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
