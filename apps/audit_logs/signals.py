import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.apps import apps
from apps.audit_logs.models import AuditLogEntry
from apps.audit_logs.middleware import get_current_request


# List of models to track
TRACKED_MODELS = [
    'customers.Customer',
    'routers.Router', 
    'barangays.Barangay',
    'subscriptions.SubscriptionPlan',
    'lcp.LCP',
    'lcp.Splitter',
    'lcp.NAP',
    'customer_installations.CustomerInstallation',
    'customer_subscriptions.CustomerSubscription',
    'tickets.Ticket',
    'tickets.TicketComment',
    'users.CustomUser',
    'roles.Role',
]


def create_audit_log(user, obj, action_flag, change_message=''):
    """Create an audit log entry with metadata"""
    if user and user.is_authenticated:
        # Create Django's LogEntry
        log_entry = LogEntry.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(obj.__class__),
            object_id=str(obj.pk),
            object_repr=str(obj)[:200],
            action_flag=action_flag,
            change_message=change_message
        )
        
        # Get request metadata
        request = get_current_request()
        if request and hasattr(request, 'audit_metadata'):
            # Create extended audit log entry
            AuditLogEntry.objects.create(
                log_entry=log_entry,
                ip_address=request.audit_metadata.get('ip_address'),
                user_agent=request.audit_metadata.get('user_agent'),
                request_method=request.audit_metadata.get('request_method'),
                session_key=request.audit_metadata.get('session_key') or None,
            )


@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    """Log creation and update of tracked models"""
    model_label = f"{sender._meta.app_label}.{sender.__name__}"
    
    if model_label in TRACKED_MODELS:
        request = get_current_request()
        if request and hasattr(request, 'user'):
            action_flag = ADDITION if created else CHANGE
            action_text = "Created" if created else "Updated"
            
            # Get changed fields for updates
            change_message = f"{action_text} {sender.__name__}"
            if not created and hasattr(instance, '_state'):
                # This would need more sophisticated change tracking
                # For now, just log that it was updated
                pass
                
            create_audit_log(
                user=request.user,
                obj=instance,
                action_flag=action_flag,
                change_message=change_message
            )


@receiver(pre_delete)
def log_delete(sender, instance, **kwargs):
    """Log deletion of tracked models"""
    model_label = f"{sender._meta.app_label}.{sender.__name__}"
    
    if model_label in TRACKED_MODELS:
        request = get_current_request()
        if request and hasattr(request, 'user'):
            create_audit_log(
                user=request.user,
                obj=instance,
                action_flag=DELETION,
                change_message=f"Deleted {sender.__name__}"
            )
