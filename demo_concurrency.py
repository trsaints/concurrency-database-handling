#!/usr/bin/env python3
"""
Interactive demonstration of database concurrency concepts.

This script provides a simple way to see concurrency issues in action
and understand how optimistic locking solves them.
"""

from app.database.connection import DatabaseConnection
from app.repositories.product_repository import ProductRepository
from app.entities.product import Product
import sys
import threading
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))


def demonstrate_lost_update_problem():
    """
    Demonstrate the classic 'Lost Update' problem and how optimistic locking solves it.
    """
    print("=" * 70)
    print("DEMONSTRATION: Lost Update Problem")
    print("=" * 70)
    print()

    # Create a test product
    print("📦 Creating test product...")
    test_product = Product(
        name="Demo Product",
        description="Product for demonstrating concurrency",
        price=100.0,
        stock_quantity=50
    )
    created_product = ProductRepository.create(test_product)
    product_id = created_product.id
    print(
        f"✅ Created product {product_id} with price ${created_product.price}")
    print()

    try:
        # Scenario: Two users want to update the same product
        print("👥 Scenario: Alice and Bob both want to update the product price")
        print()

        results = {"alice": None, "bob": None}

        def alice_update():
            """Alice's update process."""
            print("👩 Alice: Loading product page...")
            product = ProductRepository.find_by_id(product_id)
            print(
                f"👩 Alice: Sees price ${product.price}, version {product.version}")

            print("👩 Alice: Thinking about price change... (simulating user delay)")
            time.sleep(1)  # Alice takes 1 second to decide

            print("👩 Alice: Updating price to $120")
            product.price = 120.0
            product.description = "Updated by Alice"

            updated = ProductRepository.update(product)
            results["alice"] = updated

            if updated:
                print(
                    f"👩 Alice: ✅ Successfully updated! New version: {updated.version}")
            else:
                print("👩 Alice: ❌ Update failed - someone else modified the product!")

        def bob_update():
            """Bob's update process."""
            print("👨 Bob: Loading product page...")
            product = ProductRepository.find_by_id(product_id)
            print(
                f"👨 Bob: Sees price ${product.price}, version {product.version}")

            print("👨 Bob: Thinking about price change... (simulating user delay)")
            time.sleep(0.5)  # Bob takes 0.5 seconds to decide

            print("👨 Bob: Updating price to $110")
            product.price = 110.0
            product.description = "Updated by Bob"

            updated = ProductRepository.update(product)
            results["bob"] = updated

            if updated:
                print(
                    f"👨 Bob: ✅ Successfully updated! New version: {updated.version}")
            else:
                print("👨 Bob: ❌ Update failed - someone else modified the product!")

        # Start both users' processes simultaneously
        print("🚀 Starting both updates simultaneously...")
        print()

        alice_thread = threading.Thread(target=alice_update)
        bob_thread = threading.Thread(target=bob_update)

        alice_thread.start()
        bob_thread.start()

        alice_thread.join()
        bob_thread.join()

        print()
        print("📊 RESULTS:")
        print("-" * 40)

        # Check final state
        final_product = ProductRepository.find_by_id(product_id)

        if results["alice"] and results["bob"]:
            print("❌ PROBLEM: Both updates succeeded - this shouldn't happen!")
        elif results["alice"]:
            print("✅ Alice's update succeeded, Bob's was rejected")
            print(f"   Final price: ${final_product.price}")
            print(f"   Final version: {final_product.version}")
            print(f"   Description: {final_product.description}")
        elif results["bob"]:
            print("✅ Bob's update succeeded, Alice's was rejected")
            print(f"   Final price: ${final_product.price}")
            print(f"   Final version: {final_product.version}")
            print(f"   Description: {final_product.description}")
        else:
            print("❌ Both updates failed - unexpected!")

        print()
        print("🎓 EXPLANATION:")
        print("This demonstrates optimistic locking in action!")
        print("- Both users read the same initial version")
        print("- The first to update succeeds and increments the version")
        print("- The second update fails because the version has changed")
        print("- This prevents the 'lost update' problem where one user's")
        print("  changes would overwrite another's without them knowing")

    finally:
        # Cleanup
        print()
        print("🧹 Cleaning up...")
        ProductRepository.delete(product_id)
        print("✅ Test product deleted")


