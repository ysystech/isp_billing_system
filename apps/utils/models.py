from django.db import models
from decimal import Decimal


class BaseModel(models.Model):
    """
    Base model that includes default created / updated timestamps.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GeoLocatedModel(models.Model):
    """
    Abstract base model for any model that needs geographic coordinates.
    Provides latitude/longitude fields and location-related utilities.
    """
    
    LOCATION_ACCURACY_CHOICES = [
        ('exact', 'Exact GPS'),
        ('approximate', 'Approximate'),
        ('address', 'From Address'),
        ('manual', 'Manual Entry'),
    ]
    
    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text="Latitude coordinate (e.g., 8.4542363)"
    )
    longitude = models.DecimalField(
        max_digits=11, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text="Longitude coordinate (e.g., 124.6318977)"
    )
    location_accuracy = models.CharField(
        max_length=50, 
        blank=True,
        choices=LOCATION_ACCURACY_CHOICES,
        default='manual',
        help_text="How the location was determined"
    )
    location_notes = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Additional notes about the location (landmark, building, etc.)"
    )
    
    class Meta:
        abstract = True
    
    @property
    def has_coordinates(self):
        """Check if this model has valid coordinates"""
        return self.latitude is not None and self.longitude is not None
    
    @property
    def coordinates(self):
        """Return coordinates as a tuple (lat, lng) or None"""
        if self.has_coordinates:
            return (float(self.latitude), float(self.longitude))
        return None
    
    @property
    def coordinates_display(self):
        """Return formatted coordinates for display"""
        if self.has_coordinates:
            return f"{self.latitude:.6f}, {self.longitude:.6f}"
        return "No coordinates set"
    
    def distance_to(self, other):
        """
        Calculate approximate distance to another GeoLocatedModel in meters.
        Uses simplified calculation suitable for small distances.
        """
        if not (self.has_coordinates and hasattr(other, 'has_coordinates') and other.has_coordinates):
            return None
            
        # Approximate calculation for small distances
        # At CDO latitude (~8.45°), 1 degree ≈ 111km
        lat_diff = float(self.latitude - other.latitude)
        lng_diff = float(self.longitude - other.longitude)
        
        # Simple Pythagorean theorem (accurate enough for <10km)
        lat_meters = lat_diff * 111320  # meters per degree latitude
        lng_meters = lng_diff * 110540  # meters per degree longitude at CDO latitude
        
        distance = (lat_meters ** 2 + lng_meters ** 2) ** 0.5
        return round(distance, 2)
        
        distance = (lat_meters ** 2 + lng_meters ** 2) ** 0.5
        return round(distance, 2)


class TenantAwareModel(BaseModel):
    """
    Abstract base model that adds tenant awareness to any model.
    All models that need to be isolated by tenant should inherit from this.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant']),
        ]
