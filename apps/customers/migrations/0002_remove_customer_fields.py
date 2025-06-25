# Generated migration to remove fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='middle_name',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='phone_secondary',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='city',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='province',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='postal_code',
        ),
    ]
