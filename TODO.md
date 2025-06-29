# ISP Billing System - TODO List

## High Priority Features

### 1. Audit Log System
- **Status**: Permission exists (`view_logentry`) but no implementation
- **Description**: Need to create a user-facing audit log viewer
- **Requirements**:
  - Track all CRUD operations across the system
  - Show who did what and when
  - Include IP addresses and user agents
  - Filterable by user, date, action type, and model
  - Exportable to CSV/PDF
- **Location**: Should be accessible from User Management section
- **Permission**: `admin.view_logentry` already exists

### 2. ~~Reports Simplification~~ ✅ COMPLETED (June 29, 2025)
- ~~Currently 16 permissions in Reports & Analytics~~
- ~~Could be simplified to 11 permissions (1 per report page)~~
- ~~Waiting for decision on implementation~~
- **DONE**: Successfully reduced from 20 to 11 permissions
  - 1 dashboard permission
  - 7 individual report permissions
  - 2 performance dashboard permissions
  - 1 export permission

## Medium Priority

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

## Low Priority

### 6. Customer Portal
- Self-service interface
- View bills and payment history
- Submit tickets

### 7. Mobile App
- Field technician app
- Installation management
- Ticket updates

## Technical Debt

### ~~8. MAC Address Field Migration~~ ✅ COMPLETED (June 29, 2025)
- ~~Router model has MAC address field~~
- ~~Need to make it non-nullable after updating existing records~~
- **DONE**: All existing routers now have MAC addresses
- **DONE**: Field is now required (non-nullable)
- Generated MAC addresses use TP-Link OUI prefix (50:C7:BF)

### 9. Performance Optimization
- Query optimization for large datasets
- Implement caching strategies
- Database indexing review

## Completed Features ✅
- RBAC Permission System (simplified from 107 to 70 permissions)
- Geo-location for infrastructure
- Hierarchical network selection
- Prepaid subscription system
- Support ticket workflow
- Acknowledgment receipt generation
- Reports Permission Simplification (reduced from 20 to 11 permissions - June 29, 2025)
- MAC Address Field Migration (made non-nullable - June 29, 2025)
