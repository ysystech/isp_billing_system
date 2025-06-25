from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.barangays.models import Barangay

User = get_user_model()


class BarangayModelTest(TestCase):
    """Test the Barangay model"""
    
    def setUp(self):
        self.barangay = Barangay.objects.create(
            name="Barangay Carmen",
            code="CARM",
            description="Central business district"
        )
    
    def test_barangay_creation(self):
        """Test barangay is created with correct attributes"""
        self.assertEqual(self.barangay.name, "Barangay Carmen")
        self.assertEqual(self.barangay.code, "CARM")
        self.assertEqual(self.barangay.description, "Central business district")
        self.assertTrue(self.barangay.is_active)
    
    def test_barangay_str(self):
        """Test the string representation of barangay"""
        self.assertEqual(str(self.barangay), "Barangay Carmen")
    
    def test_unique_name(self):
        """Test that barangay names must be unique"""
        with self.assertRaises(Exception):
            Barangay.objects.create(name="Barangay Carmen")
    
    def test_unique_code(self):
        """Test that barangay codes must be unique"""
        with self.assertRaises(Exception):
            Barangay.objects.create(name="Another Barangay", code="CARM")
