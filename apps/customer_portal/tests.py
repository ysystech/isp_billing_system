from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.customers.models import Customer
from apps.tenants.models import Tenant
from apps.barangays.models import Barangay

User = get_user_model()


class CustomerPortalTestCase(TestCase):
    def setUp(self):
        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test ISP",
            is_active=True
        )
        
        # Create barangay
        self.barangay = Barangay.objects.create(
            tenant=self.tenant,
            name="Test Barangay",
            is_active=True
        )
        
        # Create regular user (non-customer)
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="testpass123",
            tenant=self.tenant
        )        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="testpass123",
            tenant=self.tenant
        )
        
        # Create customer profile
        self.customer = Customer.objects.create(
            tenant=self.tenant,
            user=self.customer_user,
            first_name="John",
            last_name="Doe",
            email="customer@example.com",
            phone_primary="09123456789",
            street_address="123 Test St",
            barangay=self.barangay,
            status=Customer.ACTIVE
        )
    
    def test_customer_portal_access(self):
        """Test that customers can access the portal"""
        self.client.login(username="customer", password="testpass123")
        response = self.client.get(reverse('customer_portal:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome, John!")
    
    def test_non_customer_redirect(self):
        """Test that non-customers are redirected"""
        self.client.login(username="regular", password="testpass123")
        response = self.client.get(reverse('customer_portal:dashboard'))
        self.assertEqual(response.status_code, 302)
        # Should redirect to home page
        self.assertEqual(response.url, reverse('web:home'))    
    def test_anonymous_redirect(self):
        """Test that anonymous users are redirected to login"""
        response = self.client.get(reverse('customer_portal:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_profile_update(self):
        """Test customer can update their phone number"""
        self.client.login(username="customer", password="testpass123")
        response = self.client.post(reverse('customer_portal:profile'), {
            'phone_primary': '09987654321'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify phone was updated
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.phone_primary, '09987654321')