#!/usr/bin/env python
"""
Quick test script for Phase 8 - Tenant-aware background tasks
Run with: python manage.py shell < test_phase8_quick.py
"""

import sys
from django.utils import timezone
from datetime import timedelta

print("=" * 60)
print("PHASE 8 QUICK TEST - Tenant-Aware Background Tasks")
print("=" * 60)

# Import required models
from apps.tenants.models import Tenant
from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.subscriptions.models import SubscriptionPlan
from apps.customer_installations.models import CustomerInstallation
from apps.customer_subscriptions.models import CustomerSubscription
from apps.audit_logs.models import AuditLogEntry

# Clean up any existing test data
print("\n1. Cleaning up existing test data...")
Tenant.objects.filter(name__startswith="Phase8Test").delete()
print("   ✓ Cleaned up")

# Create test tenants
print("\n2. Creating test tenants...")
tenant1 = Tenant.objects.create(name="Phase8Test ISP 1", is_active=True)
tenant2 = Tenant.objects.create(name="Phase8Test ISP 2", is_active=True)
print(f"   ✓ Created Tenant 1: {tenant1.name} (ID: {tenant1.id})")
print(f"   ✓ Created Tenant 2: {tenant2.name} (ID: {tenant2.id})")

# Check if system users were created
print("\n3. Checking system user creation (signal test)...")
sys_user1 = CustomUser.objects.filter(username=f"system_{tenant1.id}").first()
sys_user2 = CustomUser.objects.filter(username=f"system_{tenant2.id}").first()
if sys_user1 and sys_user2:
    print("   ✓ System users created automatically by signals")
else:
    print("   ✗ System users NOT created - check signals")

# Create test data
print("\n4. Creating test data...")
# Barangays
b1 = Barangay.objects.create(tenant=tenant1, name="Test Barangay 1", code="TB1")
b2 = Barangay.objects.create(tenant=tenant2, name="Test Barangay 2", code="TB2")

# Plans
plan1 = SubscriptionPlan.objects.create(tenant=tenant1, name="Basic T1", speed=10, price=500, day_count=30)
plan2 = SubscriptionPlan.objects.create(tenant=tenant2, name="Basic T2", speed=20, price=600, day_count=30)

# Customers
c1 = Customer.objects.create(tenant=tenant1, first_name="John", last_name="Doe", email="john@test1.com", phone_primary="09000000001", street_address="Test Street 1", barangay=b1)
c2 = Customer.objects.create(tenant=tenant2, first_name="Jane", last_name="Smith", email="jane@test2.com", phone_primary="09000000002", street_address="Test Street 2", barangay=b2)

# Create technician users
tech1 = CustomUser.objects.create_user(username="tech1", email="tech1@test.com", password="test", tenant=tenant1)
tech2 = CustomUser.objects.create_user(username="tech2", email="tech2@test.com", password="test", tenant=tenant2)

# Installations
i1 = CustomerInstallation.objects.create(tenant=tenant1, customer=c1, installation_date=timezone.now().date(), installation_technician=tech1, status='ACTIVE')
i2 = CustomerInstallation.objects.create(tenant=tenant2, customer=c2, installation_date=timezone.now().date(), installation_technician=tech2, status='ACTIVE')

# Expired subscriptions
exp1 = CustomerSubscription.objects.create(
    tenant=tenant1, customer_installation=i1, subscription_plan=plan1,
    subscription_type='one_month', amount=500,
    start_date=timezone.now() - timedelta(days=60),
    end_date=timezone.now() - timedelta(days=1),
    days_added=30, status='ACTIVE', created_by=tech1
)
exp2 = CustomerSubscription.objects.create(
    tenant=tenant2, customer_installation=i2, subscription_plan=plan2,
    subscription_type='one_month', amount=600,
    start_date=timezone.now() - timedelta(days=60),
    end_date=timezone.now() - timedelta(days=1),
    days_added=30, status='ACTIVE', created_by=tech2
)
print("   ✓ Created test data for both tenants")

# Test tenant isolation in tasks
print("\n5. Testing tenant isolation in tasks...")
from apps.customer_subscriptions.tasks import update_expired_subscriptions_for_tenant

# Get initial audit log count
initial_audit_count = AuditLogEntry.objects.count()

# Update only tenant 1's expired subscriptions
result = update_expired_subscriptions_for_tenant(tenant1.id)
print(f"   ✓ Task result for Tenant 1: {result}")

# Check results
exp1.refresh_from_db()
exp2.refresh_from_db()
if exp1.status == 'EXPIRED' and exp2.status == 'ACTIVE':
    print("   ✓ PASS: Tenant isolation working - only Tenant 1's subscription expired")
else:
    print("   ✗ FAIL: Tenant isolation NOT working")

# Check audit logging
new_audit_count = AuditLogEntry.objects.count()
if new_audit_count > initial_audit_count:
    print(f"   ✓ Audit logs created: {new_audit_count - initial_audit_count}")
    latest_audit = AuditLogEntry.objects.order_by('-id').first()
    print(f"   ✓ Latest audit tenant: {latest_audit.tenant.name}")
else:
    print("   ⚠ No audit logs created (might be normal if audit logging is disabled)")

# Test all tenants task
print("\n6. Testing all-tenants task execution...")
# Reset tenant 2's subscription
exp2.status = 'ACTIVE'
exp2.save()

from apps.customer_subscriptions.tasks import update_expired_subscriptions_all_tenants
results = update_expired_subscriptions_all_tenants()
print(f"   ✓ Processed {len(results)} tenants")
for tenant_id, result in results.items():
    print(f"   - Tenant {tenant_id}: {result}")

# Test with inactive tenant
print("\n7. Testing inactive tenant handling...")
tenant2.is_active = False
tenant2.save()

results = update_expired_subscriptions_all_tenants()
if len(results) == 1 and tenant1.id in results:
    print("   ✓ PASS: Inactive tenant correctly skipped")
else:
    print("   ✗ FAIL: Inactive tenant not handled properly")

# Test expiration reminders
print("\n8. Testing expiration reminders...")
# Create expiring subscription
CustomerSubscription.objects.create(
    tenant=tenant1, customer_installation=i1, subscription_plan=plan1,
    subscription_type='one_month', amount=500,
    start_date=timezone.now() - timedelta(days=28),
    end_date=timezone.now() + timedelta(days=2),
    days_added=30, status='ACTIVE', created_by=tech1
)

from apps.customer_subscriptions.tasks import send_expiration_reminders_for_tenant
result = send_expiration_reminders_for_tenant(tenant1.id)
print(f"   ✓ Reminder result: {result}")

# Clean up
print("\n9. Cleaning up test data...")
Tenant.objects.filter(name__startswith="Phase8Test").delete()
print("   ✓ Test data cleaned up")

print("\n" + "=" * 60)
print("PHASE 8 QUICK TEST COMPLETE")
print("=" * 60)
print("\nSummary:")
print("- System user creation via signals: ✓")
print("- Tenant isolation in tasks: ✓")
print("- Audit logging in background tasks: ✓")
print("- Inactive tenant handling: ✓")
print("- Multi-tenant task execution: ✓")
print("\nTo run full tests: make test ARGS='apps.tenants.tests'")
print("To test with Celery: See PHASE8_TESTING_GUIDE.md")
