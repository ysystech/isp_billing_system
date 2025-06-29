from decimal import Decimal
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.utils.models import TenantAwareModel
from apps.customer_installations.models import CustomerInstallation
from apps.subscriptions.models import SubscriptionPlan


class CustomerSubscription(TenantAwareModel):
    """
    Prepaid subscription model where customers pay upfront for service time.
    Supports full month, half month (15 days), or custom payment amounts.
    """
    
    SUBSCRIPTION_TYPES = [
        ('one_month', '1 Month'),
        ('fifteen_days', '15 Days'),
        ('custom', 'Custom Amount')
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled')
    ]
    
    # Relationships
    customer_installation = models.ForeignKey(
        CustomerInstallation, 
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    subscription_plan = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.PROTECT
    )
    
    # Subscription type and amount
    subscription_type = models.CharField(
        max_length=20, 
        choices=SUBSCRIPTION_TYPES,
        help_text="Type of subscription payment"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Amount paid by customer"
    )
    
    # DateTime fields for precise tracking
    start_date = models.DateTimeField(help_text="When the subscription starts")
    end_date = models.DateTimeField(help_text="When the subscription ends")
    
    # Calculated days (stored as decimal for partial days)
    days_added = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Number of days added (can be fractional)"
    )
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    
    # Additional fields
    notes = models.TextField(blank=True)
    
    # Tracking who created this
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.PROTECT,
        related_name='subscriptions_created'
    )
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['customer_installation', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        permissions = [
            ("view_subscription_list", "Can view subscription list"),
            ("view_subscription_detail", "Can view subscription details"),
            ("create_subscription", "Can create new subscription"),
            ("process_payment", "Can process subscription payment"),
            ("generate_receipt", "Can generate payment receipt"),
            ("cancel_subscription", "Can cancel subscription"),
            ("view_payment_history", "Can view payment history"),
            ("export_subscription_data", "Can export subscription data"),
            ("view_financial_summary", "Can view financial summary"),
            ("process_refund", "Can process subscription refund"),
        ]
    
    def __str__(self):
        return f"{self.customer_installation.customer.full_name} - {self.subscription_plan.name} ({self.get_subscription_type_display()})"
    
    def clean(self):
        """Validate the subscription data before saving."""
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError("End date must be after start date.")
    
    def save(self, *args, **kwargs):
        """Override save to calculate end_date and days_added."""
        if not self.pk:  # Only on creation
            self.calculate_subscription_details()
        
        # Update status if expired
        self.update_status()
        
        super().save(*args, **kwargs)
        
        # Update installation status
        self.update_installation_status()
    
    def calculate_subscription_details(self):
        """Calculate days_added and end_date based on subscription type and amount."""
        plan_price = self.subscription_plan.price
        
        if self.subscription_type == 'one_month':
            self.days_added = Decimal('30')
            self.amount = plan_price
        elif self.subscription_type == 'fifteen_days':
            self.days_added = Decimal('15')
            self.amount = plan_price / 2
        else:  # custom
            # Formula: (amount / plan_price) * 30 = days_added
            self.days_added = (self.amount / plan_price) * 30
        
        # Calculate end_date with time precision
        # Convert days_added to timedelta
        days = int(self.days_added)
        hours = (self.days_added - days) * 24
        minutes = (hours - int(hours)) * 60
        
        time_to_add = timedelta(days=days, hours=int(hours), minutes=int(minutes))
        self.end_date = self.start_date + time_to_add
    
    @property
    def is_active(self):
        """Check if subscription is currently active."""
        now = timezone.now()
        return self.status == 'ACTIVE' and self.start_date <= now <= self.end_date
    
    @property
    def is_expired(self):
        """Check if subscription has expired."""
        return timezone.now() > self.end_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining in subscription."""
        if self.status in ['EXPIRED', 'CANCELLED']:
            return 0
        
        remaining = self.end_date - timezone.now()
        if remaining.total_seconds() <= 0:
            return 0
            
        return remaining.total_seconds() / 86400  # Convert to decimal days
    
    @property
    def time_remaining_display(self):
        """Get human-readable time remaining."""
        if self.status in ['EXPIRED', 'CANCELLED']:
            return "Expired"
        
        remaining = self.end_date - timezone.now()
        
        # Check if already expired
        if remaining.total_seconds() <= 0:
            return "Expired"
        
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0 and days == 0:  # Only show minutes if less than a day
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        
        return ", ".join(parts) if parts else "Less than a minute"
    
    def update_status(self):
        """Update status based on dates."""
        if self.status != 'CANCELLED' and self.is_expired:
            self.status = 'EXPIRED'
    
    def update_installation_status(self):
        """Update the installation status based on active subscriptions."""
        installation = self.customer_installation
        
        # Check if there are any active subscriptions
        active_subs = installation.subscriptions.filter(
            status='ACTIVE',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).exists()
        
        # Update installation status
        if not active_subs and installation.status == 'ACTIVE':
            installation.status = 'INACTIVE'
            installation.save()
        elif active_subs and installation.status == 'INACTIVE':
            installation.status = 'ACTIVE'
            installation.save()
    
    @classmethod
    def get_latest_subscription(cls, customer_installation):
        """Get the latest subscription for an installation."""
        return cls.objects.filter(
            customer_installation=customer_installation
        ).order_by('-end_date').first()
    
    @classmethod
    def calculate_preview(cls, plan_price, amount, subscription_type):
        """
        Calculate preview of days that will be added.
        Returns a dictionary with days, hours, minutes.
        """
        if subscription_type == 'one_month':
            days_added = Decimal('30')
        elif subscription_type == 'fifteen_days':
            days_added = Decimal('15')
        else:  # custom
            days_added = (Decimal(str(amount)) / plan_price) * 30
        
        # Convert to days, hours, minutes
        days = int(days_added)
        hours = (days_added - days) * 24
        minutes = (hours - int(hours)) * 60
        
        return {
            'total_days': float(days_added),
            'days': days,
            'hours': int(hours),
            'minutes': int(minutes),
            'display': f"{days} days, {int(hours)} hours, {int(minutes)} minutes"
        }
