# ISP Billing System - Project Knowledge Base (Updated - July 1, 2025)
=================================================================================

## Project Overview
A comprehensive billing management system originally built for a small-scale Internet Service Provider (ISP) in Cagayan de Oro, Northern Mindanao, Philippines. **NOW BEING CONVERTED TO MULTI-TENANT SAAS** to support multiple ISP companies in a single deployment.

### Multi-Tenant Architecture Status
- **Conversion Started**: June 29, 2025
- **Current Status**: Phase 8 of 10 COMPLETE (80% overall)
- **Architecture**: Shared database with row-level tenant isolation
- **Target**: Complete isolation between ISP companies
- **Recent Achievement**: Background tasks and signals now tenant-aware

## Production Deployment Status
- **Live URL**: https://fiberbill.com
- **Deployment Date**: July 1, 2025
- **Server**: Google Cloud Platform (GCE)
- **Server IP**: 34.124.190.52
- **SSL**: Let's Encrypt (auto-renewal enabled)
- **Admin Access**: https://fiberbill.com/admin/
- **SSH Access**: `ssh prod-billing` (configured in local SSH config)

## Technical Stack
- **Backend**: Django 5.2.2 with Python 3.12
- **Frontend**: Django Templates + HTMX + Alpine.js
- **Styling**: Tailwind CSS v4 + DaisyUI
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Development**: Docker Compose
- **Production**: Gunicorn + Nginx
- **Base Framework**: Pegasus SaaS
- **Maps**: Leaflet.js with OpenStreetMap
- **PDF Generation**: WeasyPrint
- **Time Zone**: Asia/Manila (Philippine Standard Time)

## Project Structure
```
/Users/aldesabido/pers/isp_billing_system/
├── apps/
│   ├── tenants/                 # Multi-tenant core
│   │   ├── models.py           # Tenant model
│   │   ├── middleware.py       # Request tenant context
│   │   ├── backends.py         # Permission bypass for owners
│   │   ├── mixins.py           # TenantRequiredMixin, @tenant_required
│   │   ├── api_mixins.py       # API tenant filtering mixins
│   │   ├── context.py          # Tenant context for background tasks
│   │   ├── tasks.py            # Tenant-aware task base classes
│   │   ├── signals.py          # Tenant lifecycle signals
│   │   ├── test_isolation.py   # Comprehensive isolation tests
│   │   ├── test_api_isolation.py # API isolation tests
│   │   ├── tests/              # All tenant-related tests
│   │   ├── management/         # Tenant commands
│   │   └── verification/       # Phase 7 verification tools
│   ├── audit_logs/              # Audit logging system (tenant-aware)
│   ├── barangays/               # Barangay master list (tenant-aware)
│   ├── customers/               # Customer management (tenant-aware)
│   ├── dashboard/               # Dashboard views and widgets
│   ├── lcp/                     # LCP infrastructure (tenant-aware)
│   ├── routers/                 # Router inventory (tenant-aware)
│   ├── subscriptions/           # Subscription plans (tenant-aware)
│   ├── customer_installations/  # Customer installations (tenant-aware)
│   ├── customer_subscriptions/  # Customer payments (tenant-aware)
│   ├── network/                 # Network visualization
│   ├── tickets/                 # Support tickets (tenant-aware)
│   ├── reports/                 # Reporting system
│   ├── roles/                   # RBAC roles (tenant-aware)
│   ├── users/                   # User auth (multi-tenant updates)
│   ├── utils/                   # Utilities including test_base.py
│   └── web/                     # Public pages
├── templates/                   # Django templates
├── assets/                      # Frontend assets (Vite)
├── requirements/                # Python dependencies
├── deploy_fiberbill.sh         # Production deployment script
├── update_production.sh        # Full update script with migrations
├── quick_update.sh             # Quick update for minor changes
├── rollback_production.sh      # Emergency rollback script
├── UPDATE_GUIDE.md             # Update procedures documentation
├── deployment_credentials.txt  # Production credentials (git-ignored)
├── MULTITENANT_STATUS.md       # Current conversion status
├── PHASE1-8_COMPLETE.md        # Phase documentation files
└── TODO.md                      # Project TODO list
```

