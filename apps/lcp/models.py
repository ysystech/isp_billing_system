from django.db import models
from django.core.exceptions import ValidationError
from apps.utils.models import TenantAwareModel, GeoLocatedModel


class LCP(TenantAwareModel, GeoLocatedModel):
    """Local Convergence Point - Main distribution point"""
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=50,
        help_text="Unique identifier (e.g., LCP-001)"
    )
    location = models.TextField(help_text="Physical address or description")
    barangay = models.ForeignKey(
        'barangays.Barangay', 
        on_delete=models.PROTECT,
        related_name='lcps'
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    coverage_radius_meters = models.IntegerField(
        default=1000,
        help_text="Approximate coverage area radius in meters"
    )

    class Meta:
        verbose_name = "LCP"
        verbose_name_plural = "LCPs"
        ordering = ['code']
        unique_together = [
            ["tenant", "name"],
            ["tenant", "code"],
        ]
        permissions = [
            ("view_lcp_list", "Can view LCP list"),
            ("view_lcp_detail", "Can view LCP details"),
            ("manage_lcp_infrastructure", "Can manage LCP infrastructure"),
            ("view_lcp_map", "Can view LCP on map"),
            ("export_lcp_data", "Can export LCP data"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Splitter(TenantAwareModel, GeoLocatedModel):
    """Optical splitter that divides fiber signal"""
    lcp = models.ForeignKey(
        LCP, 
        on_delete=models.CASCADE, 
        related_name='splitters'
    )
    code = models.CharField(
        max_length=50,
        help_text="Splitter identifier (e.g., SP-001)"
    )
    type = models.CharField(
        max_length=20, 
        choices=[
            ('1:4', '1:4 (4 ports)'),
            ('1:8', '1:8 (8 ports)'),
            ('1:16', '1:16 (16 ports)'),
            ('1:32', '1:32 (32 ports)'),
            ('1:64', '1:64 (64 ports)'),
        ],
        help_text="Splitter ratio"
    )
    location = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Specific location within LCP or elsewhere"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['lcp', 'code']
        ordering = ['lcp', 'code']
        permissions = [
            ("view_splitter_list", "Can view splitter list"),
            ("view_splitter_detail", "Can view splitter details"),
            ("manage_splitter_ports", "Can manage splitter ports"),
        ]

    def __str__(self):
        return f"{self.lcp.code} - {self.code} ({self.type})"

    @property
    def port_capacity(self):
        """Get the number of output ports from splitter type"""
        return int(self.type.split(':')[1])

    @property
    def used_ports(self):
        """Get count of ports that have NAPs connected"""
        return self.naps.filter(is_active=True).count()

    @property
    def available_ports(self):
        """Get count of available ports"""
        return self.port_capacity - self.used_ports


class NAP(TenantAwareModel, GeoLocatedModel):
    """Network Access Point - Secondary distribution point"""
    splitter = models.ForeignKey(
        Splitter, 
        on_delete=models.CASCADE, 
        related_name='naps'
    )
    splitter_port = models.IntegerField(
        help_text="Which output port on the splitter (1-N)"
    )
    code = models.CharField(
        max_length=50,
        help_text="NAP identifier (e.g., NAP-001)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Descriptive name for the NAP"
    )
    location = models.TextField(help_text="Physical location of the NAP box")
    port_capacity = models.IntegerField(
        default=8,
        help_text="Number of customer ports in this NAP"
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    max_distance_meters = models.IntegerField(
        default=100,
        help_text="Maximum recommended customer distance in meters"
    )
    
    class Meta:
        verbose_name = "NAP"
        verbose_name_plural = "NAPs"
        unique_together = ['splitter', 'code']  # Changed from splitter_port to code
        ordering = ['splitter__lcp', 'splitter', 'splitter_port']
        permissions = [
            ("view_nap_list", "Can view NAP list"),
            ("view_nap_detail", "Can view NAP details"),
            ("manage_nap_ports", "Can manage NAP ports"),
            ("view_nap_availability", "Can view NAP port availability"),
        ]

    def __str__(self):
        return f"{self.splitter.lcp.code} > {self.splitter.code} (Port {self.splitter_port}) > {self.code}"

    def clean(self):
        """Validate that splitter_port is within the splitter's capacity"""
        if self.splitter_id and self.splitter_port:  # Check if splitter is set
            if self.splitter_port < 1 or self.splitter_port > self.splitter.port_capacity:
                raise ValidationError(
                    f"Splitter port must be between 1 and {self.splitter.port_capacity} "
                    f"for {self.splitter.type} splitter"
                )

    @property
    def connection_path(self):
        """Get the full connection path from LCP to NAP"""
        return f"{self.splitter.lcp.name} > {self.splitter.code} (Port {self.splitter_port}) > {self.name}"

    @property
    def used_ports(self):
        """Get count of ports that have installations connected"""
        return self.customer_installations.filter(status='ACTIVE').count()

    @property
    def available_ports(self):
        """Get count of available ports"""
        return self.port_capacity - self.used_ports
