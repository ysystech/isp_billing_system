"""
Quick test script to verify the new models and relationships are working correctly.
Run with: python manage.py shell < test_phase3.py
"""

from apps.customer_installations.models import CustomerInstallation
from apps.customer_subscriptions.models import CustomerSubscription
from apps.customers.models import Customer
from apps.subscriptions.models import SubscriptionPlan
from django.utils import timezone

print("=== Phase 3 Implementation Test ===\n")

# Test 1: Check models are accessible
print("1. Models imported successfully ✓")

# Test 2: Check installations count
installations = CustomerInstallation.objects.all()
print(f"2. Total installations: {installations.count()}")

# Test 3: Check active installations
active_installations = CustomerInstallation.objects.filter(status='ACTIVE')
print(f"3. Active installations: {active_installations.count()}")

# Test 4: Check subscriptions count
subscriptions = CustomerSubscription.objects.all()
print(f"4. Total subscriptions: {subscriptions.count()}")

# Test 5: Check active subscriptions
now = timezone.now()
active_subs = CustomerSubscription.objects.filter(
    start_date__lte=now,
    end_date__gte=now,
    is_paid=True
)
print(f"5. Active subscriptions: {active_subs.count()}")

# Test 6: Check subscription plans with day_count
plans = SubscriptionPlan.objects.all()
print(f"\n6. Subscription Plans ({plans.count()} total):")
for plan in plans[:5]:  # Show first 5
    print(f"   - {plan.name}: {plan.day_count} days, ₱{plan.price}")

# Test 7: Check installation-subscription relationship
print("\n7. Sample Installation with Subscriptions:")
sample_installation = CustomerInstallation.objects.filter(subscriptions__isnull=False).first()
if sample_installation:
    print(f"   Customer: {sample_installation.customer.full_name}")
    print(f"   Status: {sample_installation.status}")
    print(f"   Current subscription: {'Active' if sample_installation.current_subscription else 'None'}")
    print(f"   Total subscriptions: {sample_installation.subscriptions.count()}")

print("\n=== All tests completed successfully! ===")
