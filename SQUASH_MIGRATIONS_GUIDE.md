# Squashing Migrations Guide - ISP Billing System

## Overview
This guide will help you squash all migrations and start fresh with the multi-tenant structure from the beginning.

## Prerequisites
- Backup any important data (if any)
- Ensure all code changes are committed to git
- Stop the development server

## Step-by-Step Process

### 1. Create Fresh Migration Files

First, we'll create new initial migrations that capture the current state of all models:

```bash
# Stop all services
make stop

# Remove all existing migration files (but keep __init__.py)
find apps -path "*/migrations/*.py" -not -name "__init__.py" -delete

# Create new migrations for all apps
make manage ARGS="makemigrations"
```

### 2. Update Initial Data Setup

Since we're starting fresh, all initial data is set up with a single command:

```bash
# This runs all setup commands:
# - setup_default_site
# - setup_permission_categories  
# - map_permissions_to_categories
# - setup_report_permissions
make manage ARGS="initial_setup"

# Or with environment-specific options:
make manage ARGS="initial_setup --domain=localhost:8000 --name='ISP Dev'"
```

### 3. Reset the Database

```bash
# Drop the existing database and create a new one
make manage ARGS="dbshell"
# Then in the PostgreSQL shell:
DROP DATABASE isp_billing_system;
CREATE DATABASE isp_billing_system;
\q

# Or more simply, if using Docker:
docker-compose down -v  # This removes volumes
docker-compose up -d db
```

### 4. Run Fresh Migrations

```bash
# Run migrations on the clean database
make manage ARGS="migrate"

# Create a superuser
make manage ARGS="createsuperuser"

# Run initial setup (all commands at once)
make manage ARGS="initial_setup"
```

### 5. Create Default Tenant (Optional)

You might want to create a management command for setting up a default tenant:

```python
# apps/tenants/management/commands/create_default_tenant.py
from django.core.management.base import BaseCommand
from apps.tenants.models import Tenant
from apps.users.models import CustomUser

class Command(BaseCommand):
    help = 'Create a default tenant for development'

    def handle(self, *args, **options):
        tenant, created = Tenant.objects.get_or_create(
            name='Default ISP Company',
            defaults={'is_active': True}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created tenant: {tenant.name}'))
        else:
            self.stdout.write(f'Tenant already exists: {tenant.name}')
```

## Benefits of Squashing

1. **Clean History**: No more migration clutter from the single-tenant to multi-tenant conversion
2. **Faster Migrations**: One migration per app instead of many
3. **Easier Deployment**: New deployments don't need to replay the entire conversion history
4. **Consistent Schema**: All tables have tenant fields from the start

## Important Notes

1. **Data Loss**: This process will delete all existing data. Make sure to backup if needed.

2. **Team Coordination**: If working with a team, coordinate this change as everyone will need to reset their databases.

3. **Production**: Never do this on a production database with real data. This is only for development/staging environments or before initial production deployment.

4. **Git History**: After squashing, commit the new migration files:
   ```bash
   git add apps/*/migrations/0001_initial.py
   git commit -m "Squash migrations: Fresh start with multi-tenant structure"
   ```

## Verification

After completing the process, verify everything works:

```bash
# Check migrations
make manage ARGS="showmigrations"

# Start the server
make start

# Run tests
make test
```

## Migration File Structure After Squashing

Each app will have just one initial migration:
```
apps/
├── audit_logs/migrations/0001_initial.py
├── barangays/migrations/0001_initial.py
├── customer_installations/migrations/0001_initial.py
├── customer_subscriptions/migrations/0001_initial.py
├── customers/migrations/0001_initial.py
├── lcp/migrations/0001_initial.py
├── reports/migrations/0001_initial.py
├── roles/migrations/0001_initial.py
├── routers/migrations/0001_initial.py
├── subscriptions/migrations/0001_initial.py
├── tenants/migrations/0001_initial.py
├── tickets/migrations/0001_initial.py
└── users/migrations/0001_initial.py
```

## Alternative: Squash Without Data Loss

If you need to preserve data, Django's `squashmigrations` command can be used, but it's more complex and not recommended for this multi-tenant conversion scenario.

## Completion

Once done, you'll have a clean, multi-tenant application from the ground up with:
- All models inheriting from TenantAwareModel
- Clean migration history
- Proper initial data setup through management commands
- No legacy single-tenant artifacts
