"""
Middleware for role-based access control.
"""
from django.utils.deprecation import MiddlewareMixin
from .utils import get_user_roles, user_has_role


class RoleMiddleware(MiddlewareMixin):
    """
    Middleware to add role checking methods to the request object.
    
    Adds:
        - request.user_roles: List of Role objects
        - request.user_has_role(role_name): Check if user has a specific role
        - request.user_has_any_role(*role_names): Check if user has any of the roles
        - request.user_has_permission(permission): Check if user has a permission
    """
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Cache user roles on the request
            request.user_roles = get_user_roles(request.user)
            
            # Add helper methods
            def user_has_role(role_name):
                return user_has_role(request.user, role_name)
            
            def user_has_any_role(*role_names):
                return any(user_has_role(request.user, role) for role in role_names)
            
            def user_has_permission(permission):
                return request.user.has_perm(permission)
            
            request.user_has_role = user_has_role
            request.user_has_any_role = user_has_any_role
            request.user_has_permission = user_has_permission
        else:
            # For anonymous users
            request.user_roles = []
            request.user_has_role = lambda x: False
            request.user_has_any_role = lambda *x: False
            request.user_has_permission = lambda x: False
        
        return None
