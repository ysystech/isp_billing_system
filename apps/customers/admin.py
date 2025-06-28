from django.contrib import admin
from django.utils.html import format_html

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        "get_full_name",
        "email",
        "phone_primary",
        "status_badge",
        "created_at"
    ]
    list_filter = ["status", "barangay", "created_at"]
    search_fields = [
        "first_name",
        "last_name",
        "email",
        "phone_primary",
        "street_address"
    ]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Personal Information", {
            "fields": (
                ("first_name", "last_name"),
                "email",
                "phone_primary",
            )
        }),
        ("Service Address", {
            "fields": (
                "street_address",
                "barangay",
            )
        }),
        ("Account Information", {
            "fields": (
                "user",
                "status",
                "notes",
            )
        }),
        ("System Information", {
            "fields": ("created_at", "updated_at"),
            "classes": ["collapse"]
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = "Full Name"
    get_full_name.admin_order_field = "last_name"
    
    def status_badge(self, obj):
        colors = {
            Customer.ACTIVE: "green",
            Customer.INACTIVE: "gray",
            Customer.SUSPENDED: "orange",
            Customer.TERMINATED: "red",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"
