from django.db import models
from django.core.validators import RegexValidator
from apps.utils.models import BaseModel


class Router(BaseModel):
    """Model for tracking routers deployed to customers"""
    
    # Basic Information
    brand = models.CharField(
        max_length=50,
        help_text="Router manufacturer (e.g., TP-Link, Mikrotik, Ubiquiti)"
    )
    model = models.CharField(
        max_length=100,
        blank=True,
        help_text="Router model number"
    )
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique serial number from manufacturer"
    )
    
    # MAC Address field with validation
    mac_address = models.CharField(
        max_length=17,
        unique=True,
        null=True,  # Temporarily nullable for migration
        blank=True,  # Temporarily optional for migration
        validators=[
            RegexValidator(
                regex=r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
                message='Enter a valid MAC address (e.g., 00:11:22:33:44:55 or 00-11-22-33-44-55)'
            )
        ],
        help_text="MAC address of the router (e.g., 00:11:22:33:44:55)"
    )
    
    # Additional Information
    notes = models.TextField(
        blank=True,
        help_text="Any additional notes about this router"
    )
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["serial_number"]),
        ]
    
    def __str__(self):
        return f"{self.brand} {self.model} - {self.serial_number}" if self.model else f"{self.brand} - {self.serial_number}"
