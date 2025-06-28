"""
Template tags for role and permission checking.
"""
from django import template
from django.contrib.auth.models import Permission
from apps.roles.models import Role
from apps.roles.utils import get_user_roles, user_has_role

register = template.Library()


@register.filter
def has_permission(user, permission):
    """
    Check if user has a specific permission.
    
    Usage:
        {% if user|has_permission:"customers.add_customer" %}
            <a href="...">Add Customer</a>
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    return user.has_perm(permission)


@register.filter
def has_any_permission(user, permissions):
    """
    Check if user has any of the comma-separated permissions.
    
    Usage:
        {% if user|has_any_permission:"customers.add_customer,customers.change_customer" %}
            <a href="...">Manage Customer</a>
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    
    for perm in permissions.split(','):
        if user.has_perm(perm.strip()):
            return True
    return False


@register.filter
def has_all_permissions(user, permissions):
    """
    Check if user has all of the comma-separated permissions.
    
    Usage:
        {% if user|has_all_permissions:"customers.add_customer,customers.delete_customer" %}
            <a href="...">Full Customer Control</a>
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    
    for perm in permissions.split(','):
        if not user.has_perm(perm.strip()):
            return False
    return True


@register.filter
def has_role(user, role_name):
    """
    Check if user has a specific role.
    
    Usage:
        {% if user|has_role:"Manager" %}
            <a href="...">Manager Dashboard</a>
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    return user_has_role(user, role_name)


@register.filter
def has_any_role(user, role_names):
    """
    Check if user has any of the comma-separated roles.
    
    Usage:
        {% if user|has_any_role:"Manager,Supervisor" %}
            <a href="...">Management Area</a>
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    
    roles = [name.strip() for name in role_names.split(',')]
    return user.groups.filter(name__in=roles, role__is_active=True).exists()


@register.filter
def get_roles(user):
    """
    Get all roles for a user.
    
    Usage:
        {% for role in user|get_roles %}
            <span class="badge">{{ role.name }}</span>
        {% endfor %}
    """
    if not user.is_authenticated:
        return []
    return get_user_roles(user)


@register.simple_tag
def user_permissions(user):
    """
    Get all permissions for a user.
    
    Usage:
        {% user_permissions user as perms %}
        {% for perm in perms %}
            {{ perm.codename }}
        {% endfor %}
    """
    if not user.is_authenticated:
        return Permission.objects.none()
    return user.user_permissions.all() | Permission.objects.filter(group__user=user)


@register.inclusion_tag('roles/tags/permission_checker.html')
def permission_checker(user, permission, show_message=True):
    """
    Include tag that shows content based on permission.
    
    Usage:
        {% permission_checker user "customers.add_customer" %}
    """
    return {
        'has_permission': user.has_perm(permission) if user.is_authenticated else False,
        'permission': permission,
        'show_message': show_message
    }
