from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission


class Command(BaseCommand):
    help = 'List all customer permissions'

    def handle(self, *args, **options):
        # Get all permissions for the customer app
        customer_perms = Permission.objects.filter(
            content_type__app_label='customers'
        ).order_by('codename')
        
        self.stdout.write(self.style.SUCCESS('\nAll Customer Permissions:'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        for perm in customer_perms:
            self.stdout.write(f'{perm.codename:<35} | {perm.name}')
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'\nTotal: {customer_perms.count()} permissions')
