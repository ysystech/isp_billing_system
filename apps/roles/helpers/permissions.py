"""
Helper functions for role-based permission management.
"""
from apps.roles.models import Role


def get_accessible_roles(user):
    """
    Return roles that the user is permitted to see and manage based on their permissions.
    A user can only manage roles that have a subset of their own permissions.
    
    Args:
        user: The user to check permissions for
        
    Returns:
        QuerySet of Role objects that the user can access
    """
    if user.is_superuser:
        return Role.objects.all()  # Superusers can see all roles
    
    # Get all the user's permissions as a set
    user_permissions = set(user.get_all_permissions())
    
    # Filter roles to include only those where all permissions are a subset of the user's permissions
    accessible_roles = []
    for role in Role.objects.filter(is_active=True):
        # Get all permissions in this role
        role_permissions = {f"{perm.content_type.app_label}.{perm.codename}" 
                           for perm in role.permissions}
        
        # Check if this role only contains permissions the user has
        if role_permissions.issubset(user_permissions):
            accessible_roles.append(role.id)
    
    # Return queryset of accessible roles
    return Role.objects.filter(id__in=accessible_roles)


def can_manage_role(user, role):
    """
    Check if a user can manage a specific role.
    
    Args:
        user: The user to check
        role: The role to check
        
    Returns:
        bool: True if the user can manage the role, False otherwise
    """
    if user.is_superuser:
        return True
    
    # Get all the user's permissions as a set
    user_permissions = set(user.get_all_permissions())
    
    # Get all permissions in this role
    role_permissions = {f"{perm.content_type.app_label}.{perm.codename}" 
                       for perm in role.permissions}
    
    # Check if this role only contains permissions the user has
    return role_permissions.issubset(user_permissions)
