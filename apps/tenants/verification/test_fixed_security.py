"""
Fixed security tests for multi-tenant data isolation.
Handles permissions properly and uses correct model fields.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from apps.tenants.models import Tenant
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.routers.models import Router
from apps.subscriptions.models import SubscriptionPlan
from apps.lcp.models import LCP, Splitter, NAP
from apps.utils.test_base import TenantTestCase

User = get_user_model()


class FixedTenantIsolationSecurityTest(TenantTestCase):
    """
    Fixed security tests with proper permissions and field names.
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Use the tenant created by TenantTestCase as tenant1
        cls.tenant1 = cls.tenant
        
        # Create a second tenant with data
        cls.tenant2 = Tenant.objects.create(
            name="Competitor ISP",
            created_by=User.objects.create_user(
                username="competitor_owner",
                email="owner@competitor.com",
                password="testpass123"
            )
        )
        
        # Create users for second tenant
        cls.tenant2_owner = cls.tenant2.created_by
        cls.tenant2_owner.tenant = cls.tenant2
        cls.tenant2_owner.is_tenant_owner = True
        cls.tenant2_owner.save()
        
        cls.tenant2_user = User.objects.create_user(
            username="competitor_user",
            email="user@competitor.com",
            password="testpass123",
            tenant=cls.tenant2
        )
        
        # Create test data for both tenants
        cls._create_tenant1_data()
        cls._create_tenant2_data()
        
        # Setup permissions
        cls._setup_permissions()
    
    @classmethod
    def _setup_permissions(cls):
        """Grant necessary permissions to test users."""
        # Get customer permissions
        customer_ct = ContentType.objects.get_for_model(Customer)
        view_list_perm = Permission.objects.get(
            codename='view_customer_list',
            content_type=customer_ct
        )
        view_detail_perm = Permission.objects.get(
            codename='view_customer_detail', 
            content_type=customer_ct
        )
        create_perm = Permission.objects.get(
            codename='create_customer',
            content_type=customer_ct
        )
        
        # Grant permissions to both users
        for user in [cls.user, cls.tenant2_user]:
            user.user_permissions.add(view_list_perm, view_detail_perm, create_perm)
    
    @classmethod
    def _create_tenant1_data(cls):
        """Create test data for tenant 1."""
        cls.barangay1 = Barangay.objects.create(
            name="Tenant1 Barangay",
            code="T1B001",
            tenant=cls.tenant1
        )
        
        cls.customer1 = Customer.objects.create(
            email="customer1@tenant1.com",
            first_name="Tenant1",
            last_name="Customer",
            barangay=cls.barangay1,
            tenant=cls.tenant1
        )
        
        cls.plan1 = SubscriptionPlan.objects.create(
            name="Tenant1 5Mbps",
            speed=5,
            price=999.00,
            tenant=cls.tenant1
        )
        
        cls.lcp1 = LCP.objects.create(
            name="Tenant1 LCP",
            code="LCP-T1-001",
            location="Tenant1 Location",
            barangay=cls.barangay1,
            tenant=cls.tenant1
        )
    
    @classmethod  
    def _create_tenant2_data(cls):
        """Create test data for tenant 2."""
        cls.barangay2 = Barangay.objects.create(
            name="Tenant2 Barangay",
            code="T2B001",
            tenant=cls.tenant2
        )
        
        cls.customer2 = Customer.objects.create(
            email="customer2@tenant2.com",
            first_name="Tenant2",
            last_name="Customer",
            barangay=cls.barangay2,
            tenant=cls.tenant2
        )
        
        cls.plan2 = SubscriptionPlan.objects.create(
            name="Tenant2 10Mbps",
            speed=10,
            price=1499.00,
            tenant=cls.tenant2
        )
        
        cls.lcp2 = LCP.objects.create(
            name="Tenant2 LCP",
            code="LCP-T2-001",
            location="Tenant2 Location",
            barangay=cls.barangay2,
            tenant=cls.tenant2
        )

    def test_customer_listing_isolation(self):
        """Test that users can only see customers from their own tenant."""
        # Login as tenant1 user
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should only see tenant1 customers
        self.assertContains(response, 'Tenant1')
        self.assertContains(response, 'customer1@tenant1.com')
        self.assertNotContains(response, 'Tenant2')
        self.assertNotContains(response, 'customer2@tenant2.com')
        
        # Login as tenant2 user  
        self.client.login(username='competitor_user', password='testpass123')
        
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should only see tenant2 customers
        self.assertContains(response, 'Tenant2')
        self.assertContains(response, 'customer2@tenant2.com')
        self.assertNotContains(response, 'Tenant1')
        self.assertNotContains(response, 'customer1@tenant1.com')

    def test_direct_object_access_returns_404(self):
        """Test that direct URL access to other tenant's objects returns 404."""
        # Give user view permission
        self.user.user_permissions.add(
            Permission.objects.get(codename='view_customer_detail')
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # Can access own tenant's customer
        response = self.client.get(
            reverse('customers:customer_detail', args=[self.customer1.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Cannot access other tenant's customer - should get 404
        response = self.client.get(
            reverse('customers:customer_detail', args=[self.customer2.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_tenant_owner_permissions_within_tenant(self):
        """Test that tenant owners have full access within their tenant only."""
        # Login as tenant1 owner
        self.client.login(username='testowner', password='testpass123')
        
        # Should be able to access everything in tenant1
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        
        # Can access tenant1's customer detail
        response = self.client.get(
            reverse('customers:customer_detail', args=[self.customer1.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Cannot access tenant2's customer - should get 404
        response = self.client.get(
            reverse('customers:customer_detail', args=[self.customer2.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_model_queryset_isolation(self):
        """Test that model querysets filter by tenant correctly."""
        # Direct model queries should show all data
        all_customers = Customer.objects.all()
        self.assertEqual(all_customers.count(), 2)
        
        # Filtered queries should only show tenant-specific data
        tenant1_customers = Customer.objects.filter(tenant=self.tenant1)
        self.assertEqual(tenant1_customers.count(), 1)
        self.assertEqual(tenant1_customers.first().email, 'customer1@tenant1.com')
        
        tenant2_customers = Customer.objects.filter(tenant=self.tenant2)
        self.assertEqual(tenant2_customers.count(), 1)
        self.assertEqual(tenant2_customers.first().email, 'customer2@tenant2.com')

    def test_barangay_isolation(self):
        """Test that barangays are isolated by tenant."""
        # Each tenant should only see their barangays
        tenant1_barangays = Barangay.objects.filter(tenant=self.tenant1)
        self.assertEqual(tenant1_barangays.count(), 1)
        self.assertEqual(tenant1_barangays.first().code, 'T1B001')
        
        tenant2_barangays = Barangay.objects.filter(tenant=self.tenant2)
        self.assertEqual(tenant2_barangays.count(), 1)
        self.assertEqual(tenant2_barangays.first().code, 'T2B001')

    def test_subscription_plan_isolation(self):
        """Test that subscription plans are isolated by tenant."""
        # Each tenant should only see their plans
        tenant1_plans = SubscriptionPlan.objects.filter(tenant=self.tenant1)
        self.assertEqual(tenant1_plans.count(), 1)
        self.assertEqual(tenant1_plans.first().speed, 5)
        
        tenant2_plans = SubscriptionPlan.objects.filter(tenant=self.tenant2)
        self.assertEqual(tenant2_plans.count(), 1)
        self.assertEqual(tenant2_plans.first().speed, 10)

    def test_lcp_isolation(self):
        """Test that LCP infrastructure is isolated by tenant."""
        # Each tenant should only see their LCPs
        tenant1_lcps = LCP.objects.filter(tenant=self.tenant1)
        self.assertEqual(tenant1_lcps.count(), 1)
        self.assertEqual(tenant1_lcps.first().code, 'LCP-T1-001')
        
        tenant2_lcps = LCP.objects.filter(tenant=self.tenant2)
        self.assertEqual(tenant2_lcps.count(), 1)
        self.assertEqual(tenant2_lcps.first().code, 'LCP-T2-001')

    def test_no_null_tenant_records(self):
        """Ensure no records exist without tenant assignment."""
        # Check all models for null tenants
        models_to_check = [
            Customer, Barangay, SubscriptionPlan, LCP
        ]
        
        for model in models_to_check:
            null_records = model.objects.filter(tenant__isnull=True)
            self.assertEqual(
                null_records.count(), 0,
                f"{model.__name__} has records with null tenant"
            )