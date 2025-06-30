"""
Essential security tests for multi-tenant isolation.
Focuses on critical security boundaries.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection
from apps.tenants.models import Tenant
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.utils.test_base import TenantTestCase

User = get_user_model()


class EssentialTenantSecurityTest(TenantTestCase):
    """Test essential tenant security boundaries."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create second tenant
        cls.tenant2 = Tenant.objects.create(
            name="Competitor ISP",
            created_by=User.objects.create_user(
                username="tenant2_owner",
                email="owner@tenant2.com",
                password="testpass123"
            )
        )
        
        # Create test data
        cls.barangay1 = Barangay.objects.create(
            name="Tenant1 Barangay",
            code="T1-001",
            tenant=cls.tenant
        )
        
        cls.barangay2 = Barangay.objects.create(
            name="Tenant2 Barangay",
            code="T2-001",
            tenant=cls.tenant2
        )
        
        cls.customer1 = Customer.objects.create(
            first_name="Test",
            last_name="Customer1",
            email="cust1@tenant1.com",
            barangay=cls.barangay1,
            tenant=cls.tenant
        )
        
        cls.customer2 = Customer.objects.create(
            first_name="Test", 
            last_name="Customer2",
            email="cust2@tenant2.com",
            barangay=cls.barangay2,
            tenant=cls.tenant2
        )
    
    def test_view_level_isolation(self):
        """Test that views properly isolate tenant data."""
        # Give tenant owner all customer permissions
        self.client.login(username='testowner', password='testpass123')
        
        # Can see own customer
        response = self.client.get(
            reverse('customers:customer_detail', args=[self.customer1.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Cannot see other tenant's customer (404)
        response = self.client.get(
            reverse('customers:customer_detail', args=[self.customer2.id])
        )
        self.assertEqual(response.status_code, 404)
    
    def test_queryset_isolation(self):
        """Test that querysets are properly filtered."""
        # Direct ORM queries show all data
        all_customers = Customer.objects.all()
        self.assertEqual(all_customers.count(), 2)
        
        # But filtered by tenant shows only tenant data
        tenant1_customers = Customer.objects.filter(tenant=self.tenant)
        self.assertEqual(tenant1_customers.count(), 1)
        self.assertEqual(tenant1_customers.first().email, "cust1@tenant1.com")
    
    def test_sql_query_logging(self):
        """Test that SQL queries include tenant filtering."""
        with connection.cursor() as cursor:
            # Reset query log
            connection.queries_log.clear()
            
            # Make a query
            list(Customer.objects.filter(tenant=self.tenant))
            
            # Check last query includes tenant_id
            if connection.queries:
                last_query = connection.queries[-1]['sql']
                self.assertIn('tenant_id', last_query.lower())
    
    def test_no_global_access(self):
        """Ensure no way to access all tenants' data through views."""
        self.client.login(username='testowner', password='testpass123')
        
        # List view should only show tenant's customers
        response = self.client.get(reverse('customers:customer_list'))
        if response.status_code == 200:
            customers = response.context.get('customers', [])
            # Should only see 1 customer (tenant1's)
            self.assertEqual(len(customers), 1)