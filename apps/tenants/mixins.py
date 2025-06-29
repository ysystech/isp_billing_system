from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q


class TenantRequiredMixin(LoginRequiredMixin):
    """
    Mixin that ensures user has a tenant and provides tenant filtering.
    """
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        # Ensure user has a tenant
        if not hasattr(request.user, 'tenant') or not request.user.tenant:
            raise PermissionDenied("You must belong to a tenant to access this resource.")
        
        return response
    
    def get_queryset(self):
        """
        Filter queryset by current tenant.
        """
        queryset = super().get_queryset()
        
        # Only filter if the model has a tenant field
        if hasattr(queryset.model, 'tenant'):
            queryset = queryset.filter(tenant=self.request.tenant)
        
        return queryset


def filter_by_tenant(queryset, tenant):
    """
    Helper function to filter a queryset by tenant.
    Returns the filtered queryset if the model has a tenant field,
    otherwise returns the original queryset.
    """
    if hasattr(queryset.model, 'tenant'):
        return queryset.filter(tenant=tenant)
    return queryset


def tenant_required(view_func):
    """
    Decorator for function-based views that ensures user has a tenant.
    """
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if not hasattr(request.user, 'tenant') or not request.user.tenant:
            raise PermissionDenied("You must belong to a tenant to access this resource.")
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view
