"""
Management command to set up the edit_ticket permission.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, ContentType
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates the edit_ticket permission and updates permission mappings'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Get the content type for the ticket model
                content_type = ContentType.objects.get(app_label='tickets', model='ticket')
                
                # Check if the permission already exists
                if not Permission.objects.filter(
                    content_type=content_type,
                    codename='edit_ticket'
                ).exists():
                    # Create the new permission
                    Permission.objects.create(
                        content_type=content_type,
                        codename='edit_ticket',
                        name='Can edit ticket'
                    )
                    self.stdout.write(self.style.SUCCESS("✅ Created edit_ticket permission successfully!"))
                else:
                    self.stdout.write(self.style.WARNING("⚠️ Permission edit_ticket already exists."))
                
                # Now run the permission mapping command
                from django.core.management import call_command
                self.stdout.write(self.style.NOTICE("\n📊 Running permission mapping..."))
                call_command('map_permissions_to_categories', verbosity=1)
                
                self.stdout.write(self.style.SUCCESS("\n🔄 Done! The new permissions are now available."))
                self.stdout.write(self.style.WARNING("⚠️ IMPORTANT: You need to assign the new permissions to your roles."))
                self.stdout.write("Visit http://localhost:8000/roles/ to update your roles.")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creating permission: {e}"))
            raise