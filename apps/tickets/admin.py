from django.contrib import admin
from django.utils.html import format_html
from .models import Ticket, TicketComment


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 1
    readonly_fields = ('created_at',)
    fields = ('user', 'comment', 'created_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_number', 'title', 'customer', 'category', 
        'priority_badge', 'status_badge', 'assigned_to', 'created_at'
    ]
    list_filter = ['status', 'priority', 'category', 'source', 'created_at']
    search_fields = [
        'ticket_number', 'title', 'description',
        'customer__first_name', 'customer__last_name', 'customer__email'
    ]
    readonly_fields = ['ticket_number', 'created_at', 'updated_at', 'resolved_at']
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_number', 'title', 'description', 'category', 'priority', 'source')
        }),
        ('Customer Information', {
            'fields': ('customer', 'customer_installation')
        }),
        ('Assignment & Status', {
            'fields': ('status', 'assigned_to', 'reported_by')
        }),
        ('Resolution', {
            'fields': ('resolved_at', 'resolution_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TicketCommentInline]
    
    def priority_badge(self, obj):
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'urgent': 'darkred',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.priority, 'black'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'assigned': 'blue',
            'in_progress': 'purple',
            'resolved': 'green',
            'cancelled': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'user', 'comment_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['ticket__ticket_number', 'comment', 'user__email']
    readonly_fields = ['created_at']
    
    def comment_preview(self, obj):
        return obj.comment[:100] + '...' if len(obj.comment) > 100 else obj.comment
    comment_preview.short_description = 'Comment'
