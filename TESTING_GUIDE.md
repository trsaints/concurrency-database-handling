# Database Concurrency Testing Guide

This guide explains how to test database concurrency in your application and understand the various concurrency scenarios.

## Overview

The test suite demonstrates and validates several important database concurrency concepts:

1. **Optimistic Locking**: Using version numbers to prevent lost updates
2. **Race Conditions**: Handling simultaneous access to shared resources
3. **Stock Management**: Preventing overselling in concurrent scenarios
4. **Connection Pool Stress Testing**: Validating system behavior under load
5. **Retry Patterns**: Graceful handling of version conflicts

## Prerequisites

1. **Database Setup**: Ensure PostgreSQL is running

   ```bash
   docker-compose up -d
   ```

2. **Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

## Running the Tests

### Quick Concurrency Test Run

Run the main concurrency demonstration:

```bash
python run_tests.py
```

### Run All Tests

Run the complete test suite:

```bash
python run_tests.py --all
```

### Run Individual Test Categories

Run specific test files:

```bash
# Clean, focused concurrency tests (recommended)
pytest app/tests/test_concurrency_clean.py -v

# Comprehensive concurrency scenarios (verbose output)
pytest app/tests/test_concurrency.py -v

# Original detailed patterns (very verbose)
pytest app/tests/test_concurrency_patterns.py -v -s
```

### Run Specific Tests

Run individual test methods:

```bash
# Test optimistic locking (clean output)
pytest app/tests/test_concurrency_clean.py::TestConcurrencyPatterns::test_lost_update_prevention -v

# Test race conditions (clean output)
pytest app/tests/test_concurrency_clean.py::TestConcurrencyPatterns::test_stock_depletion_race_condition -v

# For more detailed failure output (if needed for debugging):
pytest app/tests/test_concurrency_clean.py::TestConcurrencyPatterns::test_lost_update_prevention -v --tb=short

# For full traceback (maximum detail):
pytest app/tests/test_concurrency_clean.py::TestConcurrencyPatterns::test_lost_update_prevention -v --tb=long
```

## Test Output Levels

The tests are configured for minimal, clean output by default. You can control the amount of detail shown on failures:

- **`--tb=line`** (default): Shows only the failing line
- **`--tb=short`**: Shows a short traceback
- **`--tb=long`**: Shows full traceback with all source code
- **`--tb=no`**: No traceback at all, just pass/fail

Example outputs:

### Clean Output (default):

```
FAILED test_lost_update_prevention - AssertionError: Expected 1 successful update, got 2
```

### Verbose Output (--tb=short):

```
FAILED test_lost_update_prevention - AssertionError: Expected 1 successful update, got 2
    assert successful_updates == 1, f"Expected 1 successful update, got {successful_updates}"
```

# Test race conditions

```
pytest app/tests/test_concurrency_patterns.py::TestConcurrencyPatterns::test_stock_depletion_race_condition -v -s

```

## Understanding the Test Results

### 1. Lost Update Prevention Test

**What it tests**: Demonstrates how optimistic locking prevents lost updates when multiple users edit the same record.

**Expected behavior**:

- Only one of two concurrent updates should succeed
- The failed update should be rejected due to version conflict
- Version number should increment correctly

**Sample output**:

```

=== Lost Update Prevention Test Results ===
Successful updates: 1
Failed updates: 1
✓ Alice: v0 -> v1, price: $110.0
✗ Bob: Version conflict

```

### 2. Stock Depletion Race Condition Test

**What it tests**: Simulates multiple customers trying to purchase limited stock simultaneously.

**Expected behavior**:

- No overselling should occur
- Stock should never go negative
- Total sold should not exceed available stock

**Sample output**:

```

=== Stock Depletion Race Condition Test Results ===
Total purchase attempts: 10
Successful purchases: 5
Failed purchases: 5
Initial stock: 5
Total sold: 5
Remaining stock: 0

```

### 3. High Concurrency Stress Test

**What it tests**: System behavior under high load with many concurrent operations.

**Expected behavior**:

- Most operations should succeed
- System should remain stable
- No database errors or connection issues

**Sample output**:

```

=== High Concurrency Stress Test Results ===
Duration: 2.45 seconds
Total operations attempted: 200
Successful reads: 134
Successful writes: 45
Errors: 0
Success rate: 89.5%
Operations per second: 81.6

```

### 4. Optimistic Locking Retry Pattern Test

