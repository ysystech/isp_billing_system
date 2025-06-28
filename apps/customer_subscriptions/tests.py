from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.subscriptions.models import SubscriptionPlan
from apps.customer_installations.models import CustomerInstallation
from .models import CustomerSubscription


class CustomerSubscriptionModelTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test barangay
        self.barangay = Barangay.objects.create(
            name='Test Barangay',
            is_active=True
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_primary='09123456789',
            street_address='123 Test St',
            barangay=self.barangay
        )
        
        # Create test installation
        self.installation = CustomerInstallation.objects.create(
            customer=self.customer,
            installation_date=timezone.now().date(),
            installation_technician=self.user,
            status='ACTIVE'
        )
        
        # Create test plan
        self.plan = SubscriptionPlan.objects.create(
            name='Basic Plan',
            description='Test plan',
            speed=10,
            price=Decimal('1000.00'),
            day_count=30
        )
    
    def test_one_month_subscription_calculation(self):
        """Test one month subscription calculation."""
        subscription = CustomerSubscription(
            customer_installation=self.installation,
            subscription_plan=self.plan,
            subscription_type='one_month',
            start_date=timezone.now(),
            created_by=self.user
        )
        subscription.calculate_subscription_details()
        
        self.assertEqual(subscription.amount, Decimal('1000.00'))
        self.assertEqual(subscription.days_added, Decimal('30'))
        
    def test_fifteen_days_subscription_calculation(self):
        """Test 15 days subscription calculation."""
        subscription = CustomerSubscription(
            customer_installation=self.installation,
            subscription_plan=self.plan,
            subscription_type='fifteen_days',
            start_date=timezone.now(),
            created_by=self.user
        )
        subscription.calculate_subscription_details()
        
        self.assertEqual(subscription.amount, Decimal('500.00'))
        self.assertEqual(subscription.days_added, Decimal('15'))
    
    def test_custom_subscription_calculation(self):
        """Test custom amount subscription calculation."""
        subscription = CustomerSubscription(
            customer_installation=self.installation,
            subscription_plan=self.plan,
            subscription_type='custom',
            amount=Decimal('200.00'),
            start_date=timezone.now(),
            created_by=self.user
        )
        subscription.calculate_subscription_details()
        
        self.assertEqual(subscription.days_added, Decimal('6.0'))
    
    def test_subscription_preview(self):
        """Test subscription preview calculation."""
        preview = CustomerSubscription.calculate_preview(
            plan_price=Decimal('1000.00'),
            amount=Decimal('150.00'),
            subscription_type='custom'
        )
        
        self.assertEqual(preview['total_days'], 4.5)
        self.assertEqual(preview['days'], 4)
        self.assertEqual(preview['hours'], 12)
        self.assertEqual(preview['minutes'], 0)
