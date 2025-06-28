"""
Context processors for roles app.
"""
from .utils import get_user_roles


def user_roles(request):
    """
    Add user roles to template context.
    
    Adds:
        - user_roles: List of Role objects for the current user
        - user_role_names: List of role names as strings
        - has_role: Function to check if user has a specific role
    """
    if request.user.is_authenticated:
        roles = get_user_roles(request.user)
        role_names = [role.name for role in roles]
        
        def has_role(role_name):
            return role_name in role_names
        
        return {
            'user_roles': roles,
            'user_role_names': role_names,
            'has_role': has_role,
        }
    
    return {
        'user_roles': [],
        'user_role_names': [],
        'has_role': lambda x: False,
    }
