from django.db import models
from django.utils import timezone
from apps.utils.models import BaseModel, GeoLocatedModel
from apps.customers.models import Customer
from apps.routers.models import Router
from apps.users.models import CustomUser
from apps.lcp.models import NAP


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
    
    # NAP Connection
    nap = models.ForeignKey(
        NAP,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='customer_installations',
        help_text="NAP (Network Access Point) where customer is connected"
    )
    nap_port = models.IntegerField(
        null=True,
        blank=True,
        help_text="Port number on the NAP (1-N based on NAP capacity)"
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
    
    class Meta:
        ordering = ['-installation_date']
        verbose_name = "Customer Installation"
        verbose_name_plural = "Customer Installations"
        # Ensure unique port assignment per NAP
        unique_together = [['nap', 'nap_port']]
    
    def __str__(self):
        return f"{self.customer.full_name} - Installation ({self.get_status_display()})"
    
    def clean(self):
        """Validate NAP port assignment"""
        from django.core.exceptions import ValidationError
        
        if self.nap and self.nap_port:
            # Check if port is within NAP capacity
            if self.nap_port < 1 or self.nap_port > self.nap.port_capacity:
                raise ValidationError({
                    'nap_port': f'Port must be between 1 and {self.nap.port_capacity}'
                })
            
            # Check if port is already taken (excluding current installation)
            existing = CustomerInstallation.objects.filter(
                nap=self.nap,
                nap_port=self.nap_port
            ).exclude(pk=self.pk if self.pk else None)
            
            if existing.exists():
                raise ValidationError({
                    'nap_port': f'Port {self.nap_port} is already occupied by {existing.first().customer.get_full_name()}'
                })
        elif self.nap and not self.nap_port:
            raise ValidationError({
                'nap_port': 'Port number is required when NAP is selected'
            })
        elif not self.nap and self.nap_port:
            raise ValidationError({
                'nap': 'NAP is required when port number is specified'
            })
    
    def save(self, *args, **kwargs):
        """Validate before saving"""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def nap_connection_display(self):
        """Display NAP connection info"""
        if self.nap and self.nap_port:
            return f"{self.nap.code} - Port {self.nap_port}"
        return "Not connected"
    
    @property
    def network_path(self):
        """Get the full network path from LCP to customer"""
        if self.nap:
            return {
                'lcp': self.nap.splitter.lcp.code,
                'splitter': self.nap.splitter.code,
                'splitter_port': self.nap.splitter_port,
                'nap': self.nap.code,
                'nap_port': self.nap_port
            }
        return None
