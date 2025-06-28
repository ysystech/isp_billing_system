"""
Script to test geo-location functionality
Run with: make manage ARGS="shell < test_scripts/test_geolocation.py"
"""

from apps.customers.models import Customer
from apps.lcp.models import LCP, Splitter, NAP
from apps.barangays.models import Barangay
from decimal import Decimal

print("=" * 50)
print("Testing Geo-Location Features")
print("=" * 50)

# Test 1: Check if models have geo fields
print("\n1. Checking model fields...")
customer_fields = [f.name for f in Customer._meta.get_fields()]
lcp_fields = [f.name for f in LCP._meta.get_fields()]

geo_fields = ['latitude', 'longitude', 'location_accuracy', 'location_notes']

print("Customer has geo fields:", all(f in customer_fields for f in geo_fields))
print("LCP has geo fields:", all(f in lcp_fields for f in geo_fields))

# Test 2: Create test objects with coordinates
print("\n2. Creating test objects with coordinates...")
try:
    # Get or create a test barangay
    barangay, _ = Barangay.objects.get_or_create(
        name="Test Barangay",
        defaults={'is_active': True}
    )
    
    # Create a test customer with coordinates
    test_customer = Customer.objects.create(
        first_name="Test",
        last_name="GeoCustomer",
        email="test.geo@example.com",
        phone_primary="09123456789",
        street_address="123 Test St",
        barangay=barangay,
        latitude=Decimal('8.4542'),
        longitude=Decimal('124.6319'),
        location_accuracy='exact',
        location_notes='Near city hall'
    )
    print(f"✓ Created customer: {test_customer}")
    print(f"  Coordinates: {test_customer.coordinates_display}")
    print(f"  Has coordinates: {test_customer.has_coordinates}")
    
    # Create a test LCP
    test_lcp = LCP.objects.create(
        name="Test LCP Geo",
        code="LCP-GEO-001",
        location="Test Location",
        barangay=barangay,
        latitude=Decimal('8.4600'),
        longitude=Decimal('124.6400'),
        location_accuracy='approximate',
        coverage_radius_meters=1500
    )
    print(f"✓ Created LCP: {test_lcp}")
    print(f"  Coverage radius: {test_lcp.coverage_radius_meters}m")
    
    # Test distance calculation
    distance = test_customer.distance_to(test_lcp)
    print(f"\n3. Distance Calculation Test:")
    print(f"  Distance from customer to LCP: {distance:.2f} meters")
    
except Exception as e:
    print(f"✗ Error creating test objects: {e}")

# Test 4: Check inheritance
print("\n4. Testing model inheritance...")
print(f"Customer inherits from GeoLocatedModel: {hasattr(Customer, 'distance_to')}")
print(f"LCP inherits from GeoLocatedModel: {hasattr(LCP, 'distance_to')}")
print(f"Splitter inherits from GeoLocatedModel: {hasattr(Splitter, 'distance_to')}")
print(f"NAP inherits from GeoLocatedModel: {hasattr(NAP, 'distance_to')}")

# Clean up
print("\n5. Cleaning up test data...")
try:
    Customer.objects.filter(email="test.geo@example.com").delete()
    LCP.objects.filter(code="LCP-GEO-001").delete()
    print("✓ Test data cleaned up")
except Exception as e:
    print(f"✗ Cleanup error: {e}")

print("\n" + "=" * 50)
print("Geo-location feature test complete!")
print("=" * 50)
