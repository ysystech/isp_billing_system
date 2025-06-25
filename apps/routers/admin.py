from django.contrib import admin
from apps.routers.models import Router


@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
    list_display = [
        "brand",
        "model",
        "serial_number",
        "created_at",
    ]
    list_filter = ["brand", "created_at"]
    search_fields = [
        "brand",
        "model",
        "serial_number",
    ]
    ordering = ["-created_at"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("brand", "model", "serial_number")
        }),
        ("Additional", {
            "fields": ("notes",)
        }),
        ("System Information", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = ["created_at", "updated_at"]
