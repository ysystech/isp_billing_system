from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import CustomUser
from apps.roles.models import Role


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("get_roles", "date_joined",)
    list_filter = UserAdmin.list_filter + ("groups__role", "date_joined",)
    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        ("Custom Fields", {"fields": ("avatar",)}),
        ("Role Assignment", {"fields": ("get_user_roles",)}),
    )
    
    readonly_fields = UserAdmin.readonly_fields + ("get_user_roles",)
    
    def get_roles(self, obj):
        """Display user roles in list view."""
        roles = Role.objects.filter(group__user=obj, is_active=True)
        if roles:
            role_tags = []
            for role in roles:
                color = "primary" if not role.is_system else "warning"
                role_tags.append(
                    f'<span class="badge badge-{color} badge-sm">{role.name}</span>'
                )
            return format_html(" ".join(role_tags))
        return format_html('<span class="text-gray-400">No roles</span>')
    
    get_roles.short_description = "Roles"
    
    def get_user_roles(self, obj):
        """Display user roles in detail view."""
        roles = Role.objects.filter(group__user=obj, is_active=True)
        if roles:
            items = []
            for role in roles:
                items.append(
                    f'<li><strong>{role.name}</strong> - {role.description}</li>'
                )
            return format_html(
                '<ul style="margin: 0; padding-left: 20px;">{}</ul>',
                format_html("".join(items))
            )
        return "No roles assigned"
    
    get_user_roles.short_description = "Assigned Roles"
