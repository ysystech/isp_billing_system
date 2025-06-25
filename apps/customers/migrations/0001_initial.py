# Generated migration for initial Customer model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('middle_name', models.CharField(blank=True, max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone_primary', models.CharField(max_length=20)),
                ('phone_secondary', models.CharField(blank=True, max_length=20)),
                ('street_address', models.CharField(max_length=255)),
                ('barangay', models.CharField(max_length=100)),
                ('city', models.CharField(default='Cagayan de Oro', max_length=100)),
                ('province', models.CharField(default='Misamis Oriental', max_length=100)),
                ('postal_code', models.CharField(default='9000', max_length=10)),
                ('installation_date', models.DateField(blank=True, null=True)),
                ('installation_notes', models.TextField(blank=True)),
                ('installation_technician', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('suspended', 'Suspended'), ('terminated', 'Terminated')], default='active', max_length=20)),
                ('notes', models.TextField(blank=True, help_text='Internal notes about the customer')),
                ('user', models.OneToOneField(blank=True, help_text='Linked user account for customer portal access', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='customer_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['email'], name='customers_c_email_7f9e94_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['status'], name='customers_c_status_1cd0cf_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['last_name', 'first_name'], name='customers_c_last_na_f91b1d_idx'),
        ),
    ]
