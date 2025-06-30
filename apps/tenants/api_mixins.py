"""
Mixins for tenant-aware API views.
"""
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, NotFound
from django.http import Http404


class TenantAPIFilterMixin:
    """
    Mixin to automatically filter queryset by tenant for DRF views.
    """
    def get_queryset(self):
        """Filter queryset by request.tenant."""
        queryset = super().get_queryset()
        
        # Get tenant from request
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            raise PermissionDenied("Tenant not found in request")
        
        # Filter by tenant if the model has a tenant field
        if hasattr(queryset.model, 'tenant'):
            return queryset.filter(tenant=tenant)
        
        return queryset
    
    def perform_create(self, serializer):
        """Automatically set tenant when creating objects."""
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            raise PermissionDenied("Tenant not found in request")
        
        # Save with tenant if the model has a tenant field
        if hasattr(serializer.Meta.model, 'tenant'):
            serializer.save(tenant=tenant)
        else:
            serializer.save()


class TenantObjectMixin:
    """
    Mixin to ensure single object retrieval respects tenant boundaries.
    """
    def get_object(self):
        """Get object ensuring it belongs to the current tenant."""
        obj = super().get_object()
        
        # Check if object has tenant field and matches request tenant
        tenant = getattr(self.request, 'tenant', None)
        if hasattr(obj, 'tenant') and obj.tenant != tenant:
            raise Http404("Object not found")
        
        return obj


class TenantAwareSerializer(serializers.ModelSerializer):
    """
    Base serializer that handles tenant context.
    """
    def __init__(self, *args, **kwargs):
        # Remove tenant from kwargs if passed
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Get tenant from context if not provided
        if not self.tenant and 'request' in self.context:
            self.tenant = getattr(self.context['request'], 'tenant', None)
    
    def validate(self, attrs):
        """Add tenant to validated data if needed."""
        attrs = super().validate(attrs)
        
        # Add tenant if the model has a tenant field and it's not already set
        if hasattr(self.Meta.model, 'tenant') and 'tenant' not in attrs and self.tenant:
            attrs['tenant'] = self.tenant
        
        return attrs
    
    def to_representation(self, instance):
        """Ensure we don't accidentally expose cross-tenant data."""
        # Verify the instance belongs to the current tenant
        if hasattr(instance, 'tenant') and self.tenant and instance.tenant != self.tenant:
            raise PermissionDenied("Access denied to cross-tenant data")
        
        return super().to_representation(instance)


def validate_tenant_object(obj, tenant):
    """
    Utility function to validate that an object belongs to the specified tenant.
    
    Args:
        obj: The object to validate
        tenant: The expected tenant
        
    Raises:
        Http404: If the object doesn't belong to the tenant
    """
    if hasattr(obj, 'tenant') and obj.tenant != tenant:
        raise Http404("Object not found")
    return obj


def filter_queryset_by_tenant(queryset, tenant):
    """
    Utility function to filter a queryset by tenant.
    
    Args:
        queryset: The queryset to filter
        tenant: The tenant to filter by
        
    Returns:
        Filtered queryset
    """
    if hasattr(queryset.model, 'tenant'):
        return queryset.filter(tenant=tenant)
    return queryset
