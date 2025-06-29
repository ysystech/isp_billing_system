from django.db import models
from django.utils import timezone
from apps.utils.models import TenantAwareModel, BaseModel
from apps.customers.models import Customer
from apps.customer_installations.models import CustomerInstallation
from apps.users.models import CustomUser


class Ticket(TenantAwareModel):
    """Support ticket model for tracking customer issues and requests."""
    
    CATEGORY_CHOICES = [
        ('no_connection', 'No Internet Connection'),
        ('slow_connection', 'Slow Internet Speed'),
        ('intermittent', 'Intermittent Connection'),
        ('router_issue', 'Router/Equipment Problem'),
        ('billing', 'Billing Inquiry'),
        ('relocation', 'Relocation Request'),
        ('upgrade', 'Plan Upgrade Request'),
        ('downgrade', 'Plan Downgrade Request'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]
    
    SOURCE_CHOICES = [
        ('phone', 'Phone Call'),
        ('messenger', 'Facebook Messenger'),
        ('walk_in', 'Walk-in'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('other', 'Other'),
    ]
    
    # Required fields
    ticket_number = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        help_text="Auto-generated ticket number"
    )
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.PROTECT,
        related_name='tickets'
    )
    customer_installation = models.ForeignKey(
        CustomerInstallation,
        on_delete=models.PROTECT,
        related_name='tickets'
    )
    title = models.CharField(
        max_length=200,
        help_text="Brief description of the issue"
    )
    description = models.TextField(
        help_text="Detailed description of the issue"
    )
    
    # Choice fields
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='phone'
    )
    
    # User relationships
    reported_by = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='tickets_created',
        help_text="Staff member who created the ticket"
    )
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='tickets_assigned',
        null=True,
        blank=True,
        help_text="Technician assigned to resolve the ticket"
    )
    
    # Timestamp fields
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the ticket was resolved"
    )
    
    # Resolution details
    resolution_notes = models.TextField(
        blank=True,
        help_text="Notes about how the issue was resolved"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]
        permissions = [
            ("view_ticket_list", "Can view ticket list"),
            ("view_ticket_detail", "Can view ticket details"),
            ("create_ticket", "Can create new ticket"),
            ("assign_ticket", "Can assign ticket to technician"),
            ("change_ticket_status", "Can change ticket status"),
            ("change_ticket_priority", "Can change ticket priority"),
            ("add_ticket_comment", "Can add comments to tickets"),
            ("view_all_tickets", "Can view all tickets (not just assigned)"),
            ("export_ticket_data", "Can export ticket data"),
            ("remove_ticket", "Can remove ticket"),  # Changed from delete_ticket
        ]
    
    def __str__(self):
        return f"{self.ticket_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Generate ticket number if not set
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        
        # Set resolved_at when status changes to resolved
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != 'resolved':
            self.resolved_at = None
        
        super().save(*args, **kwargs)
    
    def generate_ticket_number(self):
        """Generate a unique ticket number in format TKT-YYYY-NNNN."""
        year = timezone.now().year
        
        # Get the last ticket of the current year
        last_ticket = Ticket.objects.filter(
            ticket_number__startswith=f'TKT-{year}-'
        ).order_by('ticket_number').last()
        
        if last_ticket:
            # Extract the number part and increment
            last_number = int(last_ticket.ticket_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f'TKT-{year}-{new_number:04d}'
    
    @property
    def is_overdue(self):
        """Check if ticket is overdue based on priority."""
        if self.status in ['resolved', 'cancelled']:
            return False
        
        # Define SLA in hours
        sla_hours = {
            'urgent': 4,
            'high': 8,
            'medium': 24,
            'low': 48,
        }
        
        hours_passed = (timezone.now() - self.created_at).total_seconds() / 3600
        return hours_passed > sla_hours.get(self.priority, 48)
    
    @property
    def response_time(self):
        """Calculate response time if resolved."""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None
    
    @property
    def status_color(self):
        """Return color class for status."""
        colors = {
            'pending': 'warning',
            'assigned': 'info',
            'in_progress': 'primary',
            'resolved': 'success',
            'cancelled': 'error',
        }
        return colors.get(self.status, 'neutral')
    
    @property
    def priority_color(self):
        """Return color class for priority."""
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'error',
            'urgent': 'error',
        }
        return colors.get(self.priority, 'neutral')


class TicketComment(BaseModel):
    """Comments and updates on tickets."""
    
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='ticket_comments'
    )
    comment = models.TextField()
    
    class Meta:
        ordering = ['created_at']
        permissions = [
            ("view_ticket_comments", "Can view ticket comments"),
            ("delete_any_comment", "Can delete any comment"),
        ]
    
    def __str__(self):
        return f"Comment on {self.ticket.ticket_number} by {self.user.get_full_name()}"
