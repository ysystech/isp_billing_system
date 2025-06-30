from django.test import TestCase
from apps.utils.test_base import TenantTestCase
from django.contrib.auth import get_user_model
from apps.barangays.models import Barangay

from apps.customers.models import Customer


User = get_user_model()


class CustomerModelTest(TenantTestCase):
    def setUp(self):
        super().setUp()
        # Create a barangay for testing
        self.barangay = Barangay.objects.create(
            name="Barangay 1",
            tenant=self.tenant
        )
        self.customer_data = {
            "first_name": "Juan",
            "last_name": "Dela Cruz",
            "email": "juan@example.com",
            "phone_primary": "+639123456789",
            "street_address": "123 Main St",
            "barangay": self.barangay,
        }

    def test_create_customer(self):
        customer = Customer.objects.create(**self.customer_data, tenant=self.tenant)
        self.assertEqual(customer.first_name, "Juan")
        self.assertEqual(customer.last_name, "Dela Cruz")
        self.assertEqual(customer.email, "juan@example.com")
        self.assertEqual(customer.status, Customer.ACTIVE)

    def test_get_full_name(self):
        customer = Customer.objects.create(**self.customer_data, tenant=self.tenant)
        self.assertEqual(customer.get_full_name(), "Juan Dela Cruz")

    def test_get_complete_address(self):
        customer = Customer.objects.create(**self.customer_data, tenant=self.tenant)
        expected = "123 Main St, Barangay 1"
        self.assertEqual(customer.get_complete_address(), expected)

    def test_is_active_property(self):
        customer = Customer.objects.create(**self.customer_data, tenant=self.tenant)
        self.assertTrue(customer.is_active)
        
        customer.status = Customer.SUSPENDED
        customer.save()
        self.assertFalse(customer.is_active)

    def test_string_representation(self):
        customer = Customer.objects.create(**self.customer_data, tenant=self.tenant)
        self.assertEqual(str(customer), "Juan Dela Cruz (juan@example.com)")

    def test_unique_email_constraint(self):
        Customer.objects.create(**self.customer_data, tenant=self.tenant)
        
        # Try to create another customer with same email
        duplicate_data = self.customer_data.copy()
        duplicate_data["first_name"] = "Maria"
        
        with self.assertRaises(Exception):
            Customer.objects.create(**duplicate_data, tenant=self.tenant)

    def test_customer_with_user_account(self):
        user = User.objects.create_user(
            username="juan123",
            email="juan@example.com",
            password="testpass123",
            tenant=self.tenant
        )
        
        customer_data = self.customer_data.copy()
        customer_data["user"] = user
        customer = Customer.objects.create(**customer_data, tenant=self.tenant)
        
        self.assertEqual(customer.user, user)
        self.assertEqual(user.customer_profile, customer)
