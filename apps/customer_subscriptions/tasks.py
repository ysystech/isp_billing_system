from celery import shared_task
from django.utils import timezone
from apps.customer_subscriptions.models import CustomerSubscription
from apps.customer_installations.models import CustomerInstallation
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_expired_subscriptions():
    """
    Periodic task to update expired subscriptions and installation statuses.
    Should run every 30 minutes or hourly.
    """
    now = timezone.now()
    
    # Find all active subscriptions that should be expired
    expired_subscriptions = CustomerSubscription.objects.filter(
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
    
    logger.info(f"Updated {updated_count} expired subscriptions")
    return f"Updated {updated_count} expired subscriptions"


@shared_task
def send_expiration_reminders():
    """
    Send reminders for subscriptions expiring soon.
    Should run daily.
    """
    from datetime import timedelta
    
    now = timezone.now()
    
    # Find subscriptions expiring in next 3 days
    expiring_soon = CustomerSubscription.objects.filter(
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
            f"Subscription {subscription.id} for {subscription.customer_installation.customer.full_name} "
            f"expires in {days_left} days"
        )
        reminders_sent += 1
    
    return f"Sent {reminders_sent} expiration reminders"
