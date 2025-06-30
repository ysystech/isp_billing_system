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
        
        # Create a second tenant for isolation testing
        self.tenant2 = Tenant.objects.create(
            name="Other ISP Company",
            is_active=True
        )        
        # Create test data for tenant 1
        self.plan1 = SubscriptionPlan.objects.create(
            tenant=self.tenant,
            name="Basic Plan",
            price=500.00,
            validity_days=30
        )
        
        self.customer1 = Customer.objects.create(
            tenant=self.tenant,
            account_number="ACC001",
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        self.installation1 = CustomerInstallation.objects.create(
            tenant=self.tenant,
            customer=self.customer1,
            olt="OLT1",
            onu_serial="SN12345",
            installation_date=timezone.now().date(),
            status='ACTIVE'
        )
        
        # Create test data for tenant 2
        self.plan2 = SubscriptionPlan.objects.create(
            tenant=self.tenant2,
            name="Premium Plan",
            price=1000.00,
            validity_days=30
        )        
        self.customer2 = Customer.objects.create(
            tenant=self.tenant2,
            account_number="ACC002",
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com"
        )
        
        self.installation2 = CustomerInstallation.objects.create(
            tenant=self.tenant2,
            customer=self.customer2,
            olt="OLT2",
            onu_serial="SN67890",
            installation_date=timezone.now().date(),
            status='ACTIVE'
        )

    def test_update_expired_subscriptions_tenant_isolation(self):
        """Test that expired subscription updates only affect the current tenant."""
        # Create expired subscription for tenant 1
        expired_sub1 = CustomerSubscription.objects.create(
            tenant=self.tenant,
            customer_installation=self.installation1,
            subscription_plan=self.plan1,
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=1),
            status='ACTIVE'
        )
        
        # Create expired subscription for tenant 2
        expired_sub2 = CustomerSubscription.objects.create(            tenant=self.tenant2,
            customer_installation=self.installation2,
            subscription_plan=self.plan2,
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=1),
            status='ACTIVE'
        )
        
        # Run task for tenant 1 only
        with tenant_context(self.tenant):
            result = update_expired_subscriptions.run()
        
        # Check that only tenant 1's subscription was updated
        expired_sub1.refresh_from_db()
        expired_sub2.refresh_from_db()
        
        self.assertEqual(expired_sub1.status, 'EXPIRED')
        self.assertEqual(expired_sub2.status, 'ACTIVE')  # Should remain active
        
        # Check installation status
        self.installation1.refresh_from_db()
        self.assertEqual(self.installation1.status, 'INACTIVE')
        
    def test_send_expiration_reminders_tenant_isolation(self):
        """Test that expiration reminders only process current tenant's data."""
        # Create soon-to-expire subscription for tenant 1
        expiring_sub1 = CustomerSubscription.objects.create(
            tenant=self.tenant,
            customer_installation=self.installation1,
            subscription_plan=self.plan1,            start_date=timezone.now() - timedelta(days=28),
            end_date=timezone.now() + timedelta(days=2),
            status='ACTIVE'
        )
        
        # Create soon-to-expire subscription for tenant 2
        expiring_sub2 = CustomerSubscription.objects.create(
            tenant=self.tenant2,
            customer_installation=self.installation2,
            subscription_plan=self.plan2,
            start_date=timezone.now() - timedelta(days=28),
            end_date=timezone.now() + timedelta(days=2),
            status='ACTIVE'
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
        CustomerSubscription.objects.create(
            tenant=self.tenant,
            customer_installation=self.installation1,
            subscription_plan=self.plan1,            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=1),
            status='ACTIVE'
        )
        
        CustomerSubscription.objects.create(
            tenant=self.tenant2,
            customer_installation=self.installation2,
            subscription_plan=self.plan2,
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=1),
            status='ACTIVE'
        )
        
        # Run task for all tenants
        results = update_expired_subscriptions.run_for_all_tenants()
        
        # Should have results for both tenants
        self.assertEqual(len(results), 2)
        self.assertIn(self.tenant.id, results)
        self.assertIn(self.tenant2.id, results)
        
        # Check both subscriptions were updated
        self.assertEqual(
            CustomerSubscription.objects.filter(status='EXPIRED').count(),
            2
        )
        
    def test_inactive_tenant_skipped(self):
        """Test that inactive tenants are skipped in processing."""
        # Make tenant 2 inactive        self.tenant2.is_active = False
        self.tenant2.save()
        
        # Create expired subscriptions for both tenants
        CustomerSubscription.objects.create(
            tenant=self.tenant,
            customer_installation=self.installation1,
            subscription_plan=self.plan1,
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=1),
            status='ACTIVE'
        )
        
        CustomerSubscription.objects.create(
            tenant=self.tenant2,
            customer_installation=self.installation2,
            subscription_plan=self.plan2,
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=1),
            status='ACTIVE'
        )
        
        # Run task for all tenants
        results = update_expired_subscriptions.run_for_all_tenants()
        
        # Should only have results for active tenant
        self.assertEqual(len(results), 1)
        self.assertIn(self.tenant.id, results)
        self.assertNotIn(self.tenant2.id, results)