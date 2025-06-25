from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.routers.models import Router
from apps.customers.models import Customer
from apps.barangays.models import Barangay

User = get_user_model()


class RouterModelTest(TestCase):
    """Test the Router model"""
    
    def setUp(self):
        self.router = Router.objects.create(
            brand="TP-Link",
            model="Archer C6",
            serial_number="TL123456789"
        )
    
    def test_router_creation(self):
        """Test router is created with correct attributes"""
        self.assertEqual(self.router.brand, "TP-Link")
        self.assertEqual(self.router.model, "Archer C6")
        self.assertEqual(self.router.serial_number, "TL123456789")
    
    def test_router_str(self):
        """Test the string representation of router"""
        self.assertEqual(str(self.router), "TP-Link Archer C6 - TL123456789")
    
    def test_router_str_without_model(self):
        """Test the string representation of router without model"""
        router = Router.objects.create(
            brand="Mikrotik",
            serial_number="MT987654321"
        )
        self.assertEqual(str(router), "Mikrotik - MT987654321")
    
    def test_unique_serial_number(self):
        """Test that serial numbers must be unique"""
        with self.assertRaises(Exception):
            Router.objects.create(
                brand="Mikrotik",
                model="RB750",
                serial_number="TL123456789"  # Same serial
            )
    
    def test_optional_fields(self):
        """Test that model is optional"""
        router = Router.objects.create(
            brand="Ubiquiti",
            serial_number="UB123456789"
        )
        self.assertEqual(router.model, "")
        self.assertEqual(router.notes, "")
