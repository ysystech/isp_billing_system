from django.db import models
from django.urls import reverse

from apps.users.models import CustomUser
from apps.utils.models import BaseModel, GeoLocatedModel
from apps.barangays.models import Barangay


class Customer(BaseModel, GeoLocatedModel):
    """
    Customer model representing ISP service subscribers
    """
    
    # Account status choices
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    
    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
        (SUSPENDED, "Suspended"),
        (TERMINATED, "Terminated"),
    ]
    
    # Link to user account
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.PROTECT,
        related_name="customer_profile",
        null=True,
        blank=True,
        help_text="Linked user account for customer portal access"
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # Contact Information
    email = models.EmailField(unique=True)
    phone_primary = models.CharField(max_length=20)
    
    # Service Address
    street_address = models.CharField(max_length=255)
    barangay = models.ForeignKey(
        Barangay,
        on_delete=models.PROTECT,
        related_name="customers",
        help_text="Customer's barangay"
    )
    
    # Account Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=ACTIVE
    )
    
    # Additional Information
    notes = models.TextField(blank=True, help_text="Internal notes about the customer")
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["status"]),
            models.Index(fields=["last_name", "first_name"]),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return customer's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_complete_address(self):
        """Return formatted complete address"""
        return f"{self.street_address}, {self.barangay.name}"
    
    def get_absolute_url(self):
        """Return the URL for customer detail view"""
        return reverse("customers:customer_detail", kwargs={"pk": self.pk})
    
    @property
    def is_active(self):
        """Check if customer account is active"""
        return self.status == self.ACTIVE
    
    @property
    def full_name(self):
        """Return customer's full name (property for compatibility)"""
        return self.get_full_name()
