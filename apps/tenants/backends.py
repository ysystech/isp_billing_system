from django.contrib.auth.backends import ModelBackend


class TenantAwareBackend(ModelBackend):
    """
    Custom authentication backend that gives tenant owners full permissions.
    """
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if user has a specific permission.
        Tenant owners bypass all permission checks.
        """
        if not user_obj.is_active:
            return False
        
        # Superusers have all permissions
        if user_obj.is_superuser:
            return True
        
        # Tenant owners have all permissions within their tenant
        if hasattr(user_obj, 'is_tenant_owner') and user_obj.is_tenant_owner:
            return True
        
        # Otherwise, check normal permissions
        return super().has_perm(user_obj, perm, obj)
    
    def has_module_perms(self, user_obj, app_label):
        """
        Check if user has permissions to access the app.
        Tenant owners can access all apps.
        """
        if not user_obj.is_active:
            return False
        
        # Superusers have all permissions
        if user_obj.is_superuser:
            return True
        
        # Tenant owners have all permissions
        if hasattr(user_obj, 'is_tenant_owner') and user_obj.is_tenant_owner:
            return True
        
        # Otherwise, check normal permissions
        return super().has_module_perms(user_obj, app_label)
