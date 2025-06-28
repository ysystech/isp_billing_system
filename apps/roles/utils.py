"""
Utility functions for role and permission management.
"""
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from .models import Role, PermissionCategory, PermissionCategoryMapping


def create_role(name, description="", permissions=None, is_system=False):
    """
    Create a new role with the given permissions.
    
    Args:
        name: Role name
        description: Role description
        permissions: List of permission codenames or Permission objects
        is_system: Whether this is a system role
    
    Returns:
        Role instance
    """
    with transaction.atomic():
        role = Role.objects.create(
            name=name,
            description=description,
            is_system=is_system
        )
        
        if permissions:
            for perm in permissions:
                if isinstance(perm, str):
                    # Permission codename provided
                    try:
                        app_label, codename = perm.split('.')
                        permission = Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename
                        )
                        role.add_permission(permission)
                    except (ValueError, Permission.DoesNotExist):
                        print(f"Warning: Permission '{perm}' not found")
                elif isinstance(perm, Permission):
                    # Permission object provided
                    role.add_permission(perm)
        
        return role


def get_permissions_for_model(model):
    """
    Get all permissions for a specific model.
    
    Args:
        model: Django model class
    
    Returns:
        QuerySet of Permission objects
    """
    content_type = ContentType.objects.get_for_model(model)
    return Permission.objects.filter(content_type=content_type)


def get_permissions_by_category(category_code):
    """
    Get all permissions for a specific category.
    
    Args:
        category_code: PermissionCategory code
    
    Returns:
        QuerySet of Permission objects
    """
    try:
        category = PermissionCategory.objects.get(code=category_code)
        return category.get_permissions()
    except PermissionCategory.DoesNotExist:
        return Permission.objects.none()


def assign_role_to_user(user, role_name):
    """
    Assign a role to a user.
    
    Args:
        user: User instance
        role_name: Name of the role
    
    Returns:
        Boolean indicating success
    """
    try:
        role = Role.objects.get(name=role_name, is_active=True)
        role.add_user(user)
        return True
    except Role.DoesNotExist:
        return False


def remove_role_from_user(user, role_name):
    """
    Remove a role from a user.
    
    Args:
        user: User instance
        role_name: Name of the role
    
    Returns:
        Boolean indicating success
    """
    try:
        role = Role.objects.get(name=role_name)
        role.remove_user(user)
        return True
    except Role.DoesNotExist:
        return False


def get_user_roles(user):
    """
    Get all roles assigned to a user.
    
    Args:
        user: User instance
    
    Returns:
        QuerySet of Role objects
    """
    return Role.objects.filter(group__user=user, is_active=True)


def user_has_role(user, role_name):
    """
    Check if a user has a specific role.
    
    Args:
        user: User instance
        role_name: Name of the role
    
    Returns:
        Boolean
    """
    return user.groups.filter(name=role_name, role__is_active=True).exists()


def get_role_permissions_dict(role):
    """
    Get a dictionary of permissions organized by category for a role.
    
    Args:
        role: Role instance
    
    Returns:
        Dictionary with category codes as keys and lists of permissions as values
    """
    permissions_dict = {}
    
    for mapping in PermissionCategoryMapping.objects.filter(
        permission__in=role.permissions
    ).select_related('category', 'permission'):
        category_code = mapping.category.code
        if category_code not in permissions_dict:
            permissions_dict[category_code] = []
        permissions_dict[category_code].append({
            'permission': mapping.permission,
            'display_name': mapping.display_name,
            'description': mapping.description
        })
    
    return permissions_dict