**What it tests**: Demonstrates how applications can implement retry logic for handling version conflicts.

**Expected behavior**:

- Most threads should eventually succeed with retries
- Early attempts may fail due to conflicts
- Later attempts should succeed as conflicts resolve

**Sample output**:

```

=== Optimistic Locking Retry Pattern Results ===
Total threads: 8
Successful updates: 7
Failed updates: 1
✓ Thread 0: succeeded on attempt 0
✓ Thread 1: succeeded on attempt 2
✓ Thread 2: succeeded on attempt 1

```

## Key Concurrency Concepts Demonstrated

### Optimistic Locking

The application uses a `version` field to implement optimistic locking:

```sql
UPDATE products
SET name = %s, version = version + 1, updated_at = CURRENT_TIMESTAMP
WHERE id = %s AND version = %s
```

If the version doesn't match, the update fails, indicating another transaction modified the record.

### Race Condition Prevention

Stock updates are protected by the optimistic locking mechanism:

```python
# This prevents overselling by ensuring atomic stock updates
product = ProductRepository.find_by_id(product_id)
if product.stock_quantity >= quantity:
    product.stock_quantity -= quantity
    updated = ProductRepository.update(product)  # May fail if version changed
```

### Connection Pool Management

The application uses a connection pool to handle concurrent database access:

```python
# ThreadedConnectionPool manages concurrent connections
cls._connection_pool = ThreadedConnectionPool(
    minconn, maxconn,
    host=settings.database_host,
    # ... other parameters
)
```

## Interpreting Test Failures

### Common Issues and Solutions

1. **Database Connection Errors**

   - **Cause**: Database not running or connection parameters incorrect
   - **Solution**: Check `docker-compose up -d` and database settings

2. **High Error Rates in Stress Tests**

   - **Cause**: Connection pool exhaustion or database overload
   - **Solution**: Adjust connection pool settings or reduce test load

3. **Unexpected Optimistic Locking Behavior**

   - **Cause**: Database isolation level or transaction handling issues
   - **Solution**: Review transaction management in repository layer

4. **Inconsistent Race Condition Results**
   - **Cause**: Timing-dependent test behavior
   - **Solution**: This is expected - race conditions are inherently timing-dependent

## Customizing Tests

### Adding New Concurrency Scenarios

To add new concurrency tests:

1. Create a new test method in `TestConcurrencyPatterns`
2. Use threading or concurrent.futures for concurrent execution
3. Verify expected behavior and data consistency
4. Add appropriate assertions

Example structure:

```python
def test_new_concurrency_scenario(self, test_product):
    """Test description."""
    results = []

    def concurrent_operation():
        # Your concurrent operation here
        pass

    # Execute concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(concurrent_operation) for _ in range(5)]
        for future in as_completed(futures):
            future.result()

    # Verify results
    assert len(results) > 0
```

### Adjusting Test Parameters

Key parameters you can modify:

- `num_threads`: Number of concurrent operations
- `operations_per_thread`: Work per thread
- `max_retries`: Retry attempts for optimistic locking
- `initial_stock`: Starting inventory for race condition tests

## Best Practices for Concurrency Testing

1. **Use Realistic Scenarios**: Base tests on actual application usage patterns
2. **Test Edge Cases**: Low stock, high concurrency, network delays
3. **Verify Data Consistency**: Always check final state matches expectations
4. **Include Retry Logic**: Test how your application handles conflicts
5. **Monitor Performance**: Track success rates and response times
6. **Test Failure Scenarios**: Ensure graceful handling of conflicts and errors

## Troubleshooting

### Test Environment Issues

If tests fail consistently:

1. Check database connection: `python -c "from app.database.connection import DatabaseConnection; DatabaseConnection.initialize_pool()"`
2. Verify table schema: Check that the `products` table has the `version` column
3. Reset test data: Restart the database container to reset to initial state

### Performance Issues

If tests are slow or timing out:

1. Reduce the number of concurrent threads
2. Decrease operations per thread
3. Check database performance and connection limits
4. Consider using a faster test database setup

## Further Reading

For more information about database concurrency:

- [PostgreSQL Concurrency Control](https://www.postgresql.org/docs/current/mvcc.html)
- [Optimistic vs Pessimistic Locking](https://en.wikipedia.org/wiki/Optimistic_concurrency_control)
- [Database Transaction Isolation Levels](<https://en.wikipedia.org/wiki/Isolation_(database_systems)>)
