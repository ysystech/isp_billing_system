# ISP Billing System - Project Knowledge Base (Multi-Tenant Update - June 29, 2025)
=================================================================================

## Project Overview
A comprehensive billing management system originally built for a small-scale Internet Service Provider (ISP) in Cagayan de Oro, Northern Mindanao, Philippines. **NOW BEING CONVERTED TO MULTI-TENANT SAAS** to support multiple ISP companies in a single deployment.

### Multi-Tenant Architecture Status
- **Conversion Started**: June 29, 2025
- **Architecture**: Shared database with row-level tenant isolation
- **Current Phase**: Phase 1 (Core Infrastructure) ✅ COMPLETE
- **Target**: Complete isolation between ISP companies

## Technical Stack
- **Backend**: Django 5.2.2 with Python 3.12
- **Frontend**: Django Templates + HTMX + Alpine.js
- **Styling**: Tailwind CSS v4 + DaisyUI
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Development**: Docker Compose
- **Base Framework**: Pegasus SaaS
- **Maps**: Leaflet.js with OpenStreetMap
- **PDF Generation**: WeasyPrint
- **Time Zone**: Asia/Manila (Philippine Standard Time)

## Multi-Tenant Architecture Decisions

### Core Principles:
1. **User-Tenant Relationship**: One user belongs to exactly one tenant (ISP company)
2. **Tenant Owner Permissions**: Flag `is_tenant_owner` gives full permissions bypass within tenant
3. **Registration Flow**: Creates tenant automatically from "Company Name" field
4. **Data Isolation**: Complete - no shared data between tenants
5. **No Default Data**: Each tenant starts with empty data (including Barangays)
6. **Permission Strategy**: Tenant owners bypass all permissions; others use RBAC
7. **No Super Admin Access**: No cross-tenant access for anyone
8. **Fresh Start**: Will delete existing data and start clean after conversion

### Technical Implementation:
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

## Project Structure
```
/Users/aldesabido/pers/isp_billing_system/
├── apps/
│   ├── tenants/                 # Multi-tenant core (NEW)
│   │   ├── models.py           # Tenant model
│   │   ├── middleware.py       # Request tenant context
│   │   ├── backends.py         # Permission bypass for owners
│   │   ├── mixins.py           # TenantRequiredMixin
│   │   └── management/         # Tenant commands
│   ├── audit_logs/              # Audit logging system
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
│   ├── roles/                   # RBAC roles (will be tenant-aware)
│   ├── users/                   # User auth (multi-tenant updates)
│   └── web/                     # Public pages
├── templates/
│   ├── components/              # Reusable components
│   ├── network/                 # Network visualization
│   ├── audit_logs/              # Audit log templates
│   └── roles/                   # Role management
├── assets/                      # Frontend assets (Vite)
├── requirements/                # Python dependencies
├── MULTITENANT_CONTEXT.md      # Conversion context
├── PHASE1_COMPLETE.md          # Phase 1 documentation
└── TODO.md                      # Project TODO list
```

## Multi-Tenant Conversion Phases

### ✅ Phase 1: Core Infrastructure (COMPLETE)
- Tenant model and admin
- User model updates (tenant, is_tenant_owner)
- TenantAwareModel abstract class
- Tenant middleware for request.tenant
- Authentication backend for permission bypass
- Registration creates tenant
- Management commands for testing

### 🚧 Phase 2: Model Updates (IN PROGRESS)
- Update all models to inherit from TenantAwareModel
- Create and run migrations for tenant fields
- Models already updated (need migrations):
  - Customer, Barangay, Router, SubscriptionPlan
  - LCP, Splitter, NAP
  - CustomerInstallation, CustomerSubscription
  - Ticket
- Models pending update:
  - TicketComment, Role, PermissionCategory
  - AuditLogEntry

### 📋 Phase 3: View Layer Updates (PLANNED)
- Add TenantRequiredMixin to all CBVs
- Add @tenant_required decorator to all FBVs
- Update all querysets to filter by tenant
- Ensure forms set tenant on new objects

### 📋 Phase 4: Permission System Updates (PLANNED)
- Update permission checks for is_tenant_owner
- Make RBAC system tenant-aware
- Scope role assignment by tenant
- Ensure audit logs are tenant-isolated

### 📋 Phase 5: API Endpoints Updates (PLANNED)
- Filter all API views by tenant
- Add tenant validation to serializers
- Update API permissions

### 📋 Phase 6: Template Updates (PLANNED)
- Add tenant name display in UI
- Remove cross-tenant data displays
- Update admin panel for tenant awareness

### 📋 Phase 7: Data Isolation Verification (PLANNED)
- Create query logging middleware (dev only)
- Add tenant isolation tests
- Verify no data leakage
- Check raw SQL queries

### 📋 Phase 8: Background Tasks & Signals (PLANNED)
- Update Celery tasks for tenant awareness
- Ensure signals respect tenant boundaries
- Update scheduled tasks

### 📋 Phase 9: Reporting System Updates (PLANNED)
- Filter all reports by tenant
- Remove global statistics
- Update charts/graphs
- Scope exports by tenant

### 📋 Phase 10: Testing & Migration (PLANNED)
- Comprehensive test suite
- Test registration flow
- Test permission bypass
- Fresh migration strategy
- Delete existing data

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

# Code quality
make ruff-lint                 # Lint Python code
make ruff-format              # Format Python code
```

## Database Schema Updates for Multi-Tenant

### Multi-Tenant Core Models

#### Tenant (NEW)
- `name`: Company/organization name (unique)
- `is_active`: Enable/disable tenant
- `created_by`: OneToOne to owner user
- Inherits BaseModel (created_at, updated_at)

#### CustomUser (UPDATED)
- **NEW**: `tenant` - ForeignKey to Tenant (PROTECT)
- **NEW**: `is_tenant_owner` - Boolean for permission bypass
- All existing fields remain

#### TenantAwareModel (NEW)
- Abstract base for all tenant-isolated models
- `tenant`: ForeignKey with CASCADE delete
- Indexed on tenant field
- All business models inherit from this

### Updated Model Hierarchy
```
BaseModel (timestamps)
    ├── Tenant
    └── TenantAwareModel (adds tenant field)
            ├── Customer
            ├── Barangay
            ├── Router
            ├── SubscriptionPlan
            ├── LCP
            ├── Splitter
            ├── NAP
            ├── CustomerInstallation
            ├── CustomerSubscription
            └── Ticket
```

## Multi-Tenant Business Rules

### Registration & Tenant Creation
- Registration requires company name
- Creates tenant automatically
- Sets registering user as tenant owner
- Owner gets full permissions within tenant

### Data Isolation Rules
- All queries filtered by request.tenant
- No cross-tenant data access
- Tenant field required on all business models
- CASCADE delete when tenant deleted

### Permission Rules
- Superusers: Full system access (legacy)
- Tenant Owners: Full access within tenant
- Regular Users: RBAC permissions within tenant
- No user can access other tenants

### Tenant Management
- Tenants cannot be deleted via admin
- Each tenant has exactly one owner
- Users cannot switch tenants
- No shared resources between tenants

## API Endpoints (To Be Updated)

All existing API endpoints will be updated to:
- Filter results by request.tenant
- Validate tenant ownership
- Prevent cross-tenant access
- Set tenant on created objects

## Security Considerations

### Multi-Tenant Security
- Row-level security via tenant filtering
- Middleware ensures tenant context
- All queries must include tenant filter
- No raw SQL without tenant checks
- Audit logs track tenant actions

### Authentication & Authorization
- Django-allauth for authentication
- Custom backend for tenant owners
- RBAC within tenant boundaries
- CSRF protection enabled
- Login required for all app views

## Known Issues/TODOs

### Multi-Tenant Conversion
1. **Phase 2-10**: Complete remaining conversion phases
2. **Data Migration**: Strategy for existing data
3. **Testing**: Comprehensive multi-tenant tests
4. **Performance**: Optimize tenant filtering
5. **Monitoring**: Tenant isolation monitoring

### Future Multi-Tenant Features
1. **Tenant Billing**: SaaS subscription management
2. **Tenant Settings**: Customization per tenant
3. **User Invitations**: Add users to tenant
4. **Tenant Export**: Data portability
5. **Usage Tracking**: Per-tenant metrics

### Original TODOs (Still Valid)
1. **Email notifications**: Automate communications
2. **SMS Integration**: Payment reminders
3. **Backup System**: Automated backups
4. **Customer Portal**: Self-service interface
5. **Mobile App**: Field technician app

## Configuration Notes

### Environment Variables
- Database: PostgreSQL connection
- Redis: Cache and Celery broker
- Timezone: Asia/Manila (UTC+8)
- Debug: Set to False for production

### Multi-Tenant Middleware
```python
MIDDLEWARE = [
    # ... other middleware ...
    'apps.tenants.middleware.TenantMiddleware',
    # ... rest of middleware ...
]

AUTHENTICATION_BACKENDS = (
    'apps.tenants.backends.TenantAwareBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
```

## Development Guidelines

### Multi-Tenant Development
1. **Always filter by tenant** in views/queries
2. **Use TenantAwareModel** for new models
3. **Test tenant isolation** thoroughly
4. **Never bypass tenant** checks (except owners)
5. **Set tenant on create** for all objects
6. **Use mixins/decorators** for consistency

### General Guidelines
1. Use absolute paths in Desktop Commander
2. Chunk large files (30 lines) for performance
3. Always validate user input server-side
4. Test coordinate features with map widget
5. Follow Django best practices
6. Use HTMX for dynamic updates
7. Maintain backward compatibility
8. Check user permissions before operations
9. All CRUD operations are auto-logged

## Recent Updates (June 29, 2025)

### Evening Session Achievements:
1. ✅ Simplified Reports permissions (20 to 11)
2. ✅ Made Router MAC address non-nullable
3. ✅ Implemented Audit Log System with UI
4. ✅ Added role assignment to User Management
5. ✅ Fixed permission checks in navigation
6. ✅ Created custom permission template tags
7. ✅ Resolved template URL naming issues

### Multi-Tenant Conversion Started:
1. ✅ Phase 1 (Core Infrastructure) COMPLETE
2. ✅ All infrastructure for multi-tenant ready
3. ✅ Tests passing for Phase 1
4. 🚧 Ready for Phase 2 (Model Updates)

## System Completion Status

### Single-Tenant Features: 99% Complete
- All core features working
- Ready for production use
- Only missing convenience features

### Multi-Tenant Conversion: ~10% Complete
- Phase 1 of 10 phases done
- Core infrastructure ready
- Models identified for update
- Clear path forward

## Summary

The ISP Billing System is a mature, production-ready application for single-tenant use. The multi-tenant conversion is underway to transform it into a SaaS platform supporting multiple ISP companies. Phase 1 (Core Infrastructure) is complete, providing the foundation for tenant isolation. The system uses Django's robust features combined with custom middleware and authentication backends to ensure complete data isolation between tenants while maintaining the full feature set for each ISP company.
