from django.test import TestCase
from django.urls import reverse
from apps.users.models import CustomUser
from apps.tenants.models import Tenant


class RegistrationFlowTest(TestCase):
    """Test the registration flow creates tenant properly."""
    
    def test_registration_page_shows_company_name_field(self):
        """Test that registration page displays company name field."""
        response = self.client.get(reverse('account_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'company_name')
        self.assertContains(response, 'Company Name')
        self.assertContains(response, 'Enter your company or organization name')
    
    def test_registration_creates_tenant(self):
        """Test that registration creates a tenant and sets user as owner."""
        registration_data = {
            'email': 'test@example.com',
            'company_name': 'Test Company Inc',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'terms_agreement': True,
        }
        
        response = self.client.post(reverse('account_signup'), registration_data)
        
        # Check user was created
        user = CustomUser.objects.filter(email='test@example.com').first()
        self.assertIsNotNone(user)
        
        # Check tenant was created
        tenant = Tenant.objects.filter(name='Test Company Inc').first()
        self.assertIsNotNone(tenant)
        
        # Check user is assigned to tenant and is owner
        self.assertEqual(user.tenant, tenant)
        self.assertTrue(user.is_tenant_owner)
        self.assertEqual(tenant.created_by, user)
