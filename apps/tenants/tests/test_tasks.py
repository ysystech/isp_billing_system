"""
Tests for tenant-aware Celery tasks.
"""
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.customer_installations.models import CustomerInstallation
from apps.customer_subscriptions.models import CustomerSubscription
from apps.customer_subscriptions.tasks import (
    update_expired_subscriptions,
    send_expiration_reminders,
    update_expired_subscriptions_all_tenants,
    update_expired_subscriptions_for_tenant,
)
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.subscriptions.models import SubscriptionPlan
from apps.tenants.models import Tenant
from apps.tenants.context import tenant_context
from apps.tenants.tasks import run_tenant_task
from apps.users.models import CustomUser
from apps.utils.test_base import TenantTestCase


class TenantAwareTaskTests(TenantTestCase):
    """Test tenant-aware task functionality."""
    
    def setUp(self):
        super().setUp()
        
        # Clean up any existing test tenants
        Tenant.objects.filter(name__startswith="TaskTest").delete()
        
        # Create a second tenant for isolation testing
        self.tenant2 = Tenant.objects.create(
            name="TaskTest ISP 2",
            is_active=True
        )
        
        # Update first tenant name to avoid conflicts
        self.tenant.name = "TaskTest ISP 1"
        self.tenant.save()
        
        # Create barangays
        self.barangay = Barangay.objects.create(
            tenant=self.tenant,
            name="Test Barangay 1",
            code="TB1"
        )
        
        self.barangay2 = Barangay.objects.create(
            tenant=self.tenant2,
            name="Test Barangay 2", 
            code="TB2"
        )
        
        # Create test data for tenant 1
        self.plan1 = SubscriptionPlan.objects.create(
            tenant=self.tenant,
            name="Basic Plan",
            speed=10,
            price=500.00,
            day_count=30
        )
        
        self.customer1 = Customer.objects.create(
            tenant=self.tenant,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_primary="09000000001",
            street_address="Test Street 1",
            barangay=self.barangay
        )
        
        # Create test technicians
        self.tech1 = CustomUser.objects.create_user(
            username="tasktech1",
            email="tasktech1@test.com",
            password="test",
            tenant=self.tenant
        )
        
        self.tech2 = CustomUser.objects.create_user(
            username="tasktech2", 
            email="tasktech2@test.com",
            password="test",
            tenant=self.tenant2
        )
        
        self.installation1 = CustomerInstallation.objects.create(
            tenant=self.tenant,
            customer=self.customer1,
            installation_date=timezone.now().date(),
            installation_technician=self.tech1,
            status='ACTIVE'
        )
        
        # Create test data for tenant 2
        self.plan2 = SubscriptionPlan.objects.create(
            tenant=self.tenant2,
            name="Premium Plan",
            speed=20,
            price=1000.00,
            day_count=30
        )
        
        self.customer2 = Customer.objects.create(
            tenant=self.tenant2,
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            phone_primary="09000000002",
            street_address="Test Street 2",
            barangay=self.barangay2
        )
        
        self.installation2 = CustomerInstallation.objects.create(
            tenant=self.tenant2,
            customer=self.customer2,
            installation_date=timezone.now().date(),
            installation_technician=self.tech2,
            status='ACTIVE'
        )

    def create_expired_subscription(self, tenant, installation, plan, technician):
        """Helper to create an expired subscription and bypass save logic"""
        sub = CustomerSubscription.objects.create(
            tenant=tenant,
            customer_installation=installation,
            subscription_plan=plan,
            subscription_type='one_month',
            amount=plan.price,
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() + timedelta(days=30),  # Will be updated
            days_added=30,
            status='ACTIVE',
            created_by=technician
        )
        # Force expired date
        CustomerSubscription.objects.filter(id=sub.id).update(
            end_date=timezone.now() - timedelta(days=1)
        )
        return CustomerSubscription.objects.get(id=sub.id)

    def test_update_expired_subscriptions_tenant_isolation(self):
        """Test that task processes only the current tenant's data."""
        # The key insight: the task correctly filters by tenant
        # We'll test this by running the task and verifying it only
        # mentions the current tenant in its output
        
        # Create subscriptions
        for tenant, installation, plan, tech in [
            (self.tenant, self.installation1, self.plan1, self.tech1),
            (self.tenant2, self.installation2, self.plan2, self.tech2)
        ]:
            # Create subscription with past end date
            CustomerSubscription.objects.create(
                tenant=tenant,
                customer_installation=installation,
                subscription_plan=plan,
                subscription_type='one_month',
                amount=plan.price,
                start_date=timezone.now() - timedelta(days=35),
                end_date=timezone.now() - timedelta(days=5),
                days_added=30,
                status='ACTIVE',
                created_by=tech
            )
        
        # Run task for tenant 1 only
        with tenant_context(self.tenant):
            result = update_expired_subscriptions.run()
        
        # Verify the task output mentions only tenant 1
        self.assertIn(self.tenant.name, result)
        self.assertNotIn(self.tenant2.name, result)
        
        # Run task for tenant 2
        with tenant_context(self.tenant2):
            result2 = update_expired_subscriptions.run()
        
        # Verify the task output mentions only tenant 2
        self.assertIn(self.tenant2.name, result2)
        self.assertNotIn(self.tenant.name, result2)
        
    def test_send_expiration_reminders_tenant_isolation(self):
        """Test that expiration reminders only process current tenant's data."""
        # Create soon-to-expire subscription for tenant 1
        expiring_sub1 = CustomerSubscription.objects.create(
            tenant=self.tenant,
            customer_installation=self.installation1,
            subscription_plan=self.plan1,
            subscription_type='one_month',
            amount=self.plan1.price,
            start_date=timezone.now() - timedelta(days=28),
            end_date=timezone.now() + timedelta(days=2),
            days_added=30,
            status='ACTIVE',
            created_by=self.tech1
        )
        
        # Create soon-to-expire subscription for tenant 2
        expiring_sub2 = CustomerSubscription.objects.create(
            tenant=self.tenant2,
            customer_installation=self.installation2,
            subscription_plan=self.plan2,
            subscription_type='one_month',
            amount=self.plan2.price,
            start_date=timezone.now() - timedelta(days=28),
            end_date=timezone.now() + timedelta(days=2),
            days_added=30,
            status='ACTIVE',
            created_by=self.tech2
        )
        
        # Run task for tenant 1 only
        with tenant_context(self.tenant):
            result = send_expiration_reminders.run()
        
        # Should only mention tenant 1's reminder
        self.assertIn(self.tenant.name, result)
        self.assertIn("1 expiration reminder", result)
        
    def test_run_all_tenants_task(self):
        """Test running tasks for all active tenants."""
        # Create expired subscriptions for both tenants
        self.create_expired_subscription(
            self.tenant, self.installation1, self.plan1, self.tech1
        )
        self.create_expired_subscription(
            self.tenant2, self.installation2, self.plan2, self.tech2
        )
        
        # Run task for all tenants
        results = update_expired_subscriptions.run_for_all_tenants()
        
        # Filter results to only our test tenants
        test_results = {k: v for k, v in results.items() 
                       if k in [self.tenant.id, self.tenant2.id]}
        
        # Should have results for both test tenants
        self.assertEqual(len(test_results), 2)
        self.assertIn(self.tenant.id, test_results)
        self.assertIn(self.tenant2.id, test_results)
        
        # Check both subscriptions were updated
        self.assertEqual(
            CustomerSubscription.objects.filter(
                tenant__in=[self.tenant, self.tenant2],
                status='EXPIRED'
            ).count(),
            2
        )
        
    def test_inactive_tenant_skipped(self):
        """Test that inactive tenants are skipped in processing."""
        # Make tenant 2 inactive
        self.tenant2.is_active = False
        self.tenant2.save()
        
        # Create expired subscriptions for both tenants
        self.create_expired_subscription(
            self.tenant, self.installation1, self.plan1, self.tech1
        )
        self.create_expired_subscription(
            self.tenant2, self.installation2, self.plan2, self.tech2
        )
        
        # Run task for all tenants
        results = update_expired_subscriptions.run_for_all_tenants()
        
        # Check that tenant2 is not in results
        self.assertIn(self.tenant.id, results)
        self.assertNotIn(self.tenant2.id, results)
