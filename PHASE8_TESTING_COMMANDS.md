# Phase 8 Testing Commands

## Quick Start Testing

### 1. Run Unit Tests (Recommended First Step)
```bash
# Run all Phase 8 tests
make test ARGS='apps.tenants.tests'

# Run only task tests
make test ARGS='apps.tenants.tests.test_tasks'

# Run only signal tests
make test ARGS='apps.tenants.tests.test_signals'
```

### 2. Run Quick Integration Test
```bash
# Run the management command test (auto-rollback)
make manage ARGS="test_phase8"

# Keep test data after running
make manage ARGS="test_phase8 --keep-data"

# Clean up test data
make manage ARGS="test_phase8 --cleanup-only"
```

### 3. Run Interactive Test Script
```bash
# Run the quick test script
make shell < test_phase8_quick.py

# Or manually in shell
make shell
# Then copy/paste the script content
```

## Full Testing with Celery

### 1. Start Required Services
```bash
# Terminal 1: Start all services
make start

# Terminal 2: Start Celery worker
make ssh
celery -A isp_billing_system worker --loglevel=info

# Terminal 3: Start Celery beat (optional, for scheduled tasks)
make ssh
celery -A isp_billing_system beat --loglevel=info
```

### 2. Test Celery Task Execution
```bash
make shell
```

```python
# Test specific tenant
from apps.customer_subscriptions.tasks import update_expired_subscriptions_for_tenant
result = update_expired_subscriptions_for_tenant.delay(1)  # Use actual tenant ID
print(result.get(timeout=10))

# Test all tenants
from apps.customer_subscriptions.tasks import update_expired_subscriptions_all_tenants
result = update_expired_subscriptions_all_tenants.delay()
print(result.get(timeout=10))
```

## What Each Test Validates

1. **Unit Tests** (`test_tasks.py`, `test_signals.py`)
   - Task isolation between tenants
   - Signal handlers create system users
   - Inactive tenants are skipped
   - Audit logging works in background

2. **Management Command Test** (`test_phase8`)
   - End-to-end task execution
   - Signal handling
   - Audit log creation
   - Multi-tenant processing

3. **Quick Script Test** (`test_phase8_quick.py`)
   - Creates real test data
   - Tests all Phase 8 features
   - Shows detailed results
   - Cleans up after itself

## Expected Results

✅ All unit tests pass
✅ Tasks only process their assigned tenant's data
✅ System users created for each tenant
✅ Audit logs created for background changes
✅ Inactive tenants skipped
✅ No cross-tenant data leakage

## Troubleshooting

If tests fail:

1. **Check services are running**
   ```bash
   docker ps
   # Should show: db, redis containers
   ```

2. **Check for existing test data**
   ```bash
   make manage ARGS="test_phase8 --cleanup-only"
   ```

3. **Check Celery is working**
   ```bash
   make shell
   from celery import current_app
   current_app.control.inspect().active()
   ```

4. **Check Redis connection**
   ```bash
   make shell
   from django.core.cache import cache
   cache.set('test', 'value')
   print(cache.get('test'))
   ```

## Next Steps

After testing is complete:
- Review PHASE8_COMPLETE.md for implementation details
- Proceed to Phase 9 (Reporting System Updates)
- Or run production tests with real data (carefully!)
