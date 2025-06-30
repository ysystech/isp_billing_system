"""
Comprehensive tests for tenant isolation across the system.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.utils.test_base import TenantTestCase
from apps.tenants.models import Tenant
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.routers.models import Router
from apps.subscriptions.models import SubscriptionPlan
from apps.lcp.models import LCP
from apps.tickets.models import Ticket
from apps.roles.models import Role

User = get_user_model()


class TenantDataIsolationTest(TenantTestCase):
    """Test that data is properly isolated between tenants."""
    
    def setUp(self):
        """Set up test data for both tenants."""
        super().setUp()
        
        # Create barangays first
        self.barangay1 = Barangay.objects.create(
            name="Barangay Test 1",
            tenant=self.tenant
        )
        
        self.barangay2 = Barangay.objects.create(
            name="Barangay Test 2",
            tenant=self.other_tenant
        )
        
        # Create data for primary tenant
        self.customer1 = Customer.objects.create(
            first_name="Customer",
            last_name="One",
            email="customer1@example.com",
            phone_primary="+639123456789",
            street_address="123 Main St",
            barangay=self.barangay1,
            tenant=self.tenant
        )
        
        self.router1 = Router.objects.create(
            brand="TP-Link",
            model="Archer C7",
            serial_number="SN123456",
            mac_address="00:11:22:33:44:55",
            tenant=self.tenant
        )
        
        self.plan1 = SubscriptionPlan.objects.create(
            name="Plan 1",
            speed=10,
            price=1000,
            day_count=30,
            tenant=self.tenant
        )
        
        # Create data for other tenant
        self.customer2 = Customer.objects.create(
            first_name="Customer",
            last_name="Two",
            email="customer2@example.com",
            phone_primary="+639987654321",
            street_address="456 Other St",
            barangay=self.barangay2,
            tenant=self.other_tenant
        )
        
        self.router2 = Router.objects.create(
            brand="Mikrotik",
            model="RB750",
            serial_number="SN789012",
            mac_address="AA:BB:CC:DD:EE:FF",
            tenant=self.other_tenant
        )
        
        self.plan2 = SubscriptionPlan.objects.create(
            name="Plan 2",
            speed=20,
            price=2000,
            day_count=30,
            tenant=self.other_tenant
        )
    
    def test_customer_isolation(self):
        """Test that customers are isolated by tenant."""
        # Filter by tenant 1
        tenant1_customers = Customer.objects.filter(tenant=self.tenant)
        self.assertEqual(tenant1_customers.count(), 1)
        self.assertIn(self.customer1, tenant1_customers)
        self.assertNotIn(self.customer2, tenant1_customers)
        
        # Filter by tenant 2
        tenant2_customers = Customer.objects.filter(tenant=self.other_tenant)
        self.assertEqual(tenant2_customers.count(), 1)
        self.assertIn(self.customer2, tenant2_customers)
        self.assertNotIn(self.customer1, tenant2_customers)
    
    def test_barangay_isolation(self):
        """Test that barangays are isolated by tenant."""
        # Each tenant can have their own barangays
        tenant1_barangays = Barangay.objects.filter(tenant=self.tenant)
        self.assertEqual(tenant1_barangays.count(), 1)
        self.assertIn(self.barangay1, tenant1_barangays)
        self.assertNotIn(self.barangay2, tenant1_barangays)
    
    def test_router_isolation(self):
        """Test that routers are isolated by tenant."""
        tenant1_routers = Router.objects.filter(tenant=self.tenant)
        self.assertEqual(tenant1_routers.count(), 1)
        self.assertIn(self.router1, tenant1_routers)
        self.assertNotIn(self.router2, tenant1_routers)
    
    def test_subscription_plan_isolation(self):
        """Test that subscription plans are isolated by tenant."""
        tenant1_plans = SubscriptionPlan.objects.filter(tenant=self.tenant)
        self.assertEqual(tenant1_plans.count(), 1)
        self.assertIn(self.plan1, tenant1_plans)
        self.assertNotIn(self.plan2, tenant1_plans)
    
    def test_duplicate_names_across_tenants(self):
        """Test that tenants can have resources with same names."""
        # Create duplicate router model in different tenant
        duplicate_router = Router.objects.create(
            brand="TP-Link",
            model="Archer C7",  # Same model as router1
            serial_number="SN345678",
            mac_address="11:22:33:44:55:66",
            tenant=self.other_tenant
        )
        
        # Both should exist
        self.assertEqual(Router.objects.filter(model="Archer C7").count(), 2)
        
        # But isolated by tenant
        tenant1_routers = Router.objects.filter(model="Archer C7", tenant=self.tenant)
        self.assertEqual(tenant1_routers.count(), 1)
        self.assertEqual(tenant1_routers.first(), self.router1)


class TenantViewIsolationTest(TenantTestCase):
    """Test that views properly isolate data by tenant."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        
        # Create barangays first
        self.barangay1 = Barangay.objects.create(
            name="Barangay 1",
            tenant=self.tenant
        )
        
        self.barangay2 = Barangay.objects.create(
            name="Barangay 2",
            tenant=self.other_tenant
        )
        
        # Create customers for both tenants
        self.customer1 = Customer.objects.create(
            first_name="Tenant1",
            last_name="Customer",
            email="t1customer@example.com",
            phone_primary="+639123456789",
            street_address="123 Main St",
            barangay=self.barangay1,
            tenant=self.tenant
        )
        
        self.customer2 = Customer.objects.create(
            first_name="Tenant2",
            last_name="Customer",
            email="t2customer@example.com",
            phone_primary="+639987654321",
            street_address="456 Other St",
            barangay=self.barangay2,
            tenant=self.other_tenant
        )
    
    def test_customer_list_view_isolation(self):
        """Test that customer list only shows tenant's customers."""
        # Login as tenant 1 owner (bypasses permissions)
        self.client.login(username='testowner', password='testpass123')
        
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should only see tenant 1's customer
        self.assertContains(response, self.customer1.first_name)
        self.assertNotContains(response, self.customer2.first_name)
    
    def test_cross_tenant_access_denied(self):
        """Test that users cannot access other tenant's data."""
        # Login as tenant 1 owner
        self.client.login(username='testowner', password='testpass123')
        
        # Try to access tenant 2's customer detail
        response = self.client.get(
            reverse('customers:customer_detail', kwargs={'pk': self.customer2.pk})
        )
        self.assertEqual(response.status_code, 404)  # Should not find it
    
    def test_tenant_owner_isolation(self):
        """Test that tenant owners are still isolated to their tenant."""
        # Login as tenant 1 owner
        self.client.login(username='testowner', password='testpass123')
        
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        
        # Even owners should only see their tenant's data
        self.assertContains(response, self.customer1.first_name)
        self.assertNotContains(response, self.customer2.first_name)


