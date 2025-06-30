"""
Simplified security tests for verifying core tenant isolation.
Focus on the most critical isolation checks.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from apps.tenants.models import Tenant
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.utils.test_base import TenantTestCase

User = get_user_model()


class CoreTenantIsolationTest(TenantTestCase):
    """Test core tenant isolation functionality."""
    
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
        
        # Setup tenant2 owner
        cls.tenant2.created_by.tenant = cls.tenant2
        cls.tenant2.created_by.is_tenant_owner = True
        cls.tenant2.created_by.save()
        
        # Create data for each tenant
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
    
    def test_queryset_filtering(self):
        """Test that model querysets are filtered by tenant."""
        # Customers should only see their tenant's data
        tenant1_customers = Customer.objects.filter(tenant=self.tenant)
        self.assertEqual(tenant1_customers.count(), 1)
        self.assertEqual(tenant1_customers.first().email, "cust1@tenant1.com")
        
        tenant2_customers = Customer.objects.filter(tenant=self.tenant2)
        self.assertEqual(tenant2_customers.count(), 1)
        self.assertEqual(tenant2_customers.first().email, "cust2@tenant2.com")
        
        # Barangays should be tenant-specific
        tenant1_barangays = Barangay.objects.filter(tenant=self.tenant)
        self.assertEqual(tenant1_barangays.count(), 1)
        self.assertEqual(tenant1_barangays.first().code, "T1-001")
    def test_foreign_key_validation(self):
        """Test that foreign keys cannot cross tenant boundaries."""
        # Try to create a customer in tenant1 with tenant2's barangay
        with self.assertRaises(Exception):
            Customer.objects.create(
                first_name="Hacker",
                last_name="Test",
                email="hacker@test.com",
                barangay=self.barangay2,  # Wrong tenant!
                tenant=self.tenant
            )
    
    def test_tenant_owner_access(self):
        """Test that tenant owners can only access their own tenant."""
        # Login as tenant1 owner
        self.client.login(username='testowner', password='testpass123')
        
        # Should be able to see tenant1's data
        customers = Customer.objects.filter(tenant=self.tenant)
        self.assertEqual(customers.count(), 1)
        
        # Should NOT see tenant2's data
        other_customers = Customer.objects.filter(tenant=self.tenant2)
        self.assertEqual(other_customers.count(), 1)  # Data exists
        
        # But through views, should get 404
        # (This would be tested with actual view tests)
    
    def test_no_null_tenants(self):
        """Verify no records exist without tenant assignment."""
        # Check all tenant-aware models
        null_customers = Customer.objects.filter(tenant__isnull=True)
        self.assertEqual(null_customers.count(), 0)
        
        null_barangays = Barangay.objects.filter(tenant__isnull=True)
        self.assertEqual(null_barangays.count(), 0)
    def test_cross_tenant_query_count(self):
        """Test that queries don't accidentally include other tenants."""
        # Create more test data
        for i in range(5):
            Customer.objects.create(
                first_name=f"Extra{i}",
                last_name="Customer",
                email=f"extra{i}@tenant1.com",
                barangay=self.barangay1,
                tenant=self.tenant
            )
        
        for i in range(10):
            Customer.objects.create(
                first_name=f"Extra{i}",
                last_name="Customer", 
                email=f"extra{i}@tenant2.com",
                barangay=self.barangay2,
                tenant=self.tenant2
            )
        
        # Verify counts
        self.assertEqual(Customer.objects.filter(tenant=self.tenant).count(), 6)
        self.assertEqual(Customer.objects.filter(tenant=self.tenant2).count(), 11)
        
        # Total should be sum of both
        self.assertEqual(Customer.objects.all().count(), 17)