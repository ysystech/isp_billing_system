# Generated manually to handle barangay field conversion

from django.db import migrations, models
import django.db.models.deletion


def convert_barangay_data(apps, schema_editor):
    """Convert existing barangay string data to ForeignKey relationships"""
    Customer = apps.get_model("customers", "Customer")
    Barangay = apps.get_model("barangays", "Barangay")
    
    # First ensure barangays are created
    # This will be done by the barangay migration dependency
    
    # Map old barangay values to new barangay objects
    for customer in Customer.objects.all():
        if hasattr(customer, 'barangay') and customer.barangay:
            # Find or create the barangay
            barangay_name = customer.barangay
            
            # Handle special cases where old value might be a code
            barangay_mapping = {
                "1": "Barangay 1",
                "2": "Barangay 2",
                "3": "Barangay 3",
                "4": "Barangay 4",
                "5": "Barangay 5",
                "6": "Barangay 6",
                "7": "Barangay 7",
                "8": "Barangay 8",
                "9": "Barangay 9",
                "10": "Barangay 10",
                # Add more mappings as needed
            }
            
            if barangay_name in barangay_mapping:
                barangay_name = barangay_mapping[barangay_name]
            
            try:
                barangay_obj = Barangay.objects.get(name=barangay_name)
                customer.barangay_new = barangay_obj
                customer.save()
            except Barangay.DoesNotExist:
                # Create a new barangay if it doesn't exist
                barangay_obj = Barangay.objects.create(
                    name=barangay_name,
                    code=barangay_name[:4].upper(),
                    is_active=True
                )
                customer.barangay_new = barangay_obj
                customer.save()


def reverse_convert_barangay_data(apps, schema_editor):
    """Reverse the conversion"""
    Customer = apps.get_model("customers", "Customer")
    
    for customer in Customer.objects.all():
        if hasattr(customer, 'barangay_new') and customer.barangay_new:
            customer.barangay = customer.barangay_new.name
            customer.save()


class Migration(migrations.Migration):
    dependencies = [
        ("customers", "0003_rename_customers_c_email_7f9e94_idx_customers_c_email_4fdeb3_idx_and_more"),
        ("barangays", "0002_populate_initial_data"),
    ]

    operations = [
        # First, add a temporary field for the new ForeignKey
        migrations.AddField(
            model_name="customer",
            name="barangay_new",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="temp_customers",
                to="barangays.barangay",
            ),
        ),
        
        # Remove the old field
        migrations.RemoveField(
            model_name="customer",
            name="barangay",
        ),
        
        # Rename the new field to the original name
        migrations.RenameField(
            model_name="customer",
            old_name="barangay_new",
            new_name="barangay",
        ),
        
        # Update the field to make it required and fix the related name
        migrations.AlterField(
            model_name="customer",
            name="barangay",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="customers",
                to="barangays.barangay",
                help_text="Customer's barangay",
            ),
        ),
    ]
