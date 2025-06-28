"""
Forms for role management.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from .models import Role, PermissionCategory

User = get_user_model()


class RoleForm(forms.ModelForm):
    """Form for creating and editing roles."""
    
    class Meta:
        model = Role
        fields = ['name', 'description', 'is_active', 'is_system']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., Department Head'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Describe what this role is for...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
            'is_system': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-warning'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.is_system:
            # System roles cannot change their name or system status
            self.fields['name'].disabled = True
            self.fields['is_system'].disabled = True


class RolePermissionsForm(forms.Form):
    """Form for managing role permissions organized by category."""
    
    def __init__(self, *args, **kwargs):
        self.role = kwargs.pop('role', None)
        super().__init__(*args, **kwargs)
        
        # Get all categories
        categories = PermissionCategory.objects.all()
        
        # Create fields for each category
        for category in categories:
            # Get permissions for this category
            permissions = Permission.objects.filter(
                permission_mappings__category=category
            ).distinct().order_by('permission_mappings__order')
            
            # Create choices
            choices = []
            for perm in permissions:
                mapping = perm.permission_mappings.filter(category=category).first()
                if mapping:
                    label = mapping.display_name
                    if mapping.description:
                        label += f' - {mapping.description}'
                else:
                    label = f'{perm.content_type.app_label}.{perm.codename}'
                
                choices.append((perm.id, label))
            
            # Create field
            if choices:
                field_name = f'category_{category.id}'
                self.fields[field_name] = forms.MultipleChoiceField(
                    choices=choices,
                    required=False,
                    widget=forms.CheckboxSelectMultiple(attrs={
                        'class': 'checkbox checkbox-sm'
                    }),
                    label=category.name,
                    help_text=category.description
                )
                
                # Set initial values if editing
                if self.role:
                    initial_perms = self.role.permissions.filter(
                        permission_mappings__category=category
                    ).values_list('id', flat=True)
                    self.fields[field_name].initial = [str(p) for p in initial_perms]
    
    def save(self):
        """Save the selected permissions to the role."""
        if not self.role:
            return
        
        # Clear existing permissions
        self.role.group.permissions.clear()
        
        # Add selected permissions
        for field_name, field in self.fields.items():
            if field_name.startswith('category_'):
                permission_ids = self.cleaned_data.get(field_name, [])
                for perm_id in permission_ids:
                    try:
                        permission = Permission.objects.get(id=perm_id)
                        self.role.add_permission(permission)
                    except Permission.DoesNotExist:
                        pass


class UserRoleAssignmentForm(forms.Form):
    """Form for assigning roles to a user."""
    
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        label="Assigned Roles"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Set initial roles
            self.fields['roles'].initial = Role.objects.filter(
                group__user=self.user,
                is_active=True
            )
    
    def save(self):
        """Save the role assignments."""
        if not self.user:
            return
        
        # Clear existing roles
        self.user.groups.clear()
        
        # Add selected roles
        for role in self.cleaned_data['roles']:
            role.add_user(self.user)
