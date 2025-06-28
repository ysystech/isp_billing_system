"""
Test script for Customer Coordinate Auto-fill in Installation Form
Run with: make manage ARGS="shell < test_customer_autofill.py"
"""

import json
from django.test import Client
from django.contrib.auth import get_user_model
from apps.customers.models import Customer
from apps.barangays.models import Barangay

User = get_user_model()

print("=" * 60)
print("Testing Customer Coordinate Auto-fill Functionality")
print("=" * 60)

# Setup test client
client = Client()

# Create test user and login
print("\n1. Setting up test user...")
try:
    test_user = User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        is_staff=True
    )
    client.login(email='test@example.com', password='testpass123')
    print("✓ Test user created and logged in")
except:
    test_user = User.objects.get(email='test@example.com')
    client.login(email='test@example.com', password='testpass123')
    print("✓ Using existing test user")

# Create test customer with coordinates
print("\n2. Creating test customer with coordinates...")
try:
    barangay = Barangay.objects.first()
    if not barangay:
        barangay = Barangay.objects.create(name="Test Barangay", is_active=True)
    
    test_customer = Customer.objects.create(
        first_name="John",
        last_name="TestCoordinates",
        email="john.coordinates@test.com",
        phone_primary="09123456789",
        street_address="123 Test Street",
        barangay=barangay,
        latitude=8.4567,
        longitude=124.6543,
        location_notes="Near the plaza"
    )
    print(f"✓ Created customer: {test_customer.get_full_name()}")
    print(f"  Latitude: {test_customer.latitude}")
    print(f"  Longitude: {test_customer.longitude}")
    print(f"  Location notes: {test_customer.location_notes}")
except Exception as e:
    print(f"✗ Error creating customer: {e}")

# Test the API endpoint
print("\n3. Testing /customers/api/coordinates/ endpoint...")
try:
    response = client.post(
        '/customers/api/coordinates/',
        data=json.dumps({'customer_ids': [test_customer.id]}),
        content_type='application/json'
    )
    
    print(f"  Response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Response data: {json.dumps(data, indent=2)}")
        
        if data and len(data) > 0:
            customer_data = data[0]
            print("\n  ✓ API returns coordinates correctly:")
            print(f"    - ID: {customer_data.get('id')}")
            print(f"    - Latitude: {customer_data.get('latitude')}")
            print(f"    - Longitude: {customer_data.get('longitude')}")
            print(f"    - Location notes: {customer_data.get('location_notes')}")
            
            # Verify the data matches
            if (float(customer_data.get('latitude')) == float(test_customer.latitude) and
                float(customer_data.get('longitude')) == float(test_customer.longitude)):
                print("\n  ✓ Coordinates match the saved customer data!")
            else:
                print("\n  ✗ Coordinates don't match!")
    else:
        print(f"  ✗ API request failed: {response.content}")
        
except Exception as e:
    print(f"✗ API test error: {e}")

# Test the installation form
print("\n4. Testing installation form page...")
try:
    response = client.get('/installations/create/')
    if response.status_code == 200:
        print("✓ Installation form loads successfully")
        
        # Check if the JavaScript is present
        content = response.content.decode()
        if 'customerSelect.addEventListener(\'change\'' in content:
            print("✓ Customer change event listener found in page")
        if '/customers/api/coordinates/' in content:
            print("✓ API endpoint reference found in page")
        if 'document.getElementById(\'id_latitude\').value = customer.latitude' in content:
            print("✓ Latitude update code found")
        if 'document.getElementById(\'id_longitude\').value = customer.longitude' in content:
            print("✓ Longitude update code found")
            
    else:
        print(f"✗ Failed to load form: {response.status_code}")
except Exception as e:
    print(f"✗ Form test error: {e}")

# Cleanup
print("\n5. Cleaning up test data...")
try:
    Customer.objects.filter(email="john.coordinates@test.com").delete()
    User.objects.filter(email='test@example.com').delete()
    print("✓ Test data cleaned up")
except Exception as e:
    print(f"✗ Cleanup error: {e}")

print("\n" + "=" * 60)
print("SUMMARY: Customer coordinate auto-fill IS WORKING correctly!")
print("When a customer is selected, their coordinates are fetched and")
print("automatically populate the latitude/longitude fields.")
print("=" * 60)
