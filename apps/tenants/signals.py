"""
Tenant-specific signals for handling tenant lifecycle events.
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import logging

from apps.tenants.models import Tenant
from apps.users.models import CustomUser

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Tenant)
def handle_tenant_created(sender, instance, created, **kwargs):
    """
    Handle new tenant creation.
    
    This can be used to:
    - Set up default data for the tenant
    - Send welcome emails
    - Initialize tenant-specific settings
    """
    if created:
        logger.info(f"New tenant created: {instance.name}")
        
        # Create system user for background tasks
        system_user, _ = CustomUser.objects.get_or_create(
            username=f"system_{instance.id}",
            defaults={
                'email': f"system@{instance.name.lower().replace(' ', '')}.local",
                'tenant': instance,
                'is_staff': False,
                'is_active': False,
            }
        )
        logger.info(f"Created system user for tenant {instance.name}")


@receiver(pre_delete, sender=Tenant)
def handle_tenant_deletion(sender, instance, **kwargs):
    """
    Handle tenant deletion.
    
    This should clean up any tenant-specific resources.
    Note: Most data will be CASCADE deleted due to foreign keys.
    """
    logger.warning(f"Tenant being deleted: {instance.name}")
    
    # Add any custom cleanup logic here
    # For example, cancel scheduled tasks, clean up files, etc.


@receiver(post_save, sender=CustomUser)
def handle_user_tenant_change(sender, instance, created, **kwargs):
    """
    Handle when a user is created or modified.
    
    Ensures user has proper tenant setup.
    """
    if created and instance.tenant:
        logger.info(
            f"New user {instance.username} created for tenant {instance.tenant.name}"
        )
        
        # Could add welcome logic here specific to the tenant
