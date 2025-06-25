from django.db import models
from django.urls import reverse

from apps.users.models import CustomUser
from apps.utils.models import BaseModel


class Customer(BaseModel):
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
    
    # Barangay choices for Cagayan de Oro
    BARANGAY_CHOICES = [
        # Urban Barangays (Poblacion)
        ("1", "Barangay 1"),
        ("2", "Barangay 2"),
        ("3", "Barangay 3"),
        ("4", "Barangay 4"),
        ("5", "Barangay 5"),
        ("6", "Barangay 6"),
        ("7", "Barangay 7"),
        ("8", "Barangay 8"),
        ("9", "Barangay 9"),
        ("10", "Barangay 10"),
        ("11", "Barangay 11"),
        ("12", "Barangay 12"),
        ("13", "Barangay 13"),
        ("14", "Barangay 14"),
        ("15", "Barangay 15"),
        ("16", "Barangay 16"),
        ("17", "Barangay 17"),
        ("18", "Barangay 18"),
        ("19", "Barangay 19"),
        ("20", "Barangay 20"),
        ("21", "Barangay 21"),
        ("22", "Barangay 22"),
        ("23", "Barangay 23"),
        ("24", "Barangay 24"),
        ("25", "Barangay 25"),
        ("26", "Barangay 26"),
        ("27", "Barangay 27"),
        ("28", "Barangay 28"),
        ("29", "Barangay 29"),
        ("30", "Barangay 30"),
        ("31", "Barangay 31"),
        ("32", "Barangay 32"),
        ("33", "Barangay 33"),
        ("34", "Barangay 34"),
        ("35", "Barangay 35"),
        ("36", "Barangay 36"),
        ("37", "Barangay 37"),
        ("38", "Barangay 38"),
        ("39", "Barangay 39"),
        ("40", "Barangay 40"),
        # Major Barangays
        ("Agusan", "Agusan"),
        ("Balulang", "Balulang"),
        ("Bayabas", "Bayabas"),
        ("Bonbon", "Bonbon"),
        ("Bugo", "Bugo"),
        ("Bulua", "Bulua"),
        ("Camaman-an", "Camaman-an"),
        ("Canitoan", "Canitoan"),
        ("Carmen", "Carmen"),
        ("Consolacion", "Consolacion"),
        ("Cugman", "Cugman"),
        ("Gusa", "Gusa"),
        ("Iponan", "Iponan"),
        ("Kauswagan", "Kauswagan"),
        ("Lapasan", "Lapasan"),
        ("Lumbia", "Lumbia"),
        ("Macabalan", "Macabalan"),
        ("Macasandig", "Macasandig"),
        ("Nazareth", "Nazareth"),
        ("Patag", "Patag"),
        ("Puerto", "Puerto"),
        ("Puntod", "Puntod"),
        ("Tablon", "Tablon"),
        ("Tagoloan", "Tagoloan"),
        ("Taglimao", "Taglimao"),
        ("Tignapoloan", "Tignapoloan"),
        # Other Barangays
        ("Balubal", "Balubal"),
        ("Bayanga", "Bayanga"),
        ("Besigan", "Besigan"),
        ("Baikingon", "Baikingon"),
        ("Dansolihon", "Dansolihon"),
        ("F.S. Catanico", "F.S. Catanico"),
        ("Indahag", "Indahag"),
        ("Mambuaya", "Mambuaya"),
        ("Pagalungan", "Pagalungan"),
        ("Pagatpat", "Pagatpat"),
        ("Pigsag-an", "Pigsag-an"),
        ("San Simon", "San Simon"),
        ("Tuburan", "Tuburan"),
        ("Tumpagon", "Tumpagon"),
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
    barangay = models.CharField(max_length=50, choices=BARANGAY_CHOICES)
    
    # Installation Details
    installation_date = models.DateField(null=True, blank=True)
    installation_notes = models.TextField(blank=True)
    installation_technician = models.CharField(max_length=100, blank=True)
    
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
        return f"{self.street_address}, {self.barangay}"
    
    def get_absolute_url(self):
        """Return the URL for customer detail view"""
        return reverse("customers:customer_detail", kwargs={"pk": self.pk})
    
    @property
    def is_active(self):
        """Check if customer account is active"""
        return self.status == self.ACTIVE
