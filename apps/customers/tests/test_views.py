from django.test import TestCase, Client
from apps.utils.test_base import TenantTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.barangays.models import Barangay

from apps.customers.models import Customer


User = get_user_model()


class CustomerViewTest(TenantTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        
        # Create a barangay for testing
        self.barangay = Barangay.objects.create(
            name="Test Barangay",
            tenant=self.tenant
        )
        
        # Use the tenant owner from TenantTestCase
        self.client.login(username="testowner", password="testpass123")
        
        self.customer = Customer.objects.create(
            first_name="Test",
            last_name="Customer",
            email="test@customer.com",
            phone_primary="+639123456789",
            street_address="123 Test St",
            barangay=self.barangay,
            tenant=self.tenant
        )

    def test_customer_list_view(self):
        url = reverse("customers:customer_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Customer")
        self.assertContains(response, "test@customer.com")

    def test_customer_detail_view(self):
        url = reverse("customers:customer_detail", kwargs={"pk": self.customer.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.customer.get_full_name())
        self.assertContains(response, self.customer.email)

    def test_customer_create_view(self):
        url = reverse("customers:customer_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Test POST
        data = {
            "first_name": "New",
            "last_name": "Customer",
            "email": "new@customer.com",
            "phone_primary": "+639987654321",
            "street_address": "456 New St",
            "barangay": self.barangay.pk,
            "status": "active",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Customer.objects.filter(email="new@customer.com", tenant=self.tenant).exists())
