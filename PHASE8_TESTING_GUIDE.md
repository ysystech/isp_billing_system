# Phase 8 Testing Guide

## Overview
This guide will help you test the tenant-aware background tasks and signals implementation from Phase 8.

## Prerequisites

1. Start all services:
```bash
make start
# Or in background:
make start-bg
```

2. Ensure Redis is running (for Celery):
```bash
docker ps | grep redis
```

3. Start Celery worker (in a new terminal):
```bash
make ssh
celery -A isp_billing_system worker --loglevel=info
```

4. Start Celery Beat (in another terminal):
```bash
make ssh
celery -A isp_billing_system beat --loglevel=info
```

## Test 1: Run Unit Tests

### Run all tenant task tests:
```bash
make test ARGS='apps.tenants.tests.test_tasks'
```

### Run tenant signal tests:
```bash
make test ARGS='apps.tenants.tests.test_signals'
```

### Run all Phase 8 related tests:
```bash
make test ARGS='apps.tenants.tests'
```

## Test 2: Manual Task Testing

### 2.1 Create Test Tenants and Data

First, access Django shell:
```bash
make shell
```

Then run this setup script:
```python
from django.utils import timezone
from datetime import timedelta
from apps.tenants.models import Tenant
from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.subscriptions.models import SubscriptionPlan
from apps.customer_installations.models import CustomerInstallation
from apps.customer_subscriptions.models import CustomerSubscription

# Create two test tenants
tenant1 = Tenant.objects.create(name="Test ISP 1", is_active=True)
tenant2 = Tenant.objects.create(name="Test ISP 2", is_active=True)

# Create a barangay for each tenant
barangay1 = Barangay.objects.create(
    tenant=tenant1,
    name="Test Barangay 1",
    code="TB1"
)
barangay2 = Barangay.objects.create(
    tenant=tenant2,
    name="Test Barangay 2",
    code="TB2"
)

# Create subscription plans
plan1 = SubscriptionPlan.objects.create(
    tenant=tenant1,
    name="Basic Plan T1",
    speed=10,
    price=500.00,
    day_count=30
)
plan2 = SubscriptionPlan.objects.create(
    tenant=tenant2,
    name="Basic Plan T2",
    speed=20,
    price=600.00,
    day_count=30
)

# Create customers
customer1 = Customer.objects.create(
    tenant=tenant1,
    first_name="John",
    last_name="Doe",
    email="john@test1.com",
    phone_primary="09000000001",
    street_address="Test Street 1",
    barangay=barangay1
)
customer2 = Customer.objects.create(
    tenant=tenant2,
    first_name="Jane",
    last_name="Smith",
    email="jane@test2.com",
    phone_primary="09000000002",
    street_address="Test Street 2",
    barangay=barangay2
)

# Create installations
install1 = CustomerInstallation.objects.create(
    tenant=tenant1,
    customer=customer1,
    olt="OLT1",
    onu_serial="TEST12345",
    installation_date=timezone.now().date(),
    status='ACTIVE'
)
install2 = CustomerInstallation.objects.create(
    tenant=tenant2,
    customer=customer2,
    olt="OLT2",
    onu_serial="TEST67890",
    installation_date=timezone.now().date(),
    status='ACTIVE'
)

# Create expired subscriptions for both tenants
expired1 = CustomerSubscription.objects.create(
    tenant=tenant1,
    customer_installation=install1,
    subscription_plan=plan1,
    start_date=timezone.now() - timedelta(days=60),
    end_date=timezone.now() - timedelta(days=1),
    status='ACTIVE',
    payment_method='GCASH',
    amount_paid=500.00
)
expired2 = CustomerSubscription.objects.create(
    tenant=tenant2,
    customer_installation=install2,
    subscription_plan=plan2,
    start_date=timezone.now() - timedelta(days=60),
    end_date=timezone.now() - timedelta(days=1),
    status='ACTIVE',
    payment_method='GCASH',
    amount_paid=600.00
)

# Create soon-to-expire subscriptions
expiring1 = CustomerSubscription.objects.create(
    tenant=tenant1,
    customer_installation=install1,
    subscription_plan=plan1,
    start_date=timezone.now() - timedelta(days=28),
    end_date=timezone.now() + timedelta(days=2),
    status='ACTIVE',
    payment_method='GCASH',
    amount_paid=500.00
)
expiring2 = CustomerSubscription.objects.create(
    tenant=tenant2,
    customer_installation=install2,
    subscription_plan=plan2,
    start_date=timezone.now() - timedelta(days=28),
    end_date=timezone.now() + timedelta(days=2),
    status='ACTIVE',
    payment_method='GCASH',
    amount_paid=600.00
)

print(f"Created test data:")
print(f"- Tenant 1: {tenant1.name} (ID: {tenant1.id})")
print(f"- Tenant 2: {tenant2.name} (ID: {tenant2.id})")
print(f"- 2 expired subscriptions")
print(f"- 2 expiring subscriptions")
```

