# ISP Billing System - TODO List

## 🚨 CRITICAL: Multi-Tenant SaaS Conversion (In Progress)

### Multi-Tenant Conversion Phases
- ✅ **Phase 1: Core Infrastructure** (COMPLETED - June 29, 2025)
  - Tenant model, User updates, Middleware
  - Authentication backend, Registration flow
  - Management commands, Tests

- ✅ **Phase 2: Model Updates** (COMPLETED - January 29, 2025)
  - Updated all models to inherit from TenantAwareModel
  - Created and ran migrations for tenant fields
  - Models updated: TicketComment, Role, AuditLogEntry

- 📋 **Phase 3: View Layer Updates** (TODO)
  - Add TenantRequiredMixin to all Class-Based Views
  - Add @tenant_required decorator to Function-Based Views
  - Update all querysets to filter by tenant

- 📋 **Phase 4: Permission System Updates** (TODO)
  - Update permission checks for is_tenant_owner
  - Make RBAC system tenant-aware
  - Scope role assignment by tenant

- 📋 **Phase 5: API Endpoints Updates** (TODO)
  - Filter all API views by tenant
  - Add tenant validation to serializers

- 📋 **Phase 6: Template Updates** (TODO)
  - Add tenant name display in UI
  - Remove cross-tenant data displays

- 📋 **Phase 7: Data Isolation Verification** (TODO)
  - Create query logging middleware
  - Add tenant isolation tests

- 📋 **Phase 8: Background Tasks & Signals** (TODO)
  - Update Celery tasks for tenant awareness
  - Ensure signals respect tenant boundaries

- 📋 **Phase 9: Reporting System Updates** (TODO)
  - Filter all reports by tenant
  - Remove global statistics

- 📋 **Phase 10: Testing & Migration** (TODO)
  - Comprehensive test suite
  - Fresh migration strategy

## High Priority Features (Post Multi-Tenant)

### 1. Multi-Tenant Billing System
- Tenant subscription plans
- Payment integration
- Usage tracking
- Billing cycles

### 2. Tenant Management Features
- Tenant settings page
- User invitation system
- Tenant data export
- Tenant deletion/archival

### 3. Email Notifications
- Automated customer communications
- Payment reminders
- Ticket status updates

### 4. SMS Integration
- Payment reminders
- Service notifications

### 5. Backup System
- Automated database backups
- Scheduled backups
- Backup retention policy

## Medium Priority

### 6. Customer Portal
- Self-service interface
- View bills and payment history
- Submit tickets

### 7. Mobile App
- Field technician app
- Installation management
- Ticket updates

## Low Priority

### 8. Performance Optimization
- Query optimization for large datasets
- Implement caching strategies
- Database indexing review
- Multi-tenant query optimization

## Completed Features ✅

### Single-Tenant Features (Pre-Conversion)
- RBAC Permission System (simplified from 107 to 70 permissions)
- Geo-location for infrastructure
- Hierarchical network selection
- Prepaid subscription system
- Support ticket workflow
- Acknowledgment receipt generation
- Reports Permission Simplification (reduced from 20 to 11 permissions - June 29, 2025)
- MAC Address Field Migration (made non-nullable - June 29, 2025)
- Audit Log System (full UI implementation - June 29, 2025)

### Multi-Tenant Infrastructure
- Multi-Tenant Phase 1: Core Infrastructure (June 29, 2025)
  - Tenant model and admin
  - User model updates
  - TenantAwareModel abstract class
  - Middleware and authentication backend
  - Registration creates tenant automatically
