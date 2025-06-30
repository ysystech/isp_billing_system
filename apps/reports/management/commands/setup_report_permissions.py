"""
Management command to set up simplified report permissions.
Run this after initial migrations to set up the 11 report permissions.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Set up simplified report permissions (11 permissions instead of 20)'

    def handle(self, *args, **options):
        self.stdout.write('Setting up report permissions...')
        
        # Get or create the reports content type
        try:
            reports_ct = ContentType.objects.get(app_label='reports', model='report')
        except ContentType.DoesNotExist:
            # Create a dummy content type for reports if it doesn't exist
            reports_ct = ContentType.objects.create(
                app_label='reports',
                model='report'
            )
            self.stdout.write(self.style.SUCCESS('Created reports content type'))
        
        # First, clean up any duplicate permissions
        duplicate_codenames = [
            'view_ticket_analysis_report', 'view_area_performance_dashboard',
            'view_subscription_expiry_report', 'view_financial_statistics',
            'view_financial_dashboard', 'view_system_statistics',
            'view_daily_collection_report', 'view_monthly_revenue_report',
            'view_customer_statistics', 'view_infrastructure_statistics',
            'view_customer_acquisition_report', 'view_technician_performance_report',
            'view_payment_behavior_report'
        ]
        
        for codename in duplicate_codenames:
            perms = Permission.objects.filter(codename=codename).order_by('id')
            if perms.count() > 1:
                # Keep the first one, delete the rest
                for perm in perms[1:]:
                    perm.delete()
                self.stdout.write(f'Cleaned up duplicates for {codename}')
        
        # Permissions to keep (11 total)
        permissions_to_keep = [
            # Main dashboard
            ('view_reports_dashboard', 'Can view reports dashboard'),
            
            # Individual reports (7)
            ('view_daily_collection_report', 'Can view daily collection report'),
            ('view_subscription_expiry_report', 'Can view subscription expiry report'),
            ('view_monthly_revenue_report', 'Can view monthly revenue report'),
            ('view_ticket_analysis_report', 'Can view ticket analysis report'),
            ('view_technician_performance_report', 'Can view technician performance report'),
            ('view_customer_acquisition_report', 'Can view customer acquisition report'),
            ('view_payment_behavior_report', 'Can view payment behavior report'),
            
            # Dashboards (2)
            ('view_area_performance_dashboard', 'Can view area performance dashboard'),
            ('view_financial_dashboard', 'Can view financial dashboard'),
            
            # Single export permission
            ('export_reports', 'Can export reports'),
        ]
        
        # Permissions to remove
        permissions_to_remove = [
            'view_customer_statistics',
            'view_financial_statistics',
            'view_infrastructure_statistics',
            'view_system_statistics',
            'access_advanced_analytics',
            'customize_report_parameters',
            'export_business_reports',
            'export_operational_reports',
            'schedule_reports',
            'view_reports',  # Duplicate of view_reports_dashboard
            'view_active_subscriptions',  # Part of dashboard
        ]
        
        # Create or update the permissions we want to keep
        created_count = 0
        updated_count = 0
        
        for codename, name in permissions_to_keep:
            permission, created = Permission.objects.update_or_create(
                codename=codename,
                content_type=reports_ct,
                defaults={'name': name}
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created permission: {codename}')
            else:
                updated_count += 1
                self.stdout.write(f'Updated permission: {codename}')
        
        # Delete the permissions we no longer need
        deleted_count = Permission.objects.filter(
            codename__in=permissions_to_remove,
            content_type=reports_ct
        ).delete()[0]
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} unnecessary permissions')
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nReport permissions setup complete!\n'
                f'Created: {created_count} permissions\n'
                f'Updated: {updated_count} permissions\n'
                f'Deleted: {deleted_count} permissions\n'
                f'Total active permissions: {len(permissions_to_keep)}'
            )
        )
