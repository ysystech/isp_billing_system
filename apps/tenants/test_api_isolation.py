"""
Tests for API endpoint tenant isolation.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import json

from apps.utils.test_base import TenantTestCase
from apps.tenants.models import Tenant
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.routers.models import Router
from apps.subscriptions.models import SubscriptionPlan
from apps.customer_installations.models import CustomerInstallation
from apps.lcp.models import LCP, Splitter, NAP

User = get_user_model()


class APITenantIsolationTest(TenantTestCase):
    """Test that API endpoints properly isolate data by tenant."""
    
    def setUp(self):
        """Set up test data for API tests."""
        super().setUp()
        self.api_client = APIClient()
        
        # Create barangays for both tenants
        self.barangay1 = Barangay.objects.create(
            name="API Test Barangay 1",
            tenant=self.tenant
        )
        
        self.barangay2 = Barangay.objects.create(
            name="API Test Barangay 2",
            tenant=self.other_tenant
        )
        
        # Create customers for both tenants
        self.customer1 = Customer.objects.create(
            first_name="API",
            last_name="Customer1",
            email="api1@example.com",
            phone_primary="+639123456789",
            street_address="123 API St",
            barangay=self.barangay1,
            latitude=8.4542,
            longitude=124.6319,
            tenant=self.tenant
        )
        
        self.customer2 = Customer.objects.create(
            first_name="API",
            last_name="Customer2",
            email="api2@example.com",
            phone_primary="+639987654321",
            street_address="456 API St",
            barangay=self.barangay2,
            latitude=8.4543,
            longitude=124.6320,
            tenant=self.other_tenant
        )
        
        # Create subscription plans
        self.plan1 = SubscriptionPlan.objects.create(
            name="API Plan 1",
            speed=10,
            price=1000,
            tenant=self.tenant
        )
        
        self.plan2 = SubscriptionPlan.objects.create(
            name="API Plan 2",
            speed=20,
            price=2000,
            tenant=self.other_tenant
        )
        
        # Create LCP infrastructure
        self.lcp1 = LCP.objects.create(
            name="API LCP 1",
            code="APILCP1",
            location="Test Location 1",
            barangay=self.barangay1,
            tenant=self.tenant
        )
        
        self.splitter1 = Splitter.objects.create(
            lcp=self.lcp1,
            code="APISPL1",
            type="1:8",
            tenant=self.tenant
        )
        
        self.nap1 = NAP.objects.create(
            splitter=self.splitter1,
            splitter_port=1,
            name="API NAP 1",
            code="APINAP1",
            location="Test NAP Location",
            port_capacity=8,
            tenant=self.tenant
        )
        
        # Create router for installation
        self.router1 = Router.objects.create(
            brand="Test Brand",
            model="Test Model",
            serial_number="APIRT001",
            mac_address="00:11:22:33:44:55",
            tenant=self.tenant
        )
        
        # Create installation
        self.installation1 = CustomerInstallation.objects.create(
            customer=self.customer1,
            router=self.router1,
            nap=self.nap1,
            nap_port=1,
            installation_technician=self.user,  # Use the test user as technician
            status="ACTIVE",
            tenant=self.tenant
        )
    
    def test_customer_coordinates_api_isolation(self):
        """Test that customer coordinates API only shows tenant's customers."""
        # Login as tenant 1 owner
        self.client.force_login(self.owner)
        
        response = self.client.get(reverse('customers:customer_coordinates_api'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['total'], 1)
        self.assertEqual(len(data['customers']), 1)
        self.assertEqual(data['customers'][0]['first_name'], 'API')
        self.assertEqual(data['customers'][0]['last_name'], 'Customer1')
        
        # Should not contain customer from other tenant
        customer_names = [f"{c['first_name']} {c['last_name']}" for c in data['customers']]
        self.assertNotIn('API Customer2', customer_names)
    
    # def test_dashboard_api_tenant_isolation(self):
    #     """Test that dashboard API stats are tenant-specific."""
    #     # Dashboard URLs are commented out in main urls.py
    #     pass
    
    def test_subscription_plan_price_api_isolation(self):
        """Test that plan price API only returns tenant's plans."""
        self.client.force_login(self.owner)
        
        # Try to get plan from own tenant
        response = self.client.get(
            reverse('customer_subscriptions:api_plan_price'),
            {'plan_id': self.plan1.pk}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'API Plan 1')
        self.assertEqual(data['price'], 1000.0)
        
        # Try to get plan from other tenant - should fail
        response = self.client.get(
            reverse('customer_subscriptions:api_plan_price'),
            {'plan_id': self.plan2.pk}
        )
        self.assertEqual(response.status_code, 404)
    
    def test_lcp_api_tenant_isolation(self):
        """Test that LCP APIs only return tenant's infrastructure."""
        self.client.force_login(self.owner)
        
        # Test LCP list API
        response = self.client.get(reverse('lcp:api_lcps'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'API LCP 1')
        
        # Test splitter API
        response = self.client.get(
            reverse('lcp:api_splitters', kwargs={'lcp_id': self.lcp1.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['code'], 'APISPL1')
        
        # Test NAP API
        response = self.client.get(
            reverse('lcp:api_naps', kwargs={'splitter_id': self.splitter1.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'API NAP 1')
    
    def test_nap_hierarchy_api_cross_tenant_blocked(self):
        """Test that NAP hierarchy API blocks cross-tenant access."""
        # Create NAP in other tenant
        lcp2 = LCP.objects.create(
            name="API LCP 2",
            code="APILCP2",
            location="Test Location 2",
            barangay=self.barangay2,
            tenant=self.other_tenant
        )
        
        splitter2 = Splitter.objects.create(
            lcp=lcp2,
            code="APISPL2",
            type="1:8",
            tenant=self.other_tenant
        )
        
        nap2 = NAP.objects.create(
            splitter=splitter2,
            splitter_port=1,
            name="API NAP 2",
            code="APINAP2",
            location="Test NAP Location 2",
            port_capacity=8,
            tenant=self.other_tenant
        )
        
        # Login as tenant 1 owner
        self.client.force_login(self.owner)
        
        # Try to access NAP from other tenant
        response = self.client.get(
            reverse('lcp:api_nap_hierarchy', kwargs={'nap_id': nap2.pk})
        )
        self.assertEqual(response.status_code, 404)
        
        # Should be able to access own NAP
        response = self.client.get(
            reverse('lcp:api_nap_hierarchy', kwargs={'nap_id': self.nap1.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['nap_name'], 'API NAP 1')
    
    def test_installation_nap_ports_api_isolation(self):
        """Test that NAP ports API respects tenant boundaries."""
        self.client.force_login(self.owner)
        
        # Get ports for own NAP
        response = self.client.get(
            reverse('customer_installations:get_nap_ports', kwargs={'nap_id': self.nap1.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Check that port 1 is occupied by our customer
        ports = data['ports']
        self.assertEqual(len(ports), 8)  # 8 port capacity
        self.assertFalse(ports[0]['available'])  # Port 1 is taken
        self.assertEqual(ports[0]['customer'], 'API Customer1')
        
        # Other ports should be available
        for i in range(1, 8):
            self.assertTrue(ports[i]['available'])
    
    def test_latest_subscription_api_isolation(self):
        """Test that latest subscription API respects tenant boundaries."""
        self.client.force_login(self.owner)
        
        # Try to get subscription for own installation
        response = self.client.get(
            reverse('customer_subscriptions:api_latest_subscription'),
            {'installation_id': self.installation1.pk}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['has_active'])  # No active subscription yet
        
        # Create router and installation in other tenant
        router2 = Router.objects.create(
            brand="Test Brand",
            model="Test Model",
            serial_number="APIRT002",
            mac_address="AA:BB:CC:DD:EE:FF",
            tenant=self.other_tenant
        )
        
        # Create infrastructure for other tenant's installation
        lcp2 = LCP.objects.create(
            name="Other LCP",
            code="OTHERLCP",
            location="Other Location",
            barangay=self.barangay2,
            tenant=self.other_tenant
        )
        
        splitter2 = Splitter.objects.create(
            lcp=lcp2,
            code="OTHERSPL",
            type="1:8",
            tenant=self.other_tenant
        )
        
        nap2 = NAP.objects.create(
            splitter=splitter2,
            splitter_port=1,
            name="Other NAP",
            code="OTHERNAP",
            location="Other NAP Location",
            port_capacity=8,
            tenant=self.other_tenant
        )
        
        installation2 = CustomerInstallation.objects.create(
            customer=self.customer2,
            router=router2,
            nap=nap2,
            nap_port=1,
            installation_technician=self.other_user,  # Use other tenant's user
            status="ACTIVE",
            tenant=self.other_tenant
        )
        
        # Try to access other tenant's installation
        response = self.client.get(
            reverse('customer_subscriptions:api_latest_subscription'),
            {'installation_id': installation2.pk}
        )
        self.assertEqual(response.status_code, 404)
    
    def test_calculate_preview_api_isolation(self):
        """Test that calculate preview API respects tenant boundaries."""
        self.client.force_login(self.owner)
        
        # Calculate for own plan
        response = self.client.post(
            reverse('customer_subscriptions:api_calculate_preview'),
            data=json.dumps({
                'plan_id': self.plan1.pk,
                'amount': 1000,
                'subscription_type': 'one_month'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['amount'], 1000.0)
        
        # Try to calculate for other tenant's plan
        response = self.client.post(
            reverse('customer_subscriptions:api_calculate_preview'),
            data=json.dumps({
                'plan_id': self.plan2.pk,
                'amount': 2000,
                'subscription_type': 'one_month'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
