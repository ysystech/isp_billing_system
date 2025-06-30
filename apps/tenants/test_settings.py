from django.test import TestCase
from django.urls import reverse
from apps.users.models import CustomUser
from apps.tenants.models import Tenant


class TenantSettingsTest(TestCase):
    """Test the tenant settings functionality."""
    
    def setUp(self):
        # Create a tenant
        self.tenant = Tenant.objects.create(name='Test Company')
        
        # Create a tenant owner
        self.owner = CustomUser.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_tenant_owner=True
        )
        
        # Create a regular user
        self.user = CustomUser.objects.create_user(
            username='user@test.com',
            email='user@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_tenant_owner=False
        )
    
    def test_tenant_settings_requires_owner(self):
        """Test that only tenant owners can access settings."""
        # Try as regular user
        self.client.login(username='user@test.com', password='testpass123')
        response = self.client.get(reverse('tenants:settings'))
        self.assertEqual(response.status_code, 403)
        
        # Try as tenant owner
        self.client.login(username='owner@test.com', password='testpass123')
        response = self.client.get(reverse('tenants:settings'))
        self.assertEqual(response.status_code, 200)
    
    def test_tenant_settings_displays_form(self):
        """Test that settings page displays the form correctly."""
        self.client.login(username='owner@test.com', password='testpass123')
        response = self.client.get(reverse('tenants:settings'))
        
        self.assertContains(response, 'Company Settings')
        self.assertContains(response, 'Test Company')
        self.assertContains(response, 'Company Name')
    
    def test_tenant_settings_update(self):
        """Test updating tenant name."""
        self.client.login(username='owner@test.com', password='testpass123')
        
        response = self.client.post(reverse('tenants:settings'), {
            'name': 'Updated Company Name'
        })
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check the tenant was updated
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.name, 'Updated Company Name')
