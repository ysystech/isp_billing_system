from datetime import timedelta
from django.db import models
from django.utils import timezone
from apps.utils.models import BaseModel
from apps.customer_installations.models import CustomerInstallation
from apps.subscriptions.models import SubscriptionPlan
from apps.users.models import CustomUser


class CustomerSubscription(BaseModel):
    """Model for tracking customer subscription payments (prepaid model)."""
    
    # Payment method choices
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('GCASH', 'GCash'),
        ('BANK', 'Bank Transfer'),
        ('OTHER', 'Other'),
    ]
    
    # Links
    installation = models.ForeignKey(
        CustomerInstallation, 
        on_delete=models.PROTECT,
        related_name='subscriptions',
        help_text="Customer installation this subscription belongs to"
    )
    plan = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.PROTECT,
        help_text="Subscription plan selected"
    )
    
    # Subscription Period
    start_date = models.DateTimeField(
        default=timezone.now,
        help_text="When this subscription period starts"
    )
    end_date = models.DateTimeField(
        help_text="When this subscription period ends (calculated from start_date + plan.day_count)"
    )
    
    # Payment Information
    amount_paid = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Actual amount paid by customer"
    )
    is_paid = models.BooleanField(
        default=True,
        help_text="Whether payment has been received (always True for prepaid)"
    )
    payment_date = models.DateTimeField(
        default=timezone.now,
        help_text="When payment was received"
    )
    
    # Payment details
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='CASH',
        help_text="Method of payment"
    )
    reference_number = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Reference number for GCash/Bank transfers"
    )
    
    # Metadata
    collected_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.PROTECT,
        related_name='subscriptions_collected',
        help_text="Cashier who processed this payment"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this subscription/payment"
    )
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = "Customer Subscription"
        verbose_name_plural = "Customer Subscriptions"
    
    def __str__(self):
        customer_name = self.installation.customer.full_name
        return f"{customer_name} - {self.plan.name} ({self.start_date.date()} to {self.end_date.date()})"
    
    def save(self, *args, **kwargs):
        """Auto-calculate end_date if not set."""
        if not self.end_date and self.start_date and self.plan:
            self.end_date = self.start_date + timedelta(days=self.plan.day_count)
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if this subscription is currently active."""
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.is_paid
    
    @property
    def days_remaining(self):
        """Get days remaining in this subscription."""
        if self.is_active:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    @property
    def is_expiring_soon(self):
        """Check if subscription expires within 3 days."""
        return self.is_active and self.days_remaining <= 3
