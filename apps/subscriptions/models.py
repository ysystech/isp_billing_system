from django.db import models
from django.core.validators import MinValueValidator
from apps.utils.models import BaseModel


class SubscriptionPlan(BaseModel):
    """Model for internet subscription plans."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the subscription plan"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of what the plan includes"
    )
    speed = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Internet speed in Mbps"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price in PHP"
    )
    day_count = models.IntegerField(
        validators=[MinValueValidator(1)],
        default=30,
        help_text="Number of days this plan is valid for"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this plan is currently available for new subscriptions"
    )
    
    class Meta:
        ordering = ['price', 'name']
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        permissions = [
            ("view_subscriptionplan_list", "Can view subscription plan list"),
            ("change_subscriptionplan_pricing", "Can change plan pricing"),
            ("activate_deactivate_plans", "Can activate/deactivate plans"),
            ("create_promotional_plans", "Can create promotional plans"),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.speed}Mbps ({self.day_count} days, ₱{self.price})"
    
    @property
    def display_price(self):
        """Return formatted price with currency symbol."""
        return f"₱{self.price:,.2f}"
    
    @property
    def display_speed(self):
        """Return formatted speed."""
        return f"{self.speed} Mbps"
