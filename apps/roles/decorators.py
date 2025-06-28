"""
Decorators for role-based permission checking.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test


def require_permission(permission, raise_exception=True, redirect_url=None):
    """
    Decorator to check if user has a specific permission.
    
    Args:
        permission: Permission string in format 'app_label.codename'
        raise_exception: If True, raise PermissionDenied. If False, redirect.
        redirect_url: URL to redirect to if permission check fails
    
    Usage:
        @require_permission('customers.add_customer')
        def customer_create(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            if request.user.has_perm(permission):
                return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied
            else:
                messages.error(request, "You don't have permission to access this page.")
                return redirect(redirect_url or 'web:home')
        
        return wrapped_view
    return decorator


def require_any_permission(*permissions, raise_exception=True, redirect_url=None):
    """
    Decorator to check if user has any of the specified permissions.
    
    Args:
        *permissions: Permission strings in format 'app_label.codename'
        raise_exception: If True, raise PermissionDenied. If False, redirect.
        redirect_url: URL to redirect to if permission check fails
    
    Usage:
        @require_any_permission('customers.change_customer', 'customers.view_customer')
        def customer_detail(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            for permission in permissions:
                if request.user.has_perm(permission):
                    return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied
            else:
                messages.error(request, "You don't have permission to access this page.")
                return redirect(redirect_url or 'web:home')
        
        return wrapped_view
    return decorator


def require_all_permissions(*permissions, raise_exception=True, redirect_url=None):
    """
    Decorator to check if user has all of the specified permissions.
    
    Args:
        *permissions: Permission strings in format 'app_label.codename'
        raise_exception: If True, raise PermissionDenied. If False, redirect.
        redirect_url: URL to redirect to if permission check fails
    
    Usage:
        @require_all_permissions('customers.add_customer', 'customers.change_customer')
        def customer_bulk_create(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            for permission in permissions:
                if not request.user.has_perm(permission):
                    if raise_exception:
                        raise PermissionDenied
                    else:
                        messages.error(request, "You don't have permission to access this page.")
                        return redirect(redirect_url or 'web:home')
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


def require_role(role_name, raise_exception=True, redirect_url=None):
    """
    Decorator to check if user has a specific role.
    
    Args:
        role_name: Name of the role
        raise_exception: If True, raise PermissionDenied. If False, redirect.
        redirect_url: URL to redirect to if permission check fails
    
    Usage:
        @require_role('Manager')
        def manager_dashboard(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            if request.user.groups.filter(name=role_name, role__is_active=True).exists():
                return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied
            else:
                messages.error(request, "You don't have the required role to access this page.")
                return redirect(redirect_url or 'web:home')
        
        return wrapped_view
    return decorator


def require_any_role(*role_names, raise_exception=True, redirect_url=None):
    """
    Decorator to check if user has any of the specified roles.
    
    Args:
        *role_names: Names of the roles
        raise_exception: If True, raise PermissionDenied. If False, redirect.
        redirect_url: URL to redirect to if permission check fails
    
    Usage:
        @require_any_role('Manager', 'Supervisor')
        def management_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            if request.user.groups.filter(name__in=role_names, role__is_active=True).exists():
                return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied
            else:
                messages.error(request, "You don't have the required role to access this page.")
                return redirect(redirect_url or 'web:home')
        
        return wrapped_view
    return decorator
