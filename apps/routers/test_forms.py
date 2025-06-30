from django.test import TestCase
from django.urls import reverse
from apps.users.models import CustomUser
from apps.tenants.models import Tenant
from apps.routers.models import Router
from django.contrib.auth.models import Permission


class RouterFormTest(TestCase):
    """Test the router form pages."""
    
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
        
        # Create a test router
        self.router = Router.objects.create(
            tenant=self.tenant,
            brand='TP-Link',
            model='Archer C6',
            serial_number='SN123456',
            mac_address='00:11:22:33:44:55'
        )
        
        self.client.login(username='test@test.com', password='testpass123')
    
    def test_router_create_page_renders(self):
        """Test that router create page renders correctly."""
        response = self.client.get(reverse('routers:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Router')
        self.assertContains(response, 'Router Information')
        self.assertContains(response, 'Technical Details')
        self.assertNotContains(response, 'hx-target="#modal-container"')
    
    def test_router_create_form_submission(self):
        """Test creating a new router."""
        data = {
            'brand': 'Mikrotik',
            'model': 'RB750',
            'serial_number': 'MT987654',
            'mac_address': 'AA:BB:CC:DD:EE:FF',
            'notes': 'Test router'
        }
        
        response = self.client.post(reverse('routers:create'), data)
        
        # Should redirect to detail page
        self.assertEqual(response.status_code, 302)
        
        # Check router was created
        router = Router.objects.filter(serial_number='MT987654').first()
        self.assertIsNotNone(router)
        self.assertEqual(router.brand, 'Mikrotik')
        self.assertEqual(router.tenant, self.tenant)
    
    def test_router_update_page_renders(self):
        """Test that router update page renders correctly."""
        response = self.client.get(reverse('routers:update', args=[self.router.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Router')
        self.assertContains(response, 'TP-Link')
        self.assertContains(response, 'SN123456')
    
    def test_router_list_has_regular_links(self):
        """Test that router list uses regular links, not modals."""
        response = self.client.get(reverse('routers:list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that Add New Router button doesn't have HTMX attributes
        self.assertNotContains(response, 'hx-target="#modal-container"')
        self.assertContains(response, 'href="{}"'.format(reverse('routers:create')))
