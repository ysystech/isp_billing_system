from django.test import TestCase
from django.urls import reverse
from apps.users.models import CustomUser
from apps.tenants.models import Tenant
from apps.barangays.models import Barangay
from django.contrib.auth.models import Permission


class BarangayFormTest(TestCase):
    """Test the barangay form pages."""
    
    def setUp(self):
        # Create a tenant
        self.tenant = Tenant.objects.create(name='Test ISP')
        
        # Create a user with barangay permissions
        self.user = CustomUser.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='testpass123',
            tenant=self.tenant
        )
        
        # Grant barangay permissions
        permissions = Permission.objects.filter(
            codename__in=['view_barangay_list', 'add_barangay', 'change_barangay']
        )
        self.user.user_permissions.add(*permissions)
        
        # Create a test barangay
        self.barangay = Barangay.objects.create(
            tenant=self.tenant,
            name='Test Barangay',
            code='TB001',
            description='Test description',
            is_active=True
        )
        
        self.client.login(username='test@test.com', password='testpass123')
    
    def test_barangay_create_page_renders(self):
        """Test that barangay create page renders correctly."""
        response = self.client.get(reverse('barangays:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Barangay')
        self.assertContains(response, 'Basic Information')
        self.assertContains(response, 'Details')
        self.assertContains(response, 'Settings')
        self.assertNotContains(response, 'hx-target="#modal-container"')
    
    def test_barangay_create_form_submission(self):
        """Test creating a new barangay."""
        data = {
            'name': 'New Barangay',
            'code': 'NB001',
            'description': 'A new barangay for testing',
            'is_active': True
        }
        
        response = self.client.post(reverse('barangays:create'), data)
        
        # Should redirect to detail page
        self.assertEqual(response.status_code, 302)
        
        # Check barangay was created
        barangay = Barangay.objects.filter(name='New Barangay').first()
        self.assertIsNotNone(barangay)
        self.assertEqual(barangay.code, 'NB001')
        self.assertEqual(barangay.tenant, self.tenant)
    
    def test_barangay_update_page_renders(self):
        """Test that barangay update page renders correctly."""
        response = self.client.get(reverse('barangays:update', args=[self.barangay.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Barangay')
        self.assertContains(response, 'Test Barangay')
        self.assertContains(response, 'TB001')
    
    def test_barangay_list_has_regular_links(self):
        """Test that barangay list uses regular links, not modals."""
        response = self.client.get(reverse('barangays:list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that Add New Barangay button doesn't have HTMX attributes
        self.assertNotContains(response, 'hx-target="#modal-container"')
        self.assertContains(response, 'href="{}"'.format(reverse('barangays:create')))
    
    def test_duplicate_name_validation(self):
        """Test that duplicate barangay names show error."""
        data = {
            'name': 'Test Barangay',  # Duplicate name
            'code': 'NEW001',
            'description': 'Another barangay',
            'is_active': True
        }
        
        response = self.client.post(reverse('barangays:create'), data)
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Check for user-friendly error message
        self.assertContains(response, "A barangay named &#x27;Test Barangay&#x27; already exists.")
    
    def test_duplicate_code_validation(self):
        """Test that duplicate barangay codes show error."""
        data = {
            'name': 'Another Barangay',
            'code': 'TB001',  # Duplicate code
            'description': 'Another barangay',
            'is_active': True
        }
        
        response = self.client.post(reverse('barangays:create'), data)
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        
        # Check for user-friendly error message
        self.assertContains(response, "A barangay with code &#x27;TB001&#x27; already exists.")
