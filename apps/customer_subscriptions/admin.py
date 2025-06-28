from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import CustomerSubscription


@admin.register(CustomerSubscription)
class CustomerSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'customer_name',
        'plan_name',
        'subscription_type',
        'amount',
        'start_date',
        'end_date',
        'status_badge',
        'time_remaining',
        'created_by',
    ]
    
    list_filter = [
        'status',
        'subscription_type',
        'subscription_plan',
        'start_date',
        'created_at',
    ]
    
    search_fields = [
        'customer_installation__customer__first_name',
        'customer_installation__customer__last_name',
        'customer_installation__customer__email',
        'subscription_plan__name',
    ]
    
    readonly_fields = [
        'days_added',
        'end_date',
        'created_at',
        'updated_at',
        'time_remaining_display',
    ]
    
    fieldsets = (
        ('Customer & Plan', {
            'fields': ('customer_installation', 'subscription_plan')
        }),
        ('Subscription Details', {
            'fields': (
                'subscription_type',
                'amount',
                'start_date',
                'end_date',
                'days_added',
                'time_remaining_display',
            )
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes')
        }),
        ('System Info', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_name(self, obj):
        return obj.customer_installation.customer.full_name
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'customer_installation__customer__last_name'
    
    def plan_name(self, obj):
        return obj.subscription_plan.name
    plan_name.short_description = 'Plan'
    plan_name.admin_order_field = 'subscription_plan__name'
    
    def status_badge(self, obj):
        colors = {
            'ACTIVE': 'green',
            'EXPIRED': 'red',
            'CANCELLED': 'gray',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def time_remaining(self, obj):
        if obj.is_active:
            return obj.time_remaining_display
        return '-'
    time_remaining.short_description = 'Time Remaining'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
