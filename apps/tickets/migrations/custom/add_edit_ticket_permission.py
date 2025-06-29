"""
Custom migration script to add the edit_ticket permission.
Run with: make manage ARGS="runscript tickets.migrations.custom.add_edit_ticket_permission"
"""
from django.contrib.auth.models import Permission, ContentType
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

def run():
    """Add the edit_ticket permission if it doesn't exist."""
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
                
            # Update the permission mapping
            print("\nℹ️ Next steps:")
            print("1. Run: make manage ARGS='map_permissions_to_categories'")
            print("2. Restart your development server")
            print("3. Update role permissions in the admin interface")
                
    except Exception as e:
        print(f"❌ Error creating permission: {e}")
        raise
