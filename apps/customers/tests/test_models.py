from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.customers.models import Customer


User = get_user_model()


class CustomerModelTest(TestCase):
    def setUp(self):
        self.customer_data = {
            "first_name": "Juan",
            "last_name": "Dela Cruz",
            "email": "juan@example.com",
            "phone_primary": "+639123456789",
            "street_address": "123 Main St",
            "barangay": "Barangay 1",
        }

    def test_create_customer(self):
        customer = Customer.objects.create(**self.customer_data)
        self.assertEqual(customer.first_name, "Juan")
        self.assertEqual(customer.last_name, "Dela Cruz")
        self.assertEqual(customer.email, "juan@example.com")
        self.assertEqual(customer.status, Customer.ACTIVE)

    def test_get_full_name(self):
        customer = Customer.objects.create(**self.customer_data)
        self.assertEqual(customer.get_full_name(), "Juan Dela Cruz")

    def test_get_complete_address(self):
        customer = Customer.objects.create(**self.customer_data)
        expected = "123 Main St, Barangay 1"
        self.assertEqual(customer.get_complete_address(), expected)

    def test_is_active_property(self):
        customer = Customer.objects.create(**self.customer_data)
        self.assertTrue(customer.is_active)
        
        customer.status = Customer.SUSPENDED
        customer.save()
        self.assertFalse(customer.is_active)

    def test_string_representation(self):
        customer = Customer.objects.create(**self.customer_data)
        self.assertEqual(str(customer), "Juan Dela Cruz (juan@example.com)")

    def test_unique_email_constraint(self):
        Customer.objects.create(**self.customer_data)
        
        # Try to create another customer with same email
        duplicate_data = self.customer_data.copy()
        duplicate_data["first_name"] = "Maria"
        
        with self.assertRaises(Exception):
            Customer.objects.create(**duplicate_data)

    def test_customer_with_user_account(self):
        user = User.objects.create_user(
            username="juan123",
            email="juan@example.com",
            password="testpass123"
        )
        
        customer_data = self.customer_data.copy()
        customer_data["user"] = user
        customer = Customer.objects.create(**customer_data)
        
        self.assertEqual(customer.user, user)
        self.assertEqual(user.customer_profile, customer)
