from django.db import models
from django.utils import timezone
from apps.utils.models import BaseModel, GeoLocatedModel
from apps.customers.models import Customer
from apps.routers.models import Router
from apps.users.models import CustomUser


class CustomerInstallation(BaseModel, GeoLocatedModel):
    """Model for tracking customer installations and their status."""
    
    # Status choices
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),  # Temporary suspension
        ('TERMINATED', 'Terminated'),  # Permanent termination
    ]
    
    # Basic Information
    customer = models.OneToOneField(
        Customer, 
        on_delete=models.PROTECT,
        related_name='installation',
        help_text="Customer this installation belongs to"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this installation is active"
    )
    
    # Installation details
    router = models.ForeignKey(
        Router, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        help_text="Router assigned to this installation"
    )
    installation_date = models.DateField(
        default=timezone.now,
        help_text="Date when the installation was completed"
    )
    installation_technician = models.ForeignKey(
        CustomUser, 
        on_delete=models.PROTECT,
        related_name='installations_performed',
        help_text="Technician who performed the installation"
    )
    installation_notes = models.TextField(
        blank=True,
        help_text="Additional notes about the installation"
    )
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE',
        help_text="Current status of the installation"
    )
    
    class Meta:
        ordering = ['-installation_date']
        verbose_name = "Customer Installation"
        verbose_name_plural = "Customer Installations"
    
    def __str__(self):
        return f"{self.customer.full_name} - Installation ({self.get_status_display()})"
    
    @property
    def current_subscription(self):
        """Get the active subscription if any."""
        from apps.customer_subscriptions.models import CustomerSubscription
        now = timezone.now()
        return self.subscriptions.filter(
            start_date__lte=now,
            end_date__gte=now,
            is_paid=True
        ).first()
    
    @property
    def is_expired(self):
        """Check if customer has no active subscription."""
        return self.current_subscription is None
    
    @property
    def days_until_expiry(self):
        """Get days until current subscription expires."""
        if self.current_subscription:
            delta = self.current_subscription.end_date - timezone.now()
            return delta.days
        return None
    
    @property
    def last_subscription(self):
        """Get the most recent subscription."""
        return self.subscriptions.order_by('-end_date').first()
