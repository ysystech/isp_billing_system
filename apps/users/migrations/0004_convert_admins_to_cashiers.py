from django.db import migrations


def convert_admin_to_cashier(apps, schema_editor):
    """Convert all existing ADMIN users to CASHIER type."""
    CustomUser = apps.get_model('users', 'CustomUser')
    
    # Update all non-superuser ADMIN users to CASHIER
    admin_users = CustomUser.objects.filter(user_type='ADMIN', is_superuser=False)
    if admin_users.exists():
        print(f"\nConverting {admin_users.count()} admin user(s) to cashier type...")
        admin_users.update(user_type='CASHIER')
        print("Conversion complete.")


def reverse_conversion(apps, schema_editor):
    """Reverse operation - not really reversible since we don't know which cashiers were admins."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_customuser_user_type'),
    ]

    operations = [
        migrations.RunPython(convert_admin_to_cashier, reverse_conversion),
    ]
