#!/usr/bin/env python3
"""
Script to run concurrency tests and demonstrate database concurrency handling.

This script sets up the environment and runs the concurrency tests to show
how different concurrency scenarios are handled by the application.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))


def check_database_connection():
    """Check if database is available."""
    try:
        from app.database.connection import DatabaseConnection
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def run_concurrency_tests():
    """Run the concurrency tests."""
    print("=" * 60)
    print("Database Concurrency Testing")
    print("=" * 60)

    # Check database connection first
    print("Checking database connection...")
    if not check_database_connection():
        print("❌ Database connection failed!")
        print("Make sure to start the database with: docker-compose up -d")
        return False

    print("✅ Database connection successful!")
    print()

    # Run specific concurrency tests
    test_commands = [
        {
            "name": "Lost Update Prevention Test",
            "command": ["python", "-m", "pytest", "app/tests/test_concurrency_clean.py::TestConcurrencyPatterns::test_lost_update_prevention", "-v"]
        },
        {
            "name": "Stock Depletion Race Condition Test",
            "command": ["python", "-m", "pytest", "app/tests/test_concurrency_clean.py::TestConcurrencyPatterns::test_stock_depletion_race_condition", "-v"]
        },
        {
            "name": "Optimistic Locking Retry Pattern Test",
            "command": ["python", "-m", "pytest", "app/tests/test_concurrency_clean.py::TestConcurrencyPatterns::test_optimistic_locking_retry_pattern", "-v"]
        },
        {
            "name": "High Concurrency Operations Test",
            "command": ["python", "-m", "pytest", "app/tests/test_concurrency_clean.py::TestConcurrencyPatterns::test_high_concurrency_operations", "-v"]
        }
    ]

    all_passed = True

    for test_info in test_commands:
        print(f"Running: {test_info['name']}")
        print("-" * 50)

        try:
            result = subprocess.run(
                test_info["command"],
                capture_output=False,
                text=True,
                timeout=60  # 60 second timeout per test
            )

            if result.returncode == 0:
                print(f"✅ {test_info['name']} PASSED")
            else:
                print(f"❌ {test_info['name']} FAILED")
                all_passed = False

        except subprocess.TimeoutExpired:
            print(f"⏰ {test_info['name']} TIMED OUT")
            all_passed = False
        except Exception as e:
            print(f"❌ {test_info['name']} ERROR: {e}")
            all_passed = False

        print()
        time.sleep(1)  # Brief pause between tests

    # Summary
    print("=" * 60)
    if all_passed:
        print("🎉 All concurrency tests PASSED!")
        print("The application correctly handles database concurrency!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    print("=" * 60)

    return all_passed


def run_all_tests():
    """Run all tests in the test suite."""
    print("Running complete test suite...")
    result = subprocess.run(
        ["python", "-m", "pytest", "app/tests/", "-v"],
        capture_output=False,
        text=True
    )
    return result.returncode == 0


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        success = run_all_tests()
    else:
        success = run_concurrency_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
