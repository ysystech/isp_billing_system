from django.contrib import admin
from django.contrib.auth.models import Permission
from django.db import transaction
from .models import Role, PermissionCategory, PermissionCategoryMapping, RolePermissionPreset


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'user_count', 'is_active', 'is_system', 'created_at']
    list_filter = ['is_active', 'is_system', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'user_count']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active', 'is_system')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_count(self, obj):
        return obj.user_count
    user_count.short_description = 'Active Users'
    
    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        if obj.is_system:
            self.message_user(request, "System roles cannot be deleted.", level='error')
            return
        super().delete_model(request, obj)


@admin.register(PermissionCategory)
class PermissionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'icon', 'order', 'permission_count']
    list_editable = ['order']
    search_fields = ['name', 'code']
    
    def permission_count(self, obj):
        return obj.get_permissions().count()
    permission_count.short_description = 'Permissions'


class PermissionCategoryMappingInline(admin.TabularInline):
    model = PermissionCategoryMapping
    extra = 1
    autocomplete_fields = ['permission']


@admin.register(PermissionCategoryMapping)
class PermissionCategoryMappingAdmin(admin.ModelAdmin):
    list_display = ['category', 'display_name', 'permission', 'order']
    list_filter = ['category']
    list_editable = ['order']
    search_fields = ['display_name', 'permission__codename', 'permission__name']
    autocomplete_fields = ['permission']
    
    fieldsets = (
        (None, {
            'fields': ('category', 'permission', 'display_name', 'description', 'order')
        }),
    )


@admin.register(RolePermissionPreset)
class RolePermissionPresetAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'permission_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions']
    
    def permission_count(self, obj):
        return obj.permissions.count()
    permission_count.short_description = 'Permissions'


# Make Permission searchable in admin
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'codename']
    list_filter = ['content_type']
    search_fields = ['name', 'codename']
    ordering = ['content_type__app_label', 'codename']