### 2.2 Test Individual Tenant Task Execution

In Django shell:
```python
from apps.customer_subscriptions.tasks import update_expired_subscriptions_for_tenant, send_expiration_reminders_for_tenant
from apps.tenants.models import Tenant

# Get tenant IDs
tenant1 = Tenant.objects.get(name="Test ISP 1")
tenant2 = Tenant.objects.get(name="Test ISP 2")

# Test updating expired subscriptions for tenant 1 only
result = update_expired_subscriptions_for_tenant(tenant1.id)
print(result)
# Should show: "Tenant Test ISP 1: Updated 1 expired subscriptions"

# Check that tenant 2's subscription is still active
from apps.customer_subscriptions.models import CustomerSubscription
t2_subs = CustomerSubscription.objects.filter(tenant=tenant2, status='EXPIRED')
print(f"Tenant 2 expired subscriptions: {t2_subs.count()}")  # Should be 0

# Test expiration reminders for tenant 2 only
result = send_expiration_reminders_for_tenant(tenant2.id)
print(result)
# Should show: "Tenant Test ISP 2: Sent 1 expiration reminders"
```

### 2.3 Test All Tenants Task Execution

```python
from apps.customer_subscriptions.tasks import update_expired_subscriptions_all_tenants

# Reset the expired subscription for tenant 2
expired = CustomerSubscription.objects.filter(tenant=tenant2, end_date__lt=timezone.now()).first()
expired.status = 'ACTIVE'
expired.save()

# Run task for all tenants
results = update_expired_subscriptions_all_tenants()
print(results)
# Should show results for both tenants
```

### 2.4 Test Background Task via Celery

```python
# Queue task for specific tenant
from apps.customer_subscriptions.tasks import update_expired_subscriptions_for_tenant
result = update_expired_subscriptions_for_tenant.delay(tenant1.id)
print(f"Task ID: {result.id}")

# Check task result
print(result.get(timeout=10))

# Queue task for all tenants
from apps.customer_subscriptions.tasks import update_expired_subscriptions_all_tenants
result = update_expired_subscriptions_all_tenants.delay()
print(result.get(timeout=10))
```

## Test 3: Signal Testing

### 3.1 Test Tenant Creation Signal

```python
from apps.tenants.models import Tenant
from apps.users.models import CustomUser

# Create a new tenant
new_tenant = Tenant.objects.create(name="Signal Test ISP", is_active=True)

# Check if system user was created
system_user = CustomUser.objects.filter(username=f"system_{new_tenant.id}").first()
print(f"System user created: {system_user}")
print(f"System user tenant: {system_user.tenant.name}")
print(f"System user active: {system_user.is_active}")  # Should be False
```

### 3.2 Test Audit Logging in Background Tasks

```python
from apps.customer_subscriptions.tasks import update_expired_subscriptions_for_tenant
from apps.audit_logs.models import AuditLogEntry
from django.contrib.admin.models import LogEntry

# Count audit logs before
before_count = AuditLogEntry.objects.count()

# Run a task that modifies data
tenant = Tenant.objects.get(name="Test ISP 1")
result = update_expired_subscriptions_for_tenant(tenant.id)

# Check audit logs after
after_count = AuditLogEntry.objects.count()
print(f"Audit logs created: {after_count - before_count}")

# Check the latest audit log
latest = AuditLogEntry.objects.order_by('-id').first()
if latest:
    print(f"Latest audit log:")
    print(f"- User: {latest.log_entry.user.username}")
    print(f"- Action: {latest.log_entry.get_action_flag_display()}")
    print(f"- Object: {latest.log_entry.object_repr}")
    print(f"- IP: {latest.ip_address}")
    print(f"- User Agent: {latest.user_agent}")
    print(f"- Tenant: {latest.tenant.name}")
```

