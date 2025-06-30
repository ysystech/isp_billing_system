"""
Management command to run all initial setup commands in the correct order.
This is a convenience command that runs all setup after fresh migrations.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Run all initial setup commands for the ISP Billing System'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-site',
            action='store_true',
            help='Skip setting up the default site',
        )
        parser.add_argument(
            '--domain',
            type=str,
            help='Domain for the default site (passed to setup_default_site)',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Name for the default site (passed to setup_default_site)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('ISP Billing System - Initial Setup'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # 1. Setup default site
        if not options['skip_site']:
            self.stdout.write('\n📍 Setting up default site...')
            site_args = []
            if options['domain']:
                site_args.extend(['--domain', options['domain']])
            if options['name']:
                site_args.extend(['--name', options['name']])
            
            try:
                call_command('setup_default_site', *site_args)
                self.stdout.write(self.style.SUCCESS('✅ Default site configured'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to setup default site: {e}'))
                return
        
        # 2. Setup permission categories
        self.stdout.write('\n📁 Setting up permission categories...')
        try:
            call_command('setup_permission_categories', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Permission categories created'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to setup permission categories: {e}'))
            return
        
        # 3. Map permissions to categories
        self.stdout.write('\n🔗 Mapping permissions to categories...')
        try:
            call_command('map_permissions_to_categories', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Permissions mapped to categories'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to map permissions: {e}'))
            return
        
        # 4. Setup report permissions
        self.stdout.write('\n📊 Setting up report permissions...')
        try:
            call_command('setup_report_permissions', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Report permissions configured'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to setup report permissions: {e}'))
            return
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ All initial setup completed successfully!'))
        self.stdout.write('=' * 60)
        
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Create a superuser: make manage ARGS="createsuperuser"')
        self.stdout.write('2. Start the server: make start')
        self.stdout.write('3. Login and create your first tenant\n')
        
        # Show different environment examples
        self.stdout.write('\nFor different environments, run with options:')
        self.stdout.write('  Dev: make manage ARGS="initial_setup --domain=localhost:8000 --name=\'ISP Dev\'"')
        self.stdout.write('  Staging: make manage ARGS="initial_setup --domain=staging.example.com --name=\'ISP Staging\'"')
        self.stdout.write('  Production: make manage ARGS="initial_setup --domain=billing.example.com --name=\'ISP Billing\'"\n')
