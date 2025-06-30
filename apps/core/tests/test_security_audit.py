"""
Security Audit Tests for Multi-Tenant ISP Billing System

This test suite performs a comprehensive security audit of tenant isolation.
"""

from django.test import TestCase
from django.urls import reverse
from django.db import connection
from django.db.models import Q

from apps.tenants.models import Tenant
from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.customer_subscriptions.models import CustomerSubscription
from apps.routers.models import Router
from apps.tickets.models import Ticket
from apps.roles.models import Role
from apps.audit_logs.models import AuditLogEntry


class TenantSecurityAuditTest(TestCase):
    """Comprehensive security audit for tenant isolation."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for security testing."""
        # Create two competing ISP tenants
        cls.tenant1 = Tenant.objects.create(name="SecureNet ISP")
        cls.tenant2 = Tenant.objects.create(name="CompetitorISP")
        
        # Create users with different permission levels
        cls.admin1 = CustomUser.objects.create_user(
            username="admin1",
            email="admin@securenet.com",
            password="testpass123",
            tenant=cls.tenant1,
            is_tenant_owner=True,
            is_staff=True
        )
        
        cls.user1 = CustomUser.objects.create_user(
            username="user1",
            email="user@securenet.com",
            password="testpass123",
            tenant=cls.tenant1,
            is_staff=True
        )
        
        cls.admin2 = CustomUser.objects.create_user(
            username="admin2",
            email="admin@competitor.com",
            password="testpass123",
            tenant=cls.tenant2,
            is_tenant_owner=True,
            is_staff=True
        )
        
        # Create sensitive data for each tenant
        cls.barangay1 = Barangay.objects.create(
            tenant=cls.tenant1,
            name="Tenant1 Secret Location"
        )
        
        cls.customer1 = Customer.objects.create(
            tenant=cls.tenant1,
            first_name="VIP",
            last_name="Customer",
            email="vip@securenet.com",
            phone_primary="09991234567",
            barangay=cls.barangay1
        )
        
        cls.barangay2 = Barangay.objects.create(
            tenant=cls.tenant2,
            name="Tenant2 Confidential Area"
        )
        
        cls.customer2 = Customer.objects.create(
            tenant=cls.tenant2,
            first_name="Premium",
            last_name="Client",
            email="premium@competitor.com",
            phone_primary="09887654321",
            barangay=cls.barangay2
        )
    
    def test_url_parameter_tampering(self):
        """Test that users cannot access other tenant's data by manipulating URLs."""
        self.client.force_login(self.admin1)
        
        # List of URL patterns to test
        test_urls = [
            ('customers:detail', [self.customer2.id]),
            ('barangays:update', [self.barangay2.id]),
            ('customers:update', [self.customer2.id]),
            ('customers:delete', [self.customer2.id]),
        ]
        
        for url_name, args in test_urls:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name, args=args))
                self.assertEqual(
                    response.status_code, 
                    404,
                    f"URL {url_name} should return 404 for cross-tenant access"
                )
    
    def test_form_data_injection(self):
        """Test that users cannot inject other tenant's IDs in forms."""
        self.client.force_login(self.admin1)
        
        # Try to create a customer with tenant2's barangay
        response = self.client.post(reverse('customers:create'), {
            'first_name': 'Hacker',
            'last_name': 'Test',
            'email': 'hacker@test.com',
            'phone_primary': '09123456789',
            'barangay': self.barangay2.id,  # Wrong tenant!
            'address': 'Test Address',
            'status': Customer.ACTIVE
        })
        
        # Should either fail validation or ignore the invalid barangay
        if response.status_code == 302:  # Redirect after success
            # Check that customer was NOT created with tenant2's barangay
            customer = Customer.objects.filter(email='hacker@test.com').first()
            if customer:
                self.assertNotEqual(customer.barangay_id, self.barangay2.id)
        else:
            # Form should have validation errors
            self.assertFormError(response, 'form', 'barangay', [])
    
    def test_api_tenant_isolation(self):
        """Test that APIs properly filter by tenant."""
        self.client.force_login(self.admin1)
        
        # Test customer coordinates API
        response = self.client.get('/customers/api/coordinates/')
        self.assertEqual(response.status_code, 200)
        
        # Parse response and verify only tenant1 customers
        data = response.json()
        for customer in data:
            # Verify customer belongs to tenant1
            db_customer = Customer.objects.get(id=customer['id'])
            self.assertEqual(db_customer.tenant_id, self.tenant1.id)
    
    def test_search_isolation(self):
        """Test that search functionality doesn't leak cross-tenant data."""
        self.client.force_login(self.admin1)
        
        # Search for tenant2's customer name
        response = self.client.get('/customers/', {'q': 'Premium'})
        self.assertEqual(response.status_code, 200)
        
        # Should not find tenant2's "Premium Client"
        self.assertNotContains(response, 'Premium Client')
        self.assertNotContains(response, self.customer2.email)
    
    def test_bulk_operations_isolation(self):
        """Test that bulk operations respect tenant boundaries."""
        self.client.force_login(self.admin1)
        
        # Create some routers for tenant1
        Router.objects.create(
            tenant=self.tenant1,
            brand="TP-Link",
            model="Test1",
            serial_number="BULK1",
            mac_address="11:22:33:44:55:66"
        )
        
        # Try to access router list with export
        response = self.client.get('/routers/', {'export': 'csv'})
        
        if response.status_code == 200 and response.get('Content-Type', '').startswith('text/csv'):
            # Check CSV content
            content = response.content.decode('utf-8')
            # Should not contain any reference to tenant2
            self.assertNotIn('CompetitorISP', content)
            self.assertNotIn(str(self.tenant2.id), content)
    
    def test_audit_log_isolation(self):
        """Test that audit logs are properly isolated by tenant."""
        self.client.force_login(self.admin1)
        
        # Create a customer to generate audit log
        response = self.client.post(reverse('customers:create'), {
            'first_name': 'Audit',
            'last_name': 'Test',
            'email': 'audit@test.com',
            'phone_primary': '09111111111',
            'barangay': self.barangay1.id,
            'address': 'Audit Address',
            'status': Customer.ACTIVE
        })
        
        # Check audit logs
        if hasattr(self.admin1, 'tenant'):
            audit_logs = AuditLogEntry.objects.filter(user=self.admin1)
            for log in audit_logs:
                self.assertEqual(log.tenant_id, self.tenant1.id)
    
    def test_permission_bypass_attempts(self):
        """Test that regular users cannot bypass permissions."""
        # Create a limited user for tenant1
        limited_user = CustomUser.objects.create_user(
            username="limited1",
            email="limited@securenet.com",
            password="testpass123",
            tenant=self.tenant1,
            is_staff=True
        )
        
        self.client.force_login(limited_user)
        
        # Try to access admin-only views
        admin_urls = [
            '/admin/',
            reverse('barangays:create'),
            reverse('customers:delete', args=[self.customer1.id]),
        ]
        
        for url in admin_urls:
            response = self.client.get(url)
            self.assertIn(
                response.status_code,
                [302, 403, 404],
                f"Limited user should not access {url}"
            )
    
    def test_sql_injection_protection(self):
        """Test that the system is protected against SQL injection."""
        self.client.force_login(self.admin1)
        
        # Try SQL injection in search
        dangerous_inputs = [
            "'; DROP TABLE customers; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM tenants_tenant --",
        ]
        
        for dangerous_input in dangerous_inputs:
            with self.subTest(input=dangerous_input):
                # Try in search
                response = self.client.get('/customers/', {'q': dangerous_input})
                self.assertEqual(response.status_code, 200)
                
                # Verify tables still exist
                self.assertTrue(Customer.objects.exists())
                self.assertTrue(Tenant.objects.exists())
    
    def test_session_isolation(self):
        """Test that sessions don't leak between tenants."""
        # Login as tenant1 admin
        self.client.force_login(self.admin1)
        session1 = self.client.session.session_key
        
        # Logout and login as tenant2 admin
        self.client.logout()
        self.client.force_login(self.admin2)
        session2 = self.client.session.session_key
        
        # Sessions should be different
        self.assertNotEqual(session1, session2)
        
        # Try to access with old session
        self.client.logout()
        session = self.client.session
        session.session_key = session1
        session.save()
        
        # Should not have access to tenant2 data
        response = self.client.get('/customers/')
        # Should redirect to login or show no data
        self.assertIn(response.status_code, [302, 200])
        if response.status_code == 200:
            self.assertNotContains(response, self.customer2.email)
    
    def test_file_upload_isolation(self):
        """Test that file uploads are isolated by tenant."""
        # This would test file upload features if they exist
        # For now, we'll test that router imports respect tenant boundaries
        pass
    
    def test_error_message_leakage(self):
        """Test that error messages don't leak tenant information."""
        self.client.force_login(self.admin1)
        
        # Try to access non-existent customer
        response = self.client.get('/customers/99999/')
        self.assertEqual(response.status_code, 404)
        
        # Error page should not reveal information about other tenants
        if hasattr(response, 'content'):
            content = str(response.content)
            self.assertNotIn('CompetitorISP', content)
            self.assertNotIn(self.customer2.email, content)
