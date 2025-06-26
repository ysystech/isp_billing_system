from django.contrib import admin
from .models import CustomerInstallation


@admin.register(CustomerInstallation)
class CustomerInstallationAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 
        'status', 
        'installation_date', 
        'router', 
        'installation_technician',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'status', 
        'is_active', 
        'installation_date', 
        'created_at'
    ]
    search_fields = [
        'customer__first_name', 
        'customer__last_name', 
        'customer__email',
        'router__serial_number'
    ]
    raw_id_fields = ['customer', 'router', 'installation_technician']
    date_hierarchy = 'installation_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer', 'is_active', 'status')
        }),
        ('Installation Details', {
            'fields': (
                'router', 
                'installation_date', 
                'installation_technician', 
                'installation_notes'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
