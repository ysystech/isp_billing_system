from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.subscriptions.models import SubscriptionPlan
from apps.subscriptions.forms import SubscriptionPlanForm

User = get_user_model()


class SubscriptionPlanModelTest(TestCase):
    """Test cases for the SubscriptionPlan model."""
    
    def setUp(self):
        self.plan = SubscriptionPlan.objects.create(
            name="Basic Plan",
            description="Basic internet plan for home users",
            speed=100,
            price=Decimal('1000.00')
        )
    
    def test_create_subscription_plan(self):
        """Test creating a subscription plan."""
        self.assertEqual(self.plan.name, "Basic Plan")
        self.assertEqual(self.plan.speed, 100)
        self.assertEqual(self.plan.price, Decimal('1000.00'))
        self.assertTrue(self.plan.is_active)
    
    def test_string_representation(self):
        """Test the string representation of a plan."""
        expected = "Basic Plan - 100Mbps (₱1000.00/month)"
        self.assertEqual(str(self.plan), expected)
    
    def test_display_properties(self):
        """Test display properties."""
        self.assertEqual(self.plan.display_price, "₱1,000.00")
        self.assertEqual(self.plan.display_speed, "100 Mbps")
    
    def test_unique_name_constraint(self):
        """Test that plan names must be unique."""
        with self.assertRaises(Exception):
            SubscriptionPlan.objects.create(
                name="Basic Plan",  # Duplicate name
                speed=50,
                price=Decimal('500.00')
            )


class SubscriptionPlanFormTest(TestCase):
    """Test cases for the SubscriptionPlanForm."""
    
    def test_valid_form(self):
        """Test form with valid data."""
        form_data = {
            'name': 'Premium Plan',
            'description': 'High-speed internet for power users',
            'speed': 500,
            'price': '2500.00',
            'is_active': True
        }
        form = SubscriptionPlanForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_negative_price_validation(self):
        """Test that negative prices are not allowed."""
        form_data = {
            'name': 'Invalid Plan',
            'speed': 100,
            'price': '-100.00',
            'is_active': True
        }
        form = SubscriptionPlanForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)
    
    def test_zero_speed_validation(self):
        """Test that speed must be greater than 0."""
        form_data = {
            'name': 'Invalid Plan',
            'speed': 0,
            'price': '1000.00',
            'is_active': True
        }
        form = SubscriptionPlanForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('speed', form.errors)


class SubscriptionPlanViewTest(TestCase):
    """Test cases for subscription plan views."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser@example.com', password='testpass123')
        
        self.plan = SubscriptionPlan.objects.create(
            name="Test Plan",
            description="Test description",
            speed=200,
            price=Decimal('1500.00')
        )
    
    def test_list_view(self):
        """Test the subscription plan list view."""
        url = reverse('subscriptions:subscription_plan_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Plan')
        self.assertContains(response, '200 Mbps')
    
    def test_create_view_get(self):
        """Test GET request to create view."""
        url = reverse('subscriptions:subscription_plan_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Subscription Plan')
    
    def test_create_view_post(self):
        """Test POST request to create a new plan."""
        url = reverse('subscriptions:subscription_plan_create')
        data = {
            'name': 'New Plan',
            'description': 'New plan description',
            'speed': 300,
            'price': '2000.00',
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SubscriptionPlan.objects.filter(name='New Plan').exists())
    
    def test_update_view(self):
        """Test updating a plan."""
        url = reverse('subscriptions:subscription_plan_update', kwargs={'pk': self.plan.pk})
        data = {
            'name': 'Updated Plan',
            'description': 'Updated description',
            'speed': 250,
            'price': '1800.00',
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.name, 'Updated Plan')
        self.assertEqual(self.plan.speed, 250)
    
    def test_delete_view(self):
        """Test deleting a plan."""
        url = reverse('subscriptions:subscription_plan_delete', kwargs={'pk': self.plan.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SubscriptionPlan.objects.filter(pk=self.plan.pk).exists())
    
    def test_detail_view(self):
        """Test the plan detail view."""
        url = reverse('subscriptions:subscription_plan_detail', kwargs={'pk': self.plan.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.name)
        self.assertContains(response, self.plan.display_price)
    
    def test_search_functionality(self):
        """Test searching for plans."""
        # Create additional plans
        SubscriptionPlan.objects.create(
            name="Enterprise Plan",
            speed=1000,
            price=Decimal('5000.00')
        )
        
        url = reverse('subscriptions:subscription_plan_list')
        response = self.client.get(url, {'search': 'Enterprise'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enterprise Plan')
        self.assertNotContains(response, 'Test Plan')
    
    def test_login_required(self):
        """Test that login is required for all views."""
        self.client.logout()
        
        urls = [
            reverse('subscriptions:subscription_plan_list'),
            reverse('subscriptions:subscription_plan_create'),
            reverse('subscriptions:subscription_plan_detail', kwargs={'pk': self.plan.pk}),
            reverse('subscriptions:subscription_plan_update', kwargs={'pk': self.plan.pk}),
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/accounts/login/', response.url)
