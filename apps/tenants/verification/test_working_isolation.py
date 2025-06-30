"""
Working security tests for multi-tenant data isolation.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from apps.tenants.models import Tenant
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.utils.test_base import TenantTestCase

User = get_user_model()


class WorkingTenantIsolationTest(TenantTestCase):
    """Working tests that verify core tenant isolation."""
    
    def setUp(self):
        super().setUp()
        
        # Create second tenant
        self.tenant2 = Tenant.objects.create(
            name="Competitor ISP",
            created_by=User.objects.create_user(
                username="tenant2_owner",
                email="owner@tenant2.com", 
                password="testpass123"
            )
        )
        
        # Setup tenant2 owner
        self.tenant2.created_by.tenant = self.tenant2
        self.tenant2.created_by.is_tenant_owner = True
        self.tenant2.created_by.save()
        
        # Create test data
        self.barangay1 = Barangay.objects.create(
            name="Barangay 1",
            code="B001",
            tenant=self.tenant
        )
        
        self.barangay2 = Barangay.objects.create(
            name="Barangay 2", 
            code="B002",
            tenant=self.tenant2
        )
        
        self.customer1 = Customer.objects.create(
            first_name="Customer",
            last_name="One",
            email="c1@tenant1.com",
            barangay=self.barangay1,
            tenant=self.tenant
        )
        
        self.customer2 = Customer.objects.create(
            first_name="Customer",
            last_name="Two",
            email="c2@tenant2.com",
            barangay=self.barangay2,
            tenant=self.tenant2
        )
        
        # Grant permissions to test user
        customer_ct = ContentType.objects.get_for_model(Customer)
        perms = Permission.objects.filter(
            content_type=customer_ct,
            codename__in=['view_customer_list', 'view_customer_detail']
        )
        self.user.user_permissions.add(*perms)

    def test_basic_isolation(self):
        """Test basic tenant isolation works."""
        # Each tenant has correct data
        self.assertEqual(Customer.objects.filter(tenant=self.tenant).count(), 1)
        self.assertEqual(Customer.objects.filter(tenant=self.tenant2).count(), 1)
        
        # Total is sum of both
        self.assertEqual(Customer.objects.all().count(), 2)

    def test_customer_list_view_isolation(self):
        """Test customer list only shows current tenant's data."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should see tenant1 customer
        self.assertContains(response, 'c1@tenant1.com')
        # Should NOT see tenant2 customer
        self.assertNotContains(response, 'c2@tenant2.com')

    def test_cross_tenant_404(self):
        """Test accessing other tenant's data returns 404."""
        self.client.login(username='testuser', password='testpass123')
        
        # Can access own customer
        response = self.client.get(
            reverse('customers:customer_detail', args=[self.customer1.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Cannot access other tenant's customer
        response = self.client.get(
            reverse('customers:customer_detail', args=[self.customer2.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_tenant_owner_isolation(self):
        """Test tenant owners are still isolated to their tenant."""
        self.client.login(username='testowner', password='testpass123')
        
        # Owner can access their tenant's data without specific permissions
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        
        # But still cannot access other tenant's specific records
        response = self.client.get(
            reverse('customers:customer_detail', args=[self.customer2.id])
        )
        self.assertEqual(response.status_code, 404)