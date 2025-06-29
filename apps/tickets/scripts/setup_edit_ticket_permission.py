"""
Script to add the edit_ticket permission and update role mappings.
Run with: make manage ARGS="runscript tickets.scripts.setup_edit_ticket_permission"
"""
from django.contrib.auth.models import Permission, ContentType
from django.db import transaction

def run():
    """Add the edit_ticket permission and update role mappings."""
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
                print("✅ Created edit_ticket permission successfully!")
            else:
                print("⚠️ Permission edit_ticket already exists.")
            
            # Now run the permission mapping command
            from django.core.management import call_command
            print("\n📊 Running permission mapping...")
            call_command('map_permissions_to_categories', verbosity=1)
            
            print("\n🔄 Done! The new permissions are now available.")
            print("⚠️ IMPORTANT: You need to assign the new permissions to your roles.")
            print("Visit http://localhost:8000/roles/ to update your roles.")
                
    except Exception as e:
        print(f"❌ Error creating permission: {e}")
        raise