from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.customer_installations.models import CustomerInstallation
from apps.barangays.models import Barangay
from apps.lcp.models import LCP, Splitter, NAP
from apps.routers.models import Router
from .models import Ticket, TicketComment


class TicketModelTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = CustomUser.objects.create_user(
            email='staff@test.com',
            password='testpass123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create test customer
        self.barangay = Barangay.objects.create(name='Test Barangay')
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            phone_primary='09123456789',
            barangay=self.barangay
        )
        
        # Create test installation
        self.lcp = LCP.objects.create(
            name='Test LCP',
            code='LCP001',
            location='Test Location',
            barangay=self.barangay
        )
        self.splitter = Splitter.objects.create(
            lcp=self.lcp,
            code='SPL001',
            type='1:8'
        )
        self.nap = NAP.objects.create(
            splitter=self.splitter,
            splitter_port=1,
            code='NAP001',
            name='Test NAP',
            location='Test NAP Location',
            port_capacity=8
        )
        self.router = Router.objects.create(
            serial_number='RTR001',
            model='Test Router'
        )
        self.installation = CustomerInstallation.objects.create(
            customer=self.customer,
            router=self.router,
            nap=self.nap,
            nap_port=1,
            installation_date=timezone.now().date()
        )
    
    def test_ticket_creation(self):
        ticket = Ticket.objects.create(
            customer=self.customer,
            customer_installation=self.installation,
            title='No Internet Connection',
            description='Customer reports complete loss of internet',
            category='no_connection',
            priority='high',
            source='phone',
            reported_by=self.user
        )
        
        self.assertTrue(ticket.ticket_number.startswith('TKT-'))
        self.assertEqual(ticket.status, 'pending')
        self.assertIsNone(ticket.resolved_at)
    
    def test_ticket_number_generation(self):
        # Create multiple tickets
        ticket1 = Ticket.objects.create(
            customer=self.customer,
            customer_installation=self.installation,
            title='Test 1',
            description='Test',
            reported_by=self.user
        )
        ticket2 = Ticket.objects.create(
            customer=self.customer,
            customer_installation=self.installation,
            title='Test 2',
            description='Test',
            reported_by=self.user
        )
        
        year = timezone.now().year
        self.assertEqual(ticket1.ticket_number, f'TKT-{year}-0001')
        self.assertEqual(ticket2.ticket_number, f'TKT-{year}-0002')
    
    def test_ticket_resolution(self):
        ticket = Ticket.objects.create(
            customer=self.customer,
            customer_installation=self.installation,
            title='Test Ticket',
            description='Test',
            reported_by=self.user
        )
        
        # Resolve ticket
        ticket.status = 'resolved'
        ticket.resolution_notes = 'Fixed the issue'
        ticket.save()
        
        self.assertIsNotNone(ticket.resolved_at)
        self.assertEqual(ticket.status, 'resolved')


class TicketViewTest(TestCase):
    def setUp(self):
        # Create test users
        self.staff_user = CustomUser.objects.create_user(
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        self.client.login(email='staff@test.com', password='testpass123')
        
        # Set up test data (same as model test)
        self.barangay = Barangay.objects.create(name='Test Barangay')
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            phone_primary='09123456789',
            barangay=self.barangay
        )
        
        # Create installation
        self.lcp = LCP.objects.create(
            name='Test LCP',
            code='LCP001',
            location='Test Location',
            barangay=self.barangay
        )
        self.splitter = Splitter.objects.create(
            lcp=self.lcp,
            code='SPL001',
            type='1:8'
        )
        self.nap = NAP.objects.create(
            splitter=self.splitter,
            splitter_port=1,
            code='NAP001',
            name='Test NAP',
            location='Test NAP Location',
            port_capacity=8
        )
        self.router = Router.objects.create(
            serial_number='RTR001',
            model='Test Router'
        )
        self.installation = CustomerInstallation.objects.create(
            customer=self.customer,
            router=self.router,
            nap=self.nap,
            nap_port=1,
            installation_date=timezone.now().date()
        )
    
    def test_ticket_list_view(self):
        response = self.client.get(reverse('tickets:ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/ticket_list.html')
    
    def test_ticket_create_view(self):
        response = self.client.get(reverse('tickets:ticket_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/ticket_form.html')
    
    def test_ticket_creation_post(self):
        data = {
            'customer': self.customer.id,
            'customer_installation': self.installation.id,
            'title': 'Test Ticket',
            'description': 'Test description',
            'category': 'no_connection',
            'priority': 'high',
            'source': 'phone',
            'status': 'pending',
        }
        response = self.client.post(reverse('tickets:ticket_create'), data)
        
        # Should redirect to ticket detail
        self.assertEqual(response.status_code, 302)
        
        # Check ticket was created
        ticket = Ticket.objects.get(title='Test Ticket')
        self.assertEqual(ticket.reported_by, self.staff_user)
        self.assertEqual(ticket.customer, self.customer)
