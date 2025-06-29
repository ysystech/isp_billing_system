"""
Base test utilities for multi-tenant testing
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant

User = get_user_model()


class TenantTestCase(TestCase):
    """
    Base test case that automatically creates a tenant for testing.
    All test classes should inherit from this instead of TestCase.
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test tenant for all tests in this class
        cls.tenant = Tenant.objects.create(
            name="Test Company",
            is_active=True
        )
    
    def setUp(self):
        """Set up test data with tenant context."""
        super().setUp()
        # Create a test user with tenant
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            tenant=self.tenant,
            is_tenant_owner=False
        )
        
        # Create a tenant owner user
        self.owner = User.objects.create_user(
            username='testowner',
            password='testpass123',
            email='owner@example.com',
            tenant=self.tenant,
            is_tenant_owner=True
        )
        
        # Create a user from different tenant for isolation testing
        self.other_tenant = Tenant.objects.create(
            name="Other Company",
            is_active=True
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123',
            email='other@example.com',
            tenant=self.other_tenant,
            is_tenant_owner=False
        )
    
    def create_test_user(self, username='testuser2', **kwargs):
        """Helper to create additional test users in the same tenant."""
        defaults = {
            'password': 'testpass123',
            'email': f'{username}@example.com',
            'tenant': self.tenant,
            'is_tenant_owner': False
        }
        defaults.update(kwargs)
        return User.objects.create_user(username=username, **defaults)


class TenantTransactionTestCase(TransactionTestCase):
    """
    Base transaction test case for tests that need transactions.
    """
    
    def setUp(self):
        """Set up test data with tenant context."""
        super().setUp()
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            name="Test Company",
            is_active=True
        )
        
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            tenant=self.tenant,
            is_tenant_owner=False
        )
        
        self.owner = User.objects.create_user(
            username='testowner', 
            password='testpass123',
            email='owner@example.com',
            tenant=self.tenant,
            is_tenant_owner=True
        )


class TenantAPITestMixin:
    """
    Mixin for API tests that need tenant context.
    """
    
    def setUp(self):
        """Set up API test data."""
        super().setUp()
        # Ensure we have a client
        if not hasattr(self, 'client'):
            from django.test import Client
            self.client = Client()
    
    def login_as_user(self):
        """Log in as regular tenant user."""
        self.client.login(username='testuser', password='testpass123')
    
    def login_as_owner(self):
        """Log in as tenant owner."""
        self.client.login(username='testowner', password='testpass123')
    
    def login_as_other_tenant_user(self):
        """Log in as user from different tenant."""
        self.client.login(username='otheruser', password='testpass123')
    
    def get_headers(self, **kwargs):
        """Get headers for API requests."""
        headers = {
            'HTTP_ACCEPT': 'application/json',
        }
        headers.update(kwargs)
        return headers
