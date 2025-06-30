"""
Tests for tenant-specific signals.
"""
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.tenants.models import Tenant
from apps.users.models import CustomUser
from apps.utils.test_base import TenantTestCase

User = get_user_model()


class TenantSignalTests(TenantTestCase):
    """Test tenant-specific signal handlers."""
    
    def test_tenant_creation_creates_system_user(self):
        """Test that creating a tenant creates a system user."""
        # Create a new tenant
        new_tenant = Tenant.objects.create(
            name="New ISP Company",
            is_active=True
        )
        
        # Check system user was created
        system_user = User.objects.filter(
            username=f"system_{new_tenant.id}"
        ).first()
        
        self.assertIsNotNone(system_user)
        self.assertEqual(system_user.tenant, new_tenant)
        self.assertFalse(system_user.is_active)
        self.assertFalse(system_user.is_staff)
        
    def test_user_creation_logging(self):
        """Test that user creation is logged."""
        with patch('apps.tenants.signals.logger') as mock_logger:
            # Create a new user
            user = User.objects.create_user(
                username="newuser",
                email="newuser@example.com",
                password="testpass123",
                tenant=self.tenant
            )
            
            # Check logging was called
            mock_logger.info.assert_called_with(
                f"New user newuser created for tenant {self.tenant.name}"
            )
            
    def test_tenant_deletion_logging(self):
        """Test that tenant deletion is logged."""
        # Create a tenant to delete
        temp_tenant = Tenant.objects.create(
            name="Temporary ISP",
            is_active=True
        )
        
        # Get the tenant ID before deletion
        tenant_id = temp_tenant.id
        
        # Delete the system user first to avoid ProtectedError
        CustomUser.objects.filter(tenant=temp_tenant).delete()
        
        with patch('apps.tenants.signals.logger') as mock_logger:
            # Delete the tenant
            temp_tenant.delete()
            
            # Check warning was logged
            mock_logger.warning.assert_called_with(
                "Tenant being deleted: Temporary ISP"
            )
