from django.test import TestCase
from apps.utils.test_base import TenantTestCase
from apps.barangays.models import Barangay

from apps.customers.forms import CustomerForm, CustomerSearchForm
from apps.customers.models import Customer


class CustomerFormTest(TenantTestCase):
    def setUp(self):
        super().setUp()
        # Create a barangay for testing
        self.barangay = Barangay.objects.create(
            name="Test Barangay",
            tenant=self.tenant
        )
    
    def test_customer_form_valid_data(self):
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone_primary": "+639123456789",
            "street_address": "123 Main St",
            "barangay": self.barangay.pk,
            "status": "active",
        }
        form = CustomerForm(data=form_data, tenant=self.tenant)
        self.assertTrue(form.is_valid())

    def test_customer_form_missing_required_fields(self):
        form = CustomerForm(data={}, tenant=self.tenant)
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)
        self.assertIn("last_name", form.errors)
        self.assertIn("email", form.errors)

    def test_customer_form_duplicate_email(self):
        # Create existing customer
        Customer.objects.create(
            first_name="Existing",
            last_name="Customer",
            email="existing@example.com",
            phone_primary="+639123456789",
            street_address="123 Test St",
            barangay=self.barangay,
            tenant=self.tenant
        )
        
        # Try to create another with same email
        form_data = {
            "first_name": "New",
            "last_name": "Customer",
            "email": "existing@example.com",
            "phone_primary": "+639987654321",
            "street_address": "456 New St",
            "barangay": self.barangay.pk,
            "status": "active",
        }
        form = CustomerForm(data=form_data, tenant=self.tenant)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_customer_search_form(self):
        form = CustomerSearchForm()
        self.assertIn("search", form.fields)
        self.assertIn("status", form.fields)
        self.assertFalse(form.fields["search"].required)
        self.assertFalse(form.fields["status"].required)
