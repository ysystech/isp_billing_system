"""
Template tags for role-based permission management.
"""
from django import template
from apps.roles.helpers.permissions import can_manage_role

register = template.Library()


@register.filter
def can_manage(user, role):
    """
    Check if a user can manage a specific role.
    
    Usage:
        {% if request.user|can_manage:role %}
            ...
        {% endif %}
    """
    return can_manage_role(user, role)