def demonstrate_race_condition():
    """
    Demonstrate race conditions in stock management.
    """
    print("\n" + "=" * 70)
    print("DEMONSTRATION: Race Condition in Stock Management")
    print("=" * 70)
    print()

    # Create a product with limited stock
    print("📦 Creating product with limited stock...")
    test_product = Product(
        name="Limited Edition Item",
        description="Only 3 left in stock!",
        price=50.0,
        stock_quantity=3
    )
    created_product = ProductRepository.create(test_product)
    product_id = created_product.id
    print(
        f"✅ Created product {product_id} with {created_product.stock_quantity} items in stock")
    print()

    try:
        print("🛒 Scenario: 5 customers try to buy the last 3 items simultaneously")
        print()

        purchase_results = []

        def attempt_purchase(customer_name, customer_id):
            """Simulate a customer purchase."""
            print(f"🛍️  {customer_name}: Checking stock...")

            # Read current stock
            product = ProductRepository.find_by_id(product_id)
            available_stock = product.stock_quantity

            print(f"🛍️  {customer_name}: Sees {available_stock} items available")

            if available_stock > 0:
                print(
                    f"🛍️  {customer_name}: Deciding to buy... (processing payment)")
                time.sleep(0.1)  # Simulate payment processing time

                print(f"🛍️  {customer_name}: Attempting to complete purchase")
                product.stock_quantity -= 1

                updated = ProductRepository.update(product)

                if updated:
                    purchase_results.append({
                        "customer": customer_name,
                        "success": True,
                        "remaining_stock": updated.stock_quantity
                    })
                    print(
                        f"🛍️  {customer_name}: ✅ Purchase successful! {updated.stock_quantity} items left")
                else:
                    purchase_results.append({
                        "customer": customer_name,
                        "success": False,
                        "reason": "Version conflict - someone else bought it first"
                    })
                    print(
                        f"🛍️  {customer_name}: ❌ Purchase failed - item no longer available")
            else:
                purchase_results.append({
                    "customer": customer_name,
                    "success": False,
                    "reason": "Out of stock"
                })
                print(f"🛍️  {customer_name}: ❌ Out of stock!")

        # Create 5 customers trying to buy simultaneously
        customers = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        threads = []

        print("🚀 All customers start shopping simultaneously...")
        print()

        for i, customer in enumerate(customers):
            thread = threading.Thread(
                target=attempt_purchase, args=(customer, i))
            threads.append(thread)
            thread.start()

        # Wait for all purchases to complete
        for thread in threads:
            thread.join()

        print()
        print("📊 FINAL RESULTS:")
        print("-" * 40)

        successful_purchases = [r for r in purchase_results if r["success"]]
        failed_purchases = [r for r in purchase_results if not r["success"]]

        print(f"✅ Successful purchases: {len(successful_purchases)}")
        for purchase in successful_purchases:
            print(f"   - {purchase['customer']}")

        print(f"❌ Failed purchases: {len(failed_purchases)}")
        for purchase in failed_purchases:
            print(f"   - {purchase['customer']}: {purchase['reason']}")

        # Verify final stock
        final_product = ProductRepository.find_by_id(product_id)
        print(f"📦 Final stock: {final_product.stock_quantity}")

        print()
        print("🎓 EXPLANATION:")
        print("This demonstrates how optimistic locking prevents overselling!")
        print("- Without proper concurrency control, all 5 customers might")
        print("  see '3 items available' and all try to buy")
        print("- This could result in negative stock (overselling)")
        print("- With optimistic locking, only 3 purchases can succeed")
        print("- The version mechanism ensures atomic stock updates")

    finally:
        # Cleanup
        print()
        print("🧹 Cleaning up...")
        ProductRepository.delete(product_id)
        print("✅ Test product deleted")


def main():
    """Main demonstration function."""
    print("🎭 Database Concurrency Demonstration")
    print("=====================================")
    print()

    # Check database connection
    try:
        DatabaseConnection.initialize_pool()
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure to start the database with: docker-compose up -d")
        return

    print()

    try:
        # Run demonstrations
        demonstrate_lost_update_problem()
        demonstrate_race_condition()

        print("\n" + "=" * 70)
        print("🎉 DEMONSTRATION COMPLETE!")
        print("=" * 70)
        print()
        print("💡 Key Takeaways:")
        print("1. Optimistic locking prevents lost updates")
        print("2. Version numbers ensure data consistency")
        print("3. Failed updates can be handled gracefully with retries")
        print("4. Race conditions are prevented by atomic operations")
        print()
        print("📚 For more detailed tests, run: python run_tests.py")

    except KeyboardInterrupt:
        print("\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")


if __name__ == "__main__":
    main()
