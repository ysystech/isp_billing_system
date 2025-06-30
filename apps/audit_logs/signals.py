import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.apps import apps
from apps.audit_logs.models import AuditLogEntry
from apps.audit_logs.middleware import get_current_request
from apps.tenants.context import get_current_tenant


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
    # Handle background tasks - get user from system user or tenant context
    if not user:
        # Try to get tenant from context (background tasks)
        tenant = get_current_tenant()
        if tenant:
            # Get or create a system user for this tenant
            from apps.users.models import CustomUser
            user, _ = CustomUser.objects.get_or_create(
                username=f"system_{tenant.id}",
                defaults={
                    'email': f"system@{tenant.name.lower().replace(' ', '')}.local",
                    'tenant': tenant,
                    'is_staff': False,
                    'is_active': False,
                }
            )
    
    if user and user.is_authenticated:
        # Skip audit logging if user doesn't have a tenant yet (during registration)
        if hasattr(user, 'tenant') and not user.tenant:
            return
            
        # Create Django's LogEntry
        log_entry = LogEntry.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(obj.__class__),
            object_id=str(obj.pk),
            object_repr=str(obj)[:200],
            action_flag=action_flag,
            change_message=change_message
        )
        
        # Get request metadata or use background task defaults
        request = get_current_request()
        tenant = None
        ip_address = None
        user_agent = None
        request_method = None
        session_key = None
        
        if request and hasattr(request, 'audit_metadata'):
            # Request context available
            if hasattr(request, 'tenant'):
                tenant = request.tenant
            ip_address = request.audit_metadata.get('ip_address')
            user_agent = request.audit_metadata.get('user_agent')
            request_method = request.audit_metadata.get('request_method')
            session_key = request.audit_metadata.get('session_key')
        else:
            # Background task context
            tenant = get_current_tenant()
            ip_address = '127.0.0.1'  # Local for background tasks
            user_agent = 'Celery Background Task'
            request_method = 'TASK'
            
        if tenant:
            # Create extended audit log entry
            AuditLogEntry.objects.create(
                log_entry=log_entry,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                session_key=session_key,
                tenant=tenant
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