## Test 4: Verify Tenant Isolation

### 4.1 Cross-Tenant Data Check

```python
from apps.customer_subscriptions.models import CustomerSubscription
from apps.tenants.context import tenant_context

tenant1 = Tenant.objects.get(name="Test ISP 1")
tenant2 = Tenant.objects.get(name="Test ISP 2")

# Run task in tenant 1 context
with tenant_context(tenant1):
    # This should only see tenant 1's data
    subs = CustomerSubscription.objects.all()
    print(f"In tenant 1 context, subscriptions visible: {subs.count()}")
    for sub in subs:
        print(f"- Subscription tenant: {sub.tenant.name}")
```

## Test 5: Check Scheduled Tasks

### 5.1 List Scheduled Tasks

```python
from django_celery_beat.models import PeriodicTask

tasks = PeriodicTask.objects.all()
for task in tasks:
    print(f"Task: {task.name}")
    print(f"- Enabled: {task.enabled}")
    print(f"- Task: {task.task}")
    print(f"- Schedule: {task.interval or task.crontab}")
    print("---")
```

### 5.2 Manually Trigger Scheduled Task

```python
from django_celery_beat.models import PeriodicTask

# Find the task
task = PeriodicTask.objects.get(name="update-expired-subscriptions-all-tenants")

# Trigger it manually
from celery import current_app
current_app.send_task(task.task)
```

## Test 6: Performance Testing

### 6.1 Test Task Performance with Multiple Tenants

```python
import time
from apps.customer_subscriptions.tasks import update_expired_subscriptions_all_tenants

# Time the task execution
start = time.time()
result = update_expired_subscriptions_all_tenants()
end = time.time()

print(f"Task completed in {end - start:.2f} seconds")
print(f"Processed {len(result)} tenants")
```

## Test 7: Error Handling

### 7.1 Test Inactive Tenant Handling

```python
# Make a tenant inactive
tenant = Tenant.objects.get(name="Test ISP 2")
tenant.is_active = False
tenant.save()

# Try to run task for inactive tenant
from apps.customer_subscriptions.tasks import update_expired_subscriptions_for_tenant
result = update_expired_subscriptions_for_tenant(tenant.id)
print(result)  # Should return None

# Run all tenants task - should skip inactive
from apps.customer_subscriptions.tasks import update_expired_subscriptions_all_tenants
results = update_expired_subscriptions_all_tenants()
print(f"Active tenants processed: {len(results)}")
```

## Cleanup

After testing, clean up test data:
```python
# Delete test tenants (will cascade delete all related data)
Tenant.objects.filter(name__startswith="Test ISP").delete()
Tenant.objects.filter(name="Signal Test ISP").delete()
print("Test data cleaned up")
```

## Expected Results

1. **Unit Tests**: All tests should pass
2. **Task Isolation**: Tasks should only process data for their assigned tenant
3. **Signal Handlers**: System users should be created automatically
4. **Audit Logging**: All background changes should be logged with proper tenant context
5. **Performance**: Tasks should complete quickly even with multiple tenants
6. **Error Handling**: Inactive tenants should be skipped gracefully

## Troubleshooting

1. **Celery not running**: Ensure Redis is running and Celery worker is started
2. **Tasks not executing**: Check Celery logs for errors
3. **Audit logs missing**: Verify tenant context is set properly
4. **Cross-tenant data**: Check that all queries filter by tenant

## Success Criteria

✅ Tasks process only their assigned tenant's data
✅ No cross-tenant data leakage
✅ All changes are audit logged
✅ System users are created for background operations
✅ Inactive tenants are skipped
✅ Tasks complete successfully via Celery
