from django.contrib import admin
from apps.barangays.models import Barangay


@admin.register(Barangay)
class BarangayAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_active", "customer_count", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "code"]
    ordering = ["name"]
    
    fieldsets = (
        (None, {
            "fields": ("name", "code", "is_active")
        }),
        ("Additional Information", {
            "fields": ("description",)
        }),
        ("System Information", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = ["created_at", "updated_at"]
    
    def customer_count(self, obj):
        return obj.customer_count
    customer_count.short_description = "Active Customers"
