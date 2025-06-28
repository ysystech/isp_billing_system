from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.customer_subscriptions.tasks import update_expired_subscriptions


class Command(BaseCommand):
    help = 'Manually update expired subscriptions'

    def handle(self, *args, **options):
        self.stdout.write('Checking for expired subscriptions...')
        
        # Call the task directly
        result = update_expired_subscriptions()
        
        self.stdout.write(self.style.SUCCESS(result))
        self.stdout.write(self.style.SUCCESS('Subscription update complete!'))
