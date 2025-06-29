from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser


def get_current_tenant(request):
    """Get the current tenant from the request user"""
    if hasattr(request, '_cached_tenant'):
        return request._cached_tenant
    
    tenant = None
    if hasattr(request, 'user') and request.user.is_authenticated:
        tenant = getattr(request.user, 'tenant', None)
    
    request._cached_tenant = tenant
    return tenant


class TenantMiddleware:
    """
    Middleware to add the current tenant to the request object.
    This makes the tenant available throughout the request lifecycle.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add tenant as a lazy object to avoid querying if not needed
        request.tenant = SimpleLazyObject(lambda: get_current_tenant(request))
        
        response = self.get_response(request)
        return response
