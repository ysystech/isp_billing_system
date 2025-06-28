from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from apps.tickets.models import Ticket, TicketComment
from apps.customers.models import Customer
from apps.customer_installations.models import CustomerInstallation
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = 'Generate sample tickets for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of tickets to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get all customers with installations
        installations = CustomerInstallation.objects.select_related('customer').all()
        if not installations:
            self.stdout.write(self.style.ERROR('No customer installations found. Please create some first.'))
            return
        
        # Get staff users for assignment
        staff_users = CustomUser.objects.filter(is_staff=True)
        if not staff_users:
            self.stdout.write(self.style.ERROR('No staff users found. Please create some first.'))
            return
        
        # Sample data
        issues = [
            ('no_connection', 'No Internet Connection', [
                'Complete loss of internet connectivity since this morning',
                'Internet suddenly stopped working',
                'No internet for the past 2 hours',
                'Cannot connect to the internet at all'
            ]),
            ('slow_connection', 'Slow Internet Speed', [
                'Internet speed is very slow, getting only 1-2 Mbps',
                'Experiencing very slow browsing speeds',
                'Download speed is much slower than usual',
                'Video streaming is constantly buffering'
            ]),
            ('intermittent', 'Intermittent Connection', [
                'Internet keeps disconnecting every few minutes',
                'Connection drops frequently throughout the day',
                'WiFi keeps disconnecting and reconnecting',
                'Unstable connection, especially during evening'
            ]),
            ('router_issue', 'Router Problem', [
                'Router lights are blinking red',
                'Router keeps restarting on its own',
                'Cannot access router settings',
                'Router is making strange noises'
            ]),
            ('billing', 'Billing Inquiry', [
                'Question about last month\'s bill',
                'Want to know about payment options',
                'Inquiry about subscription renewal',
                'Need clarification on charges'
            ]),
            ('upgrade', 'Plan Upgrade Request', [
                'Want to upgrade to a faster plan',
                'Interested in upgrading internet speed',
                'Request to change to unlimited plan',
                'Looking for business plan options'
            ]),
        ]
        
        priorities = ['low', 'medium', 'high', 'urgent']
        sources = ['phone', 'messenger', 'walk_in', 'email']
        
        created_count = 0
        
        for i in range(count):
            # Random installation
            installation = random.choice(installations)
            
            # Random issue
            category, title_template, descriptions = random.choice(issues)
            
            # Random dates (tickets from last 30 days)
            created_date = timezone.now() - timedelta(days=random.randint(0, 30))
            
            # Create ticket
            ticket = Ticket.objects.create(
                customer=installation.customer,
                customer_installation=installation,
                title=f"{title_template} - {installation.customer.full_name}",
                description=random.choice(descriptions),
                category=category,
                priority=random.choice(priorities),
                source=random.choice(sources),
                reported_by=random.choice(staff_users),
                created_at=created_date,
                updated_at=created_date
            )
            
            # Assign some tickets
            if random.random() > 0.3:  # 70% chance of assignment
                ticket.assigned_to = random.choice(staff_users)
                ticket.status = random.choice(['assigned', 'in_progress', 'resolved'])
                
                # If resolved, add resolution
                if ticket.status == 'resolved':
                    resolution_notes = [
                        'Issue resolved by restarting the router',
                        'Fixed by replacing faulty cable',
                        'Resolved by adjusting NAP connection',
                        'Issue was due to area maintenance, now fixed',
                        'Upgraded customer plan as requested',
                        'Billing inquiry resolved and explained to customer'
                    ]
                    ticket.resolution_notes = random.choice(resolution_notes)
                    ticket.resolved_at = created_date + timedelta(hours=random.randint(2, 48))
                
                ticket.save()
                
                # Add assignment comment
                TicketComment.objects.create(
                    ticket=ticket,
                    user=ticket.reported_by,
                    comment=f"Assigned to {ticket.assigned_to.get_full_name()}",
                    created_at=created_date + timedelta(minutes=30)
                )
            
            # Add some comments
            if random.random() > 0.5:  # 50% chance of comments
                comment_texts = [
                    'Customer called to follow up',
                    'Scheduled site visit for tomorrow',
                    'Waiting for customer to be available',
                    'Issue might be related to recent weather',
                    'Customer confirmed issue is resolved',
                    'Need to check NAP box for possible damage'
                ]
                
                for j in range(random.randint(1, 3)):
                    TicketComment.objects.create(
                        ticket=ticket,
                        user=random.choice(staff_users),
                        comment=random.choice(comment_texts),
                        created_at=created_date + timedelta(hours=random.randint(1, 24))
                    )
            
            created_count += 1
            
            if created_count % 5 == 0:
                self.stdout.write(f'Created {created_count} tickets...')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample tickets')
        )
