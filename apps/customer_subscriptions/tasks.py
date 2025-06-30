from celery import shared_task
from django.utils import timezone
from apps.customer_subscriptions.models import CustomerSubscription
from apps.customer_installations.models import CustomerInstallation
from apps.tenants.tasks import TenantAwareTask
from apps.tenants.context import get_current_tenant
import logging

logger = logging.getLogger(__name__)


class UpdateExpiredSubscriptionsTask(TenantAwareTask):
    """Tenant-aware task to update expired subscriptions."""
    
    def run(self):
        """
        Update expired subscriptions for the current tenant.
        """
        tenant = get_current_tenant()
        if not tenant:
            logger.error("No tenant context available for update_expired_subscriptions")
            return "Error: No tenant context"
            
        now = timezone.now()
        
        # Find all active subscriptions that should be expired for this tenant
        expired_subscriptions = CustomerSubscription.objects.filter(
            tenant=tenant,
            status='ACTIVE',
            end_date__lt=now
        )
        
        updated_count = 0
        for subscription in expired_subscriptions:
            subscription.status = 'EXPIRED'
            subscription.save()
            updated_count += 1
            
            # Check if installation should be set to INACTIVE
            installation = subscription.customer_installation
            if not installation.has_active_subscription:
                installation.status = 'INACTIVE'
                installation.save()
                logger.info(f"Installation {installation.id} set to INACTIVE - no active subscriptions")
        
        logger.info(f"Tenant {tenant.name}: Updated {updated_count} expired subscriptions")
        return f"Tenant {tenant.name}: Updated {updated_count} expired subscriptions"


# Create the shared task instance
update_expired_subscriptions = UpdateExpiredSubscriptionsTask()


class SendExpirationRemindersTask(TenantAwareTask):
    """Tenant-aware task to send subscription expiration reminders."""
    
    def run(self):
        """
        Send reminders for subscriptions expiring soon for the current tenant.
        """
        from datetime import timedelta
        
        tenant = get_current_tenant()
        if not tenant:
            logger.error("No tenant context available for send_expiration_reminders")
            return "Error: No tenant context"
        
        now = timezone.now()
        
        # Find subscriptions expiring in next 3 days for this tenant
        expiring_soon = CustomerSubscription.objects.filter(
            tenant=tenant,
            status='ACTIVE',
            end_date__gt=now,
            end_date__lt=now + timedelta(days=3)
        )
        
        reminders_sent = 0
        for subscription in expiring_soon:
            # TODO: Implement SMS/Email notification
            # For now, just log
            days_left = (subscription.end_date - now).days
            logger.info(
                f"Tenant {tenant.name}: Subscription {subscription.id} for "
                f"{subscription.customer_installation.customer.full_name} "
                f"expires in {days_left} days"
            )
            reminders_sent += 1
        
        logger.info(f"Tenant {tenant.name}: Sent {reminders_sent} expiration reminders")
        return f"Tenant {tenant.name}: Sent {reminders_sent} expiration reminders"


# Create the shared task instance
send_expiration_reminders = SendExpirationRemindersTask()


# Backward compatibility wrapper functions
@shared_task
def update_expired_subscriptions_all_tenants():
    """
    Run update_expired_subscriptions for all active tenants.
    This replaces the old task that ran across all tenants.
    """
    return update_expired_subscriptions.run_for_all_tenants()


@shared_task
def send_expiration_reminders_all_tenants():
    """
    Run send_expiration_reminders for all active tenants.
    This replaces the old task that ran across all tenants.
    """
    return send_expiration_reminders.run_for_all_tenants()


# For specific tenant execution (useful for testing or manual runs)
@shared_task
def update_expired_subscriptions_for_tenant(tenant_id: int):
    """Run update_expired_subscriptions for a specific tenant."""
    return update_expired_subscriptions.run_for_tenant(tenant_id)


@shared_task
def send_expiration_reminders_for_tenant(tenant_id: int):
    """Run send_expiration_reminders for a specific tenant."""
    return send_expiration_reminders.run_for_tenant(tenant_id)