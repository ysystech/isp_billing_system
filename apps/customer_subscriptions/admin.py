from django.contrib import admin
from .models import CustomerSubscription


@admin.register(CustomerSubscription)
class CustomerSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'get_customer_name',
        'plan',
        'start_date',
        'end_date',
        'amount_paid',
        'payment_method',
        'is_paid',
        'collected_by'
    ]
    list_filter = [
        'is_paid',
        'payment_method',
        'plan',
        'start_date',
        'end_date'
    ]
    search_fields = [
        'installation__customer__first_name',
        'installation__customer__last_name',
        'installation__customer__email',
        'reference_number'
    ]
    raw_id_fields = ['installation', 'plan', 'collected_by']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Subscription Information', {
            'fields': ('installation', 'plan', 'start_date', 'end_date')
        }),
        ('Payment Details', {
            'fields': (
                'amount_paid',
                'is_paid',
                'payment_date',
                'payment_method',
                'reference_number',
                'collected_by'
            )
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_customer_name(self, obj):
        return obj.installation.customer.full_name
    get_customer_name.short_description = 'Customer'
    get_customer_name.admin_order_field = 'installation__customer__last_name'