## Deployment Scripts and Locations

### Local Scripts (Development Machine)
All deployment and update scripts are located in: `/Users/aldesabido/pers/isp_billing_system/`

1. **deploy_fiberbill.sh** - Initial deployment script
   - Full server setup from scratch
   - Installs all dependencies
   - Configures SSL certificates
   - Creates systemd services

2. **update_production.sh** - Full update script
   - Creates complete backup
   - Updates code from Git
   - Runs migrations
   - Updates dependencies
   - Rebuilds frontend
   - Restarts services

3. **quick_update.sh** - Quick update script
   - Simple code pull
   - Service restart only
   - For minor changes

4. **rollback_production.sh** - Emergency rollback
   - Restores from backup
   - Database rollback
   - Code restoration

### Production Scripts (Server)
Scripts are copied to: `/home/ubuntu/` on the production server
- Access via: `ssh prod-billing`
- All scripts have execute permissions

### Production Paths
- **Application**: `/home/ubuntu/isp_billing_system/`
- **Virtual Environment**: `/home/ubuntu/isp_billing_system/venv/`
- **Logs**: `/home/ubuntu/isp_billing_system/logs/`
- **Media Files**: `/home/ubuntu/isp_billing_system/media/`
- **Static Files**: `/home/ubuntu/isp_billing_system/staticfiles/`
- **Backups**: `/home/ubuntu/backups/`
- **Nginx Config**: `/etc/nginx/sites-available/fiberbill`
- **Systemd Services**: `/etc/systemd/system/isp_billing*.service`

## Production Services

### Systemd Services
- `isp_billing.service` - Main Gunicorn application
- `isp_billing_celery.service` - Celery worker
- `isp_billing_celerybeat.service` - Celery beat scheduler

### Service Management Commands
```bash
# Check status
sudo systemctl status isp_billing
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# Restart services
sudo systemctl restart isp_billing
sudo systemctl restart isp_billing_celery
sudo systemctl restart isp_billing_celerybeat

# View logs
sudo journalctl -u isp_billing -f
sudo tail -f /var/log/nginx/error.log
```

## Multi-Tenant Architecture Implementation

### Core Principles
1. **User-Tenant Relationship**: One user belongs to exactly one tenant (ISP company)
2. **Tenant Owner Permissions**: Flag `is_tenant_owner` gives full permissions bypass within tenant
3. **Registration Flow**: Creates tenant automatically from "Company Name" field
4. **Data Isolation**: Complete - no shared data between tenants
5. **No Default Data**: Each tenant starts with empty data (including Barangays)
6. **Permission Strategy**: Tenant owners bypass all permissions; others use RBAC
7. **No Super Admin Access**: No cross-tenant access for anyone
8. **Fresh Start**: Will delete existing data and start clean after conversion

### Technical Implementation
```python
# Tenant Model
class Tenant(BaseModel):
    name = CharField(max_length=100, unique=True)
    is_active = BooleanField(default=True)
    created_by = OneToOneField(User, related_name='owned_tenant')

# User Model Updates
class CustomUser(AbstractUser):
    tenant = ForeignKey(Tenant, on_delete=PROTECT)
    is_tenant_owner = BooleanField(default=False)

# Base Model for Tenant Isolation
class TenantAwareModel(BaseModel):
    tenant = ForeignKey(Tenant, on_delete=CASCADE)
    class Meta:
        abstract = True
        indexes = [Index(fields=['tenant'])]
```

## Development Commands
```bash
# Build frontend
make npm-build          # Production
make npm-dev           # Development

# Server management
make start             # Start all services
make start-bg          # Start in background
make stop              # Stop all services

# Django commands
make manage ARGS="command"     # Run Django management command
make shell                     # Django shell
make dbshell                  # Database shell
make ssh                      # SSH into web container

# Testing
make test                      # Run all tests
make test ARGS='app.tests'     # Run specific tests

# Multi-tenant specific
make manage ARGS="create_test_tenant"  # Create test tenant
make manage ARGS="verify_tenant_isolation"  # Verify isolation
make manage ARGS="test_phase8"  # Test Phase 8 implementation

# Code quality
make ruff-lint                 # Lint Python code
make ruff-format              # Format Python code
```

## Production Update Workflow

### For Major Updates (with migrations)
```bash
# On local machine
git add .
git commit -m "Description of changes"
git push origin main

# On server
ssh prod-billing
./update_production.sh
```

### For Minor Updates (no migrations)
```bash
# Push changes to Git first, then:
ssh prod-billing
./quick_update.sh
```

### Emergency Rollback
```bash
ssh prod-billing
./rollback_production.sh
# Follow prompts to select backup
```

## Production Credentials
- **Server SSH**: `ssh prod-billing`
- **Admin Username**: admin
- **Admin Password**: 722436Aa!
- **Database**: PostgreSQL on localhost
- **Django Secret**: Stored in production .env file
- Full credentials saved in: `deployment_credentials.txt` (git-ignored)

## Automated Backups
- **Schedule**: Daily at 2 AM Philippine time
- **Location**: `/home/ubuntu/backups/`
- **Retention**: 7 days
- **Includes**: Database, media files, environment config
- **Script**: `/home/ubuntu/backup_isp_billing.sh`

## Multi-Tenant Conversion Progress

### ✅ Completed Phases (1-8)
1. **Core Infrastructure**: Tenant model, middleware, authentication
2. **Model Updates**: All models made tenant-aware
3. **View Layer**: All views require tenant context
4. **Test Infrastructure**: Comprehensive test coverage
5. **API Layer**: All APIs filter by tenant
6. **Template Updates**: UI shows tenant context
7. **Security Verification**: Isolation confirmed
8. **Background Tasks**: Celery tasks tenant-aware

### 📋 Remaining Phases (9-10)
9. **Reporting System**: Make reports tenant-scoped
10. **Testing & Migration**: Final testing and data migration

## Security Best Practices Implemented

### Backend Security
- All views require authentication and tenant context
- Tenant owners bypass permissions within their tenant
- All querysets filter by tenant automatically
- Background tasks maintain tenant isolation
- No cross-tenant data access possible

### Frontend Security
- Permission checks in templates
- Tenant context displayed in navigation
- Actions hidden based on permissions

### Data Integrity
- Tenant field required on all business models
- CASCADE delete ensures data cleanup
- Forms validate tenant context
- Background tasks process each tenant separately

## Known Issues/TODOs

### Multi-Tenant Conversion
1. **Phases 9-10**: Complete remaining conversion phases
2. **Model Validation**: Add model-level FK validation
3. **Reports**: Make all reports tenant-scoped
4. **Migration Strategy**: Plan for existing data

### Future Multi-Tenant Features
1. **Tenant Billing**: SaaS subscription management
2. **Tenant Settings**: Per-tenant customization
3. **User Invitations**: Add users to tenant
4. **Tenant Export**: Data portability
5. **Usage Metrics**: Per-tenant analytics

## Summary

The ISP Billing System is successfully deployed to production at https://fiberbill.com with 80% of multi-tenant conversion complete. The system features:

- ✅ Live production deployment with SSL
- ✅ Automated deployment and update scripts
- ✅ Daily automated backups
- ✅ Complete data isolation between tenants
- ✅ Background tasks maintain tenant isolation
- ✅ Comprehensive security and permission system
- ✅ Emergency rollback capability
- ✅ Production monitoring and logging

The remaining work focuses on reporting system updates and preparing for full multi-tenant production deployment.