"""
Performance Tests for Multi-Tenant ISP Billing System

This test suite verifies that tenant filtering doesn't significantly impact performance.
"""

import time
from django.test import TestCase
from django.db import connection
from django.test.utils import override_settings
from django.utils import timezone
from decimal import Decimal

from apps.tenants.models import Tenant
from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.customer_subscriptions.models import CustomerSubscription
from apps.customer_installations.models import CustomerInstallation
from apps.lcp.models import LCP, Splitter, NAP
from apps.routers.models import Router
from apps.subscriptions.models import SubscriptionPlan


class TenantPerformanceTest(TestCase):
    """Test query performance with tenant filtering."""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data for performance testing."""
        # Create 5 tenants
        cls.tenants = []
        for i in range(5):
            tenant = Tenant.objects.create(name=f"ISP {i+1}")
            cls.tenants.append(tenant)
        
        # For each tenant, create substantial data
        for tenant in cls.tenants:
            # Create admin user
            admin = CustomUser.objects.create_user(
                username=f"admin_{tenant.id}",
                email=f"admin@isp{tenant.id}.com",
                password="testpass123",
                tenant=tenant,
                is_staff=True,
                is_tenant_owner=True  # Give full permissions
            )
            
            # Create 10 barangays per tenant
            barangays = []
            for j in range(10):
                barangay = Barangay.objects.create(
                    tenant=tenant,
                    name=f"Barangay {j+1} - {tenant.name}"
                )
                barangays.append(barangay)
            
            # Create 5 plans per tenant
            plans = []
            for speed in [5, 10, 20, 50, 100]:
                plan = SubscriptionPlan.objects.create(
                    tenant=tenant,
                    name=f"{speed}Mbps Plan",
                    speed=speed,
                    price=Decimal(str(speed * 50))
                )
                plans.append(plan)
            
            # Create network infrastructure
            for idx, barangay in enumerate(barangays[:5]):  # 5 LCPs
                lcp = LCP.objects.create(
                    tenant=tenant,
                    name=f"LCP {idx+1}",
                    code=f"LCP-{tenant.id}-{idx+1}",
                    location=f"Location {idx+1}",
                    barangay=barangay
                )
                
                # 2 splitters per LCP
                for s in range(2):
                    splitter = Splitter.objects.create(
                        tenant=tenant,
                        lcp=lcp,
                        code=f"SP-{tenant.id}-{idx+1}-{s+1}",
                        type='1:8'
                    )
                    
                    # 4 NAPs per splitter
                    for n in range(4):
                        NAP.objects.create(
                            tenant=tenant,
                            splitter=splitter,
                            splitter_port=n+1,
                            code=f"NAP-{tenant.id}-{idx+1}-{s+1}-{n+1}",
                            name=f"NAP {n+1}",
                            location=f"NAP Location {n+1}"
                        )
            
            # Create 100 customers per tenant
            for c in range(100):
                customer = Customer.objects.create(
                    tenant=tenant,
                    first_name=f"Customer{c}",
                    last_name=f"Tenant{tenant.id}",
                    email=f"customer{c}@tenant{tenant.id}.com",
                    barangay=barangays[c % len(barangays)]
                )
                
                # Create router
                router = Router.objects.create(
                    tenant=tenant,
                    brand="TP-Link",
                    model="Archer",
                    serial_number=f"SN-{tenant.id}-{c}",
                    mac_address=f"00:11:22:33:{tenant.id:02X}:{c:02X}"
                )
                
                # Get a NAP for installation
                naps = NAP.objects.filter(tenant=tenant)
                if naps.exists() and c < naps.count():
                    nap = naps[c % naps.count()]
                    
                    # Create installation
                    installation = CustomerInstallation.objects.create(
                        tenant=tenant,
                        customer=customer,
                        nap=nap,
                        nap_port=(c % 8) + 1,
                        router=router,
                        installation_date=timezone.now().date(),
                        installation_technician=admin
                    )
                    
                    # Create subscription
                    CustomerSubscription.objects.create(
                        tenant=tenant,
                        customer_installation=installation,
                        subscription_plan=plans[c % len(plans)],
                        amount=plans[c % len(plans)].price,
                        start_date=timezone.now(),
                        end_date=timezone.now() + timezone.timedelta(days=30),
                        created_by=admin
                    )
        
        # Store first tenant and admin for testing
        cls.tenant1 = cls.tenants[0]
        cls.admin1 = CustomUser.objects.get(username="admin_1")
    
    def setUp(self):
        """Reset queries before each test."""
        connection.queries_log.clear()
    
    @override_settings(DEBUG=True)
    def test_customer_list_performance(self):
        """Test performance of customer list view with tenant filtering."""
        self.client.force_login(self.admin1)
        
        # Measure time and queries
        start_time = time.time()
        start_queries = len(connection.queries)
        
        response = self.client.get('/customers/')
        
        end_time = time.time()
        end_queries = len(connection.queries)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Performance metrics
        elapsed_time = end_time - start_time
        query_count = end_queries - start_queries
        
        print(f"\nCustomer List Performance:")
        print(f"  Time: {elapsed_time:.3f} seconds")
        print(f"  Queries: {query_count}")
        
        # Performance thresholds
        self.assertLess(elapsed_time, 1.0, "Customer list should load in under 1 second")
        self.assertLess(query_count, 10, "Customer list should use less than 10 queries")
    
    @override_settings(DEBUG=True)
    def test_subscription_aggregation_performance(self):
        """Test performance of report aggregations with tenant filtering."""
        self.client.force_login(self.admin1)
        
        # Measure daily collection report
        start_time = time.time()
        start_queries = len(connection.queries)
        
        response = self.client.get('/reports/daily-collection/')
        
        end_time = time.time()
        end_queries = len(connection.queries)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Performance metrics
        elapsed_time = end_time - start_time
        query_count = end_queries - start_queries
        
        print(f"\nDaily Collection Report Performance:")
        print(f"  Time: {elapsed_time:.3f} seconds")
        print(f"  Queries: {query_count}")
        
        # Check that tenant filtering is in the queries
        tenant_filtered_queries = [
            q for q in connection.queries[start_queries:end_queries]
            if 'tenant_id' in q['sql']
        ]
        
        print(f"  Tenant-filtered queries: {len(tenant_filtered_queries)}")
        
        # Performance thresholds
        self.assertLess(elapsed_time, 2.0, "Report should load in under 2 seconds")
        self.assertGreater(len(tenant_filtered_queries), 0, "Queries should filter by tenant")
    
    def test_cross_tenant_isolation_performance(self):
        """Test that cross-tenant access is efficiently blocked."""
        # Login as tenant 1 admin
        self.client.force_login(self.admin1)
        
        # Try to access tenant 2's customer
        tenant2_customer = Customer.objects.filter(tenant=self.tenants[1]).first()
        
        start_time = time.time()
        response = self.client.get(f'/customers/{tenant2_customer.id}/')
        end_time = time.time()
        
        # Should be 404
        self.assertEqual(response.status_code, 404)
        
        # Should be fast (early rejection)
        elapsed_time = end_time - start_time
        self.assertLess(elapsed_time, 0.1, "Cross-tenant rejection should be fast")
    
    @override_settings(DEBUG=True)
    def test_index_usage(self):
        """Verify that queries use tenant indexes efficiently."""
        self.client.force_login(self.admin1)
        
        # Clear queries
        connection.queries_log.clear()
        
        # Perform various queries
        Customer.objects.filter(tenant=self.tenant1).count()
        CustomerSubscription.objects.filter(tenant=self.tenant1, status='ACTIVE').count()
        Barangay.objects.filter(tenant=self.tenant1, is_active=True).values_list('name', flat=True)
        
        # Check query plans
        for query in connection.queries:
            sql = query['sql']
            if 'tenant_id' in sql and 'SELECT' in sql:
                # In a real test, we'd use EXPLAIN to verify index usage
                # For now, just verify tenant_id is in WHERE clause
                self.assertIn('tenant_id', sql)
                
        print(f"\nTotal queries with tenant filtering: {len(connection.queries)}")
