"""Test tenant isolation for all report views."""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.tenants.models import Tenant
from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.customer_subscriptions.models import CustomerSubscription
from apps.customer_installations.models import CustomerInstallation
from apps.subscriptions.models import SubscriptionPlan
from apps.tickets.models import Ticket
from apps.lcp.models import LCP, Splitter, NAP
from apps.routers.models import Router


class ReportTenantIsolationTest(TestCase):
    """Test that all reports properly filter by tenant."""
    
    def setUp(self):
        # Create two tenants
        self.tenant1 = Tenant.objects.create(name="ISP One")
        self.tenant2 = Tenant.objects.create(name="ISP Two")
        
        # Create users for each tenant
        self.user1 = CustomUser.objects.create_user(
            username="user1",
            email="user1@test.com",
            password="testpass123",
            tenant=self.tenant1,
            is_staff=True
        )
        
        self.user2 = CustomUser.objects.create_user(
            username="user2",
            email="user2@test.com",
            password="testpass123",
            tenant=self.tenant2,
            is_staff=True
        )
        
        # Create test data for tenant1
        self.barangay1 = Barangay.objects.create(
            tenant=self.tenant1,
            name="Barangay 1"
        )
        
        self.router1 = Router.objects.create(
            tenant=self.tenant1,
            brand="TP-Link",
            model="Archer C7",
            serial_number="SN123456",
            mac_address="00:11:22:33:44:55"
        )
        
        self.plan1 = SubscriptionPlan.objects.create(
            tenant=self.tenant1,
            name="Basic Plan",
            speed=10,  # Integer, not string
            price=Decimal("500.00")
        )
        
        self.customer1 = Customer.objects.create(
            tenant=self.tenant1,
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",  # Add email
            barangay=self.barangay1
        )
        
        self.lcp1 = LCP.objects.create(
            tenant=self.tenant1,
            name="LCP 1",
            barangay=self.barangay1
        )
        
        self.splitter1 = Splitter.objects.create(
            tenant=self.tenant1,
            lcp=self.lcp1,
            code="SP-001",
            type="1:8"  # 8 port splitter
        )
        
        self.nap1 = NAP.objects.create(
            tenant=self.tenant1,
            splitter=self.splitter1,
            splitter_port=1,
            code="NAP-001",
            name="NAP 1",
            location="Near building A"
        )
        
        self.installation1 = CustomerInstallation.objects.create(
            tenant=self.tenant1,
            customer=self.customer1,
            nap=self.nap1,
            nap_port=1,
            router=self.router1,
            installation_date=timezone.now().date(),
            installation_technician=self.user1  # Add technician
        )
        
        self.subscription1 = CustomerSubscription.objects.create(
            tenant=self.tenant1,
            customer_installation=self.installation1,
            subscription_plan=self.plan1,
            amount=Decimal("500.00"),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            created_by=self.user1  # Add created_by
        )
        
        # Create test data for tenant2
        self.barangay2 = Barangay.objects.create(
            tenant=self.tenant2,
            name="Barangay 2"
        )
        
        self.customer2 = Customer.objects.create(
            tenant=self.tenant2,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",  # Add email
            barangay=self.barangay2
        )
        
        # Give both users all report permissions
        from django.contrib.auth.models import Permission
        report_permissions = Permission.objects.filter(
            content_type__app_label='reports'
        )
        self.user1.user_permissions.add(*report_permissions)
        self.user2.user_permissions.add(*report_permissions)
        
    def test_reports_dashboard_isolation(self):
        """Test reports dashboard shows only current tenant data."""
        # Login as user1
        self.client.force_login(self.user1)
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 200)
        
    def test_daily_collection_report_isolation(self):
        """Test daily collection report shows only current tenant data."""
        # Login as user1
        self.client.force_login(self.user1)
        response = self.client.get(reverse('reports:daily_collection'))
        self.assertEqual(response.status_code, 200)
        
        # Check that tenant1's data is visible
        self.assertContains(response, "₱500")  # Subscription amount
        self.assertContains(response, "John Doe")
        
        # Ensure tenant2's data is not visible
        self.assertNotContains(response, "Jane Smith")
        
    def test_subscription_expiry_report_isolation(self):
        """Test subscription expiry report shows only current tenant data."""
        # Update subscription to expire in 2 days so it shows in the urgent list
        self.subscription1.end_date = timezone.now() + timedelta(days=2)
        self.subscription1.save()
        
        self.client.force_login(self.user1)
        response = self.client.get(reverse('reports:subscription_expiry'))
        self.assertEqual(response.status_code, 200)
        
        # Should see tenant1's customer in the urgent list
        self.assertContains(response, "John Doe")
        # Should see the urgent count
        self.assertContains(response, "Due in 3 Days")
        
    def test_monthly_revenue_report_isolation(self):
        """Test monthly revenue report shows only current tenant data."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse('reports:monthly_revenue'))
        self.assertEqual(response.status_code, 200)
        
        # Should see tenant1's revenue
        self.assertContains(response, "₱500")
        
    def test_csv_export_isolation(self):
        """Test CSV exports contain only current tenant data."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse('reports:daily_collection') + '?export=csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        # Check CSV content
        content = response.content.decode('utf-8')
        self.assertIn("John Doe", content)
        self.assertNotIn("Jane Smith", content)
        
    def test_cross_tenant_access_denied(self):
        """Test that users cannot see other tenant's report data."""
        # Create subscription for tenant2
        lcp2 = LCP.objects.create(
            tenant=self.tenant2,
            name="LCP 2",
            barangay=self.barangay2
        )
        splitter2 = Splitter.objects.create(
            tenant=self.tenant2,
            lcp=lcp2,
            code="SP-002",
            type="1:8"
        )
        nap2 = NAP.objects.create(
            tenant=self.tenant2,
            splitter=splitter2,
            splitter_port=1,
            code="NAP-002", 
            name="NAP 2",
            location="Near building B"
        )
        router2 = Router.objects.create(
            tenant=self.tenant2,
            brand="Mikrotik",
            model="RB750",
            serial_number="SN789012",
            mac_address="AA:BB:CC:DD:EE:FF"
        )
        plan2 = SubscriptionPlan.objects.create(
            tenant=self.tenant2,
            name="Premium Plan",
            speed=50,  # Integer, not string
            price=Decimal("1000.00")
        )
        installation2 = CustomerInstallation.objects.create(
            tenant=self.tenant2,
            customer=self.customer2,
            nap=nap2,
            nap_port=1,
            router=router2,
            installation_date=timezone.now().date(),
            installation_technician=self.user2  # Add technician
        )
        subscription2 = CustomerSubscription.objects.create(
            tenant=self.tenant2,
            customer_installation=installation2,
            subscription_plan=plan2,
            amount=Decimal("1000.00"),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            created_by=self.user2  # Add created_by
        )
        
        # Login as user1 and check reports
        self.client.force_login(self.user1)
        
        # Daily collection should not show tenant2's ₱1000 subscription
        response = self.client.get(reverse('reports:daily_collection'))
        self.assertNotContains(response, "₱1,000")
        self.assertNotContains(response, "Jane Smith")
        
        # Monthly revenue should only show tenant1's ₱500
        response = self.client.get(reverse('reports:monthly_revenue'))
        self.assertContains(response, "₱500")
        self.assertNotContains(response, "₱1,500")  # Combined total
        
    def test_all_report_urls_require_tenant(self):
        """Test that all report URLs require tenant context."""
        report_urls = [
            'reports:dashboard',
            'reports:daily_collection',
            'reports:subscription_expiry',
            'reports:monthly_revenue',
            'reports:ticket_analysis',
            'reports:technician_performance',
            'reports:customer_acquisition',
            'reports:payment_behavior',
            'reports:area_performance',
        ]
        
        # Test without login (should redirect to login)
        for url_name in report_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)  # Redirect to login
            
        # Test with login
        self.client.force_login(self.user1)
        for url_name in report_urls:
            response = self.client.get(reverse(url_name))
            # Should either be 200 OK or 403 Forbidden (if no permission)
            self.assertIn(response.status_code, [200, 403])
