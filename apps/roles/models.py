from django.db import models
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.utils.models import BaseModel


class Role(BaseModel):
    """
    Wrapper around Django's Group model to provide additional functionality
    and better UI/UX for role management.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, help_text="Describe what this role is for")
    group = models.OneToOneField(
        Group, 
        on_delete=models.CASCADE,
        related_name='role'
    )
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(
        default=False,
        help_text="System roles cannot be deleted"
    )
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name
    
    @property
    def permissions(self):
        """Get all permissions assigned to this role."""
        return self.group.permissions.all()
    
    @property
    def users(self):
        """Get all users assigned to this role."""
        return self.group.user_set.filter(is_active=True)
    
    @property
    def user_count(self):
        """Get count of active users with this role."""
        return self.users.count()
    
    def add_permission(self, permission):
        """Add a permission to this role."""
        self.group.permissions.add(permission)
    
    def remove_permission(self, permission):
        """Remove a permission from this role."""
        self.group.permissions.remove(permission)
    
    def add_user(self, user):
        """Add a user to this role."""
        user.groups.add(self.group)
    
    def remove_user(self, user):
        """Remove a user from this role."""
        user.groups.remove(self.group)
    
    def save(self, *args, **kwargs):
        # Create or update the associated group
        if not self.pk:
            # Creating new role
            self.group = Group.objects.create(name=self.name)
        else:
            # Updating existing role
            self.group.name = self.name
            self.group.save()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Don't allow deletion of system roles
        if self.is_system:
            raise ValueError("System roles cannot be deleted")
        
        # Delete the associated group
        if self.group:
            self.group.delete()
        
        super().delete(*args, **kwargs)


class PermissionCategory(models.Model):
    """
    Categories to organize permissions for better UI/UX.
    """
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Font Awesome icon class, e.g., 'fa-users'"
    )
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Permission Categories"
    
    def __str__(self):
        return self.name
    
    def get_permissions(self):
        """
        Get all permissions that belong to this category.
        Uses PermissionCategoryMapping to get the permissions.
        """
        return Permission.objects.filter(
            permission_mappings__category=self
        ).distinct()


class PermissionCategoryMapping(models.Model):
    """
    Maps Django permissions to categories with user-friendly names.
    """
    category = models.ForeignKey(
        PermissionCategory, 
        on_delete=models.CASCADE,
        related_name='permission_mappings'
    )
    permission = models.ForeignKey(
        Permission, 
        on_delete=models.CASCADE,
        related_name='permission_mappings'
    )
    display_name = models.CharField(
        max_length=100,
        help_text="User-friendly name for this permission"
    )
    description = models.TextField(
        blank=True,
        help_text="Help text to explain what this permission does"
    )
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'display_name']
        unique_together = ['category', 'permission']
    
    def __str__(self):
        return f"{self.category.name} - {self.display_name}"


class RolePermissionPreset(models.Model):
    """
    Predefined sets of permissions that can be applied to roles.
    Useful for quickly setting up common role configurations.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def apply_to_role(self, role):
        """Apply this preset's permissions to a role."""
        role.group.permissions.set(self.permissions.all())
