from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.filter
def has_permission(user, permission):
    """
    Check if user has a specific permission.
    Usage: {% if user|has_permission:"app.permission_name" %}
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    return user.has_perm(permission)


@register.filter
def has_any_permission(user, permissions):
    """
    Check if user has any of the given permissions.
    Usage: {% if user|has_any_permission:"app.perm1,app.perm2" %}
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    permission_list = [perm.strip() for perm in permissions.split(',')]
    return any(user.has_perm(perm) for perm in permission_list)


@register.filter
def has_all_permissions(user, permissions):
    """
    Check if user has all of the given permissions.
    Usage: {% if user|has_all_permissions:"app.perm1,app.perm2" %}
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    permission_list = [perm.strip() for perm in permissions.split(',')]
    return all(user.has_perm(perm) for perm in permission_list)
