"""
Management command to set up the default Django site.
This replaces the data migration that was in apps/web/migrations.
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = 'Set up the default Django site with project metadata'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Override the domain (instead of using PROJECT_METADATA URL)',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Override the site name (instead of using PROJECT_METADATA NAME)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up default site...')
        
        # Get domain and name from options or settings
        if options['domain']:
            domain = options['domain']
            self.stdout.write(f'Using provided domain: {domain}')
        else:
            # Strip leading http:// or https:// from site URL
            url = settings.PROJECT_METADATA.get('URL', 'example.com')
            domain = url.replace('http://', '').replace('https://', '')
            self.stdout.write(f'Using domain from PROJECT_METADATA: {domain}')
        
        if options['name']:
            name = options['name'][:50]  # Site names have a max of 50 chars
            self.stdout.write(f'Using provided name: {name}')
        else:
            # Site names have a max of 50 chars
            name = settings.PROJECT_METADATA.get('NAME', 'ISP Billing System')[:50]
            self.stdout.write(f'Using name from PROJECT_METADATA: {name}')
        
        # Get or create the site
        site, created = Site.objects.get_or_create(
            id=settings.SITE_ID,
            defaults={
                'domain': domain,
                'name': name,
            }
        )
        
        if not created:
            # Update existing site
            site.domain = domain
            site.name = name
            site.save()
            self.stdout.write(self.style.WARNING(f'Updated existing site (ID: {settings.SITE_ID})'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created new site (ID: {settings.SITE_ID})'))
        
        # Fix PostgreSQL sequence
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT setval(
                        pg_get_serial_sequence('"django_site"','id'), 
                        coalesce(max("id"), 1), 
                        max("id") IS NOT null
                    ) FROM "django_site";
                    """
                )
            self.stdout.write('PostgreSQL sequence updated')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSite configuration complete!\n'
                f'ID: {site.id}\n'
                f'Domain: {site.domain}\n'
                f'Name: {site.name}'
            )
        )
        
        # Show how to use in different environments
        self.stdout.write(
            '\nFor different environments, you can override:\n'
            '  Development: python manage.py setup_default_site --domain=localhost:8000 --name="ISP Dev"\n'
            '  Staging: python manage.py setup_default_site --domain=staging.example.com --name="ISP Staging"\n'
            '  Production: python manage.py setup_default_site --domain=billing.example.com --name="ISP Billing"'
        )
