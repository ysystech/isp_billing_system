from django.test import TestCase, Client
from apps.utils.test_base import TenantTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant

User = get_user_model()


class TenantPhase1Tests(TenantTestCase):
    """Test Phase 1: Core Infrastructure"""
    
    def setUp(self):
        super().setUp()
        self.client = Client()
        
    def test_tenant_model_exists(self):
        """Test that Tenant model is properly configured"""
        tenant = Tenant.objects.create(
            name="Test Company"
        )
        self.assertEqual(str(tenant), "Test Company")
        self.assertTrue(tenant.is_active)
        
    def test_user_model_has_tenant_fields(self):
        """Test that User model has tenant-related fields"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        , tenant=self.tenant)
        self.assertTrue(hasattr(user, 'tenant'))
        self.assertTrue(hasattr(user, 'is_tenant_owner'))
        self.assertIsNone(user.tenant)
        self.assertFalse(user.is_tenant_owner)
    
    def test_tenant_aware_model_structure(self):
        """Test that TenantAwareModel is properly defined"""
        from apps.utils.models import TenantAwareModel
        
        # Check that TenantAwareModel has tenant field
        tenant_field = TenantAwareModel._meta.get_field('tenant')
        self.assertEqual(tenant_field.get_internal_type(), 'ForeignKey')
        self.assertTrue(tenant_field.many_to_one)
        
    def test_tenant_middleware_configuration(self):
        """Test that middleware is properly configured"""
        from django.conf import settings
        
        # Check that TenantMiddleware is in MIDDLEWARE
        self.assertIn('apps.tenants.middleware.TenantMiddleware', settings.MIDDLEWARE)
    
    def test_tenant_aware_backend_gives_owner_full_permissions(self):
        """Test that tenant owners bypass permission checks"""
        # Create tenant and owner
        tenant = Tenant.objects.create(name="Test ISP")
        owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="testpass123",
            tenant=tenant,
            is_tenant_owner=True
        )
        
        # Create regular user
        regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="testpass123",
            tenant=tenant,
            is_tenant_owner=False
        )
        
        # Test owner has all permissions
        self.assertTrue(owner.has_perm('customers.add_customer'))
        self.assertTrue(owner.has_perm('customers.change_customer'))
        self.assertTrue(owner.has_perm('customers.delete_customer'))
        self.assertTrue(owner.has_module_perms('customers'))
        
        # Test regular user doesn't have permissions by default
        self.assertFalse(regular_user.has_perm('customers.add_customer'))
        self.assertFalse(regular_user.has_perm('customers.change_customer'))
    
    def test_registration_form_has_company_field(self):
        """Test that registration form has company_name field"""
        from apps.users.forms import TermsSignupForm
        
        # Create form instance
        form = TermsSignupForm()
        
        # Check that company_name field exists
        self.assertIn('company_name', form.fields)
        self.assertTrue(form.fields['company_name'].required)
        self.assertEqual(form.fields['company_name'].label, 'Company Name')
    
    def test_create_test_tenant_command(self):
        """Test the create_test_tenant management command"""
        from django.core.management import call_command
        from io import StringIO
        
        # Run the command
        out = StringIO()
        call_command('create_test_tenant', 
                    email='testowner@example.com',
                    password='testpass123',
                    company='Test ISP Co',
                    stdout=out)
        
        # Check output
        output = out.getvalue()
        self.assertIn('Successfully created tenant', output)
        
        # Verify tenant and user were created
        user = User.objects.get(email='testowner@example.com')
        self.assertTrue(user.is_tenant_owner)
        self.assertEqual(user.tenant.name, 'Test ISP Co')
        self.assertEqual(user.tenant.created_by, user)
