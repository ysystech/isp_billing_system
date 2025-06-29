from django.db import models
from apps.utils.models import TenantAwareModel


class Barangay(TenantAwareModel):
    """Model for storing Barangay information"""
    
    name = models.CharField(
        max_length=100,
        help_text="Name of the barangay"
    )
    code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Optional barangay code for reporting"
    )
    description = models.TextField(
        blank=True,
        help_text="Additional notes or description about the barangay"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this barangay is currently active"
    )
    
    class Meta:
        ordering = ["name"]
        verbose_name = "Barangay"
        verbose_name_plural = "Barangays"
        permissions = [
            ("view_barangay_list", "Can view barangay list"),
            ("manage_barangay_status", "Can activate/deactivate barangays"),
            ("view_barangay_statistics", "Can view barangay statistics"),
        ]
        indexes = [
            models.Index(fields=["tenant", "name"]),
            models.Index(fields=["is_active"]),
        ]
        unique_together = [
            ["tenant", "name"],
            ["tenant", "code"],
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def customer_count(self):
        """Get the count of customers in this barangay"""
        return self.customers.filter(status="active").count()
    
    @property
    def total_customer_count(self):
        """Get the total count of all customers in this barangay"""
        return self.customers.count()