class TenantPermissionTest(TenantTestCase):
    """Test tenant-aware permissions."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.client = Client()
        
        # Create roles for both tenants
        self.role1 = Role.objects.create(
            name="Manager T1",
            description="Manager role",
            tenant=self.tenant
        )
        
        self.role2 = Role.objects.create(
            name="Manager T2",
            description="Manager role in other tenant",
            tenant=self.other_tenant
        )
    
    def test_tenant_owner_permission_bypass(self):
        """Test that tenant owners bypass permission checks."""
        # Login as tenant owner
        self.client.login(username='testowner', password='testpass123')
        
        # Should be able to access any view without specific permissions
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('roles:role_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_regular_user_needs_permissions(self):
        """Test that regular users need proper permissions."""
        # Login as regular user without permissions
        self.client.login(username='testuser', password='testpass123')
        
        # Should be denied access to role management
        response = self.client.get(reverse('roles:role_list'))
        self.assertIn(response.status_code, [302, 403])  # Redirect or forbidden
    
    def test_role_isolation(self):
        """Test that roles are isolated by tenant."""
        self.client.login(username='testowner', password='testpass123')
        
        response = self.client.get(reverse('roles:role_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should only see tenant 1's role
        self.assertContains(response, self.role1.name)
        # Should not see tenant 2's role
        self.assertNotContains(response, self.role2.name)
