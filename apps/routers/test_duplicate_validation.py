from django.test import TestCase
from django.urls import reverse
from apps.users.models import CustomUser
from apps.tenants.models import Tenant
from apps.routers.models import Router
from django.contrib.auth.models import Permission


class RouterDuplicateValidationTest(TestCase):
    """Test duplicate router validation."""
    
    def setUp(self):
        # Create a tenant
        self.tenant = Tenant.objects.create(name='Test ISP')
        
        # Create a user with router permissions
        self.user = CustomUser.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='testpass123',
            tenant=self.tenant
        )
        
        # Grant router permissions
        permissions = Permission.objects.filter(
            codename__in=['view_router_list', 'add_router', 'change_router']
        )
        self.user.user_permissions.add(*permissions)
        
        # Create an existing router
        self.existing_router = Router.objects.create(
            tenant=self.tenant,
            brand='TP-Link',
            model='Archer C6',
            serial_number='SN123456',
            mac_address='00:11:22:33:44:55'
        )
        
        self.client.login(username='test@test.com', password='testpass123')
    
    def test_duplicate_serial_number_shows_error(self):
        """Test that duplicate serial number shows user-friendly error."""
        data = {
            'brand': 'Mikrotik',
            'model': 'RB750',
            'serial_number': 'SN123456',  # Duplicate serial number
            'mac_address': 'AA:BB:CC:DD:EE:FF',
            'notes': ''
        }
        
        response = self.client.post(reverse('routers:create'), data)
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Check for user-friendly error message
        self.assertContains(response, "A router with serial number &#x27;SN123456&#x27; already exists in your inventory.")
        self.assertNotContains(response, "IntegrityError")
        self.assertNotContains(response, "duplicate key value")
    
    def test_duplicate_mac_address_shows_error(self):
        """Test that duplicate MAC address shows user-friendly error."""
        data = {
            'brand': 'Mikrotik',
            'model': 'RB750',
            'serial_number': 'SN999999',
            'mac_address': '00:11:22:33:44:55',  # Duplicate MAC address
            'notes': ''
        }
        
        response = self.client.post(reverse('routers:create'), data)
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Check for user-friendly error message
        self.assertContains(response, "A router with MAC address &#x27;00:11:22:33:44:55&#x27; already exists in your inventory.")
        self.assertNotContains(response, "IntegrityError")
        self.assertNotContains(response, "duplicate key value")
    
    def test_unique_router_creates_successfully(self):
        """Test that a router with unique values creates successfully."""
        data = {
            'brand': 'Mikrotik',
            'model': 'RB750',
            'serial_number': 'SN999999',
            'mac_address': 'AA:BB:CC:DD:EE:FF',
            'notes': 'Test router'
        }
        
        response = self.client.post(reverse('routers:create'), data)
        
        # Should redirect to detail page
        self.assertEqual(response.status_code, 302)
        
        # Check router was created
        router = Router.objects.filter(serial_number='SN999999').first()
        self.assertIsNotNone(router)
        self.assertEqual(router.brand, 'Mikrotik')
    
    def test_different_tenant_can_use_same_serial(self):
        """Test that different tenants can have routers with same serial number."""
        # Create another tenant and user
        other_tenant = Tenant.objects.create(name='Other ISP')
        other_user = CustomUser.objects.create_user(
            username='other@test.com',
            email='other@test.com',
            password='testpass123',
            tenant=other_tenant
        )
        
        # Grant permissions
        permissions = Permission.objects.filter(codename='add_router')
        other_user.user_permissions.add(*permissions)
        
        # Login as other user
        self.client.login(username='other@test.com', password='testpass123')
        
        # Try to create router with same serial number
        data = {
            'brand': 'Ubiquiti',
            'model': 'EdgeRouter',
            'serial_number': 'SN123456',  # Same as existing router in different tenant
            'mac_address': '11:22:33:44:55:66',
            'notes': ''
        }
        
        response = self.client.post(reverse('routers:create'), data)
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        
        # Check router was created
        router = Router.objects.filter(
            tenant=other_tenant,
            serial_number='SN123456'
        ).first()
        self.assertIsNotNone(router)
