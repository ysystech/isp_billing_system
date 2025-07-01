from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.customers.models import Customer
from apps.tickets.models import Ticket

User = get_user_model()


class Command(BaseCommand):
    help = 'Show ticket categories and test ticket creation'

    def handle(self, *args, **options):
        self.stdout.write("\nTicket Categories:")
        for value, label in Ticket.CATEGORY_CHOICES:
            self.stdout.write(f"  {value}: {label}")
        
        self.stdout.write("\n\nTicket Priorities:")
        for value, label in Ticket.PRIORITY_CHOICES:
            self.stdout.write(f"  {value}: {label}")
        
        self.stdout.write("\n\nTicket Status Options:")
        for value, label in Ticket.STATUS_CHOICES:
            self.stdout.write(f"  {value}: {label}")
        
        # Show customer count
        customer_count = Customer.objects.count()
        self.stdout.write(f"\n\nTotal customers: {customer_count}")
        
        # Show customers with portal access
        customers_with_portal = Customer.objects.filter(user__isnull=False).count()
        self.stdout.write(f"Customers with portal access: {customers_with_portal}")
