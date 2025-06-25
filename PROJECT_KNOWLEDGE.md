ISP Billing System - Project Knowledge Base (Updated)
=====================================================

## Project Overview
A comprehensive billing management system for a small-scale Internet Service Provider (ISP) operating in Cagayan de Oro, Northern Mindanao, Philippines. Built for localized network coverage with manual infrastructure and personalized customer service.

## Technical Stack
- **Backend**: Django 4.x with Python 3.12
- **Frontend**: Django Templates + HTMX + Alpine.js
- **Styling**: Tailwind CSS v4 + DaisyUI
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Development**: Docker Compose
- **Base Framework**: Pegasus SaaS

## Project Structure
```
/Users/aldesabido/pers/isp_billing_system/
├── apps/
│   ├── barangays/        # Barangay master list
│   ├── customers/        # Customer management
│   ├── dashboard/        # Admin dashboard
│   ├── routers/          # Router inventory
│   ├── subscriptions/    # Subscription plans
│   ├── users/            # User authentication & management
│   └── web/              # Public pages
├── templates/            # Django templates
├── assets/              # Frontend assets (Vite)
└── requirements/        # Python dependencies
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

# Code quality
make ruff-lint                 # Lint Python code
make ruff-format              # Format Python code
```

## Coding Standards

### Python
- PEP 8 with 120 character line limit
- Double quotes for strings
- Type hints encouraged but not required
- All models extend `apps.utils.models.BaseModel`
- Function-based views preferred
- Django ORM best practices

### Templates
- 2 spaces indentation
- Use `{% extends "web/app/app_base.html" %}` for app pages
- DaisyUI components preferred
- HTMX for server interactions
- Alpine.js for client-only interactions

### JavaScript
- ES6+ syntax
- 2 spaces indentation
- Single quotes for strings
- Use generated OpenAPI client for APIs

## Database Schema

### Core Models

#### Customer
- Personal and contact information
- Foreign key to Barangay
- Status tracking (Active/Inactive/Suspended/Terminated)
- Installation details
- Soft delete support

#### Barangay
- Master list of service areas (80 barangays in CDO)
- Active/inactive status
- Related customers tracking

#### Router
- Basic inventory tracking
- Brand, model, serial number
- No deployment tracking (simplified)

#### SubscriptionPlan
- Name (unique)
- Description
- Speed (Mbps)
- Price (PHP)
- Active/inactive status

#### CustomUser
- Extended Django User model
- User types: Cashier, Technician (only superuser is admin)
- Full name, email, username
- Active/inactive status

## Features Implemented

### Phase 1 Complete ✅
**Customer Management**
- Complete CRUD with search/filter
- Status tracking
- Installation history
- Barangay-based organization

**Master Lists**
- Barangays (service areas)
- Routers (inventory)

**Dashboard**
- Customer statistics
- Barangay distribution
- Router inventory count

### Phase 2 Complete ✅
**Subscription Plans**
- Complete CRUD operations
- Search and filter by name/status
- Price and speed tracking
- Active/inactive status
- Dashboard statistics widget

**User Management**
- Complete CRUD for non-superuser accounts
- User types: Cashier, Technician (only superuser can be admin)
- Email as username
- Password management
- Excludes superusers from lists
- Dashboard statistics widget

## Upcoming Phases

### Phase 3: Customer Subscriptions
- Link customers to subscription plans
- Billing cycles (Weekly/Quincenal/Monthly)
- Subscription history
- Plan changes tracking

### Phase 4: Billing System
- Invoice generation
- Payment tracking
- Billing reports
- Payment history

### Phase 5: Enhanced Features
- Automated reminders
- Payment gateway integration
- Advanced reporting
- SMS notifications

### Phase 6: Mobile Client
- Flutter application
- Customer self-service
- Payment submissions
- Usage monitoring

## Business Rules

### Customers
- Unique email required
- Must belong to a barangay
- Can be soft deleted
- Status workflow: Active → Suspended → Terminated

### Barangays
- Cannot delete if has customers
- Used for geographical reporting
- Controls service area coverage

### Routers
- Simple inventory tracking
- Unique serial numbers
- No assignment logic (for now)

### Subscription Plans
- Unique plan names
- Positive speed values
- Non-negative prices
- Can be deactivated

### Users
- Superusers excluded from management
- Only superuser can be admin (system admin)
- Email used as username
- User types determine role in system (Cashier, Technician)

## API Endpoints
- Currently using Django views
- REST API planned for mobile app
- HTMX endpoints for dynamic UI

## Security
- Django authentication
- Role-based access (superuser required for user management)
- CSRF protection (configured globally for HTMX)
- Session-based auth for web
- Password hashing using Django standards

## Performance Considerations
- Pagination on all list views (20 items)
- Database indexes on search fields
- Select/prefetch related for ORM queries
- Redis caching ready

## Deployment Notes
- Docker-based deployment
- Environment variables in .env
- Static files served by WhiteNoise
- Media files in /media/

## Sample Data Generators
```bash
make manage ARGS="generate_customers --count=50"
make manage ARGS="generate_routers --count=20"
make manage ARGS="generate_subscription_plans"
make manage ARGS="generate_sample_users"
```

## Testing
- Unit tests for models
- View tests for CRUD operations
- Form validation tests
- Use `make test` to run test suite

## Important Technical Notes

### HTMX Configuration
- CSRF token configured globally in base template: `<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>`
- No need to manually add CSRF headers to individual HTMX calls
- Use simple `htmx.ajax('METHOD', 'url')` syntax

### User Type Changes
- ADMIN user type removed from choices
- Existing admin users migrated to CASHIER type
- Only superuser (created with `createsuperuser`) has admin privileges

## Known Issues/TODOs
- No subscription assignment to customers yet
- No billing/invoice system
- No payment tracking
- No customer portal
- No SMS integration
- No role-based page restrictions (all authenticated users can access all pages)

## Data Management
- Migrations tracked in version control
- Sample data generators for testing
- Soft delete for customers
- User deactivation instead of deletion
