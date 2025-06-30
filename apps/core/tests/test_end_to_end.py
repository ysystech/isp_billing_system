"""
End-to-End Integration Tests for Multi-Tenant ISP Billing System

This test suite verifies complete workflows across all modules with tenant isolation.
"""

from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import Permission
from datetime import timedelta
from decimal import Decimal

from apps.tenants.models import Tenant
from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.routers.models import Router
from apps.subscriptions.models import SubscriptionPlan
from apps.lcp.models import LCP, Splitter, NAP
from apps.customer_installations.models import CustomerInstallation
from apps.customer_subscriptions.models import CustomerSubscription
from apps.tickets.models import Ticket
from apps.roles.models import Role


class MultiTenantEndToEndTest(TransactionTestCase):
    """Test complete workflows from customer signup to billing across multiple tenants."""
    
    def setUp(self):
        """Set up test data for two competing ISP companies."""        # Create two ISP tenants
        self.isp1 = Tenant.objects.create(name="FastNet ISP")
        self.isp2 = Tenant.objects.create(name="SpeedLink Internet")
        
        # Create admin users for each ISP
        self.admin1 = CustomUser.objects.create_user(
            username="admin1",
            email="admin@fastnet.com",
            password="testpass123",
            tenant=self.isp1,
            is_tenant_owner=True,
            is_staff=True
        )
        
        self.admin2 = CustomUser.objects.create_user(
            username="admin2",
            email="admin@speedlink.com",
            password="testpass123",
            tenant=self.isp2,
            is_tenant_owner=True,
            is_staff=True
        )
        
        # Create technician users
        self.tech1 = CustomUser.objects.create_user(
            username="tech1",
            email="tech@fastnet.com",
            password="testpass123",
            tenant=self.isp1,
            is_staff=True
        )