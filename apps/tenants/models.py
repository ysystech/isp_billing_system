from django.db import models
from apps.utils.models import BaseModel


class Tenant(BaseModel):
    """Multi-tenant organization/company"""
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_by = models.OneToOneField(
        'users.CustomUser',
        on_delete=models.PROTECT,
        related_name='owned_tenant',
        null=True,  # Temporarily nullable for migration
        blank=True
    )
    
    class Meta:
        db_table = 'tenants'
        ordering = ['name']
    
    def __str__(self):
        return self.name
