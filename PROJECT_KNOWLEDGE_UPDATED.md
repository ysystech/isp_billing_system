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
│   ├── dashboard/        # Admin dashboard (deprecated - moved to home)
│   ├── lcp/              # LCP infrastructure management
│   ├── routers/          # Router inventory
│   ├── subscriptions/    # Subscription plans
│   ├── customer_installations/  # Customer installations
│   ├── customer_subscriptions/  # Customer subscriptions
│   ├── users/            # User authentication & management
│   └── web/              # Public pages & home dashboard
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

### LCP Infrastructure Models (NEW)

#### LCP (Local Convergence Point)
- Name and unique code
- Physical location
- Linked to Barangay
- Active/inactive status
- Contains multiple splitters

#### Splitter
- Belongs to LCP
- Unique code within LCP
- Type (1:4, 1:8, 1:16, 1:32, 1:64)
- Location within LCP
- Port capacity calculated from type
- Tracks used/available ports

#### NAP (Network Access Point)
- Belongs to Splitter
- Connected to specific splitter port
- Multiple NAPs can share same port (for cascading)
- Unique code within splitter
- Physical location
- Customer port capacity
- Validates port within splitter range

### Customer Service Models

#### CustomerInstallation
- Links customer to installation details
- Installation date and technician
- Status tracking
- Equipment details

#### CustomerSubscription
- Links customer to subscription plan
- Billing cycle (Weekly/Quincenal/Monthly)
- Payment tracking
- Start/end dates

## Features Implemented

### Phase 1-2 Complete ✅
- Customer Management (CRUD, search, status tracking)
- Barangay Management 
- Router Inventory
- Subscription Plans
- User Management (Cashier/Technician roles)
- Unified Dashboard (statistics, charts, widgets)

### Phase 3 Complete ✅
- LCP Infrastructure Management
  - Hierarchical view: LCP → Splitter → NAP
  - Port tracking and availability
  - Visual capacity management
  - Full CRUD operations
- Customer Installations
- Customer Subscriptions

## Navigation Structure

**Application**
- Dashboard (unified home page with statistics)

**Admin Setup**
- Customers
- Barangays
- Routers
- Subscription Plans
- LCP (fiber infrastructure management)

**User Management**
- User Lists
- User Roles (placeholder)

**Installation**
- Setup Customer (/installations/)
- Tickets (placeholder)

**Subscription**
- Active Subscriptions
- Payment (placeholder)

## Recent Changes

### Dashboard Consolidation
- Removed separate /dashboard/ route
- Merged Project Dashboard content into home page
- Superusers see full statistics dashboard
- Regular users see welcome page
- Updated all 'dashboard:dashboard' references to 'web:home'

### Navigation Updates
- "My Account" moved to top-right dropdown
- Shows user's full name (or email if no name)
- Removed Flowbite demo and dependencies
- Reorganized menu sections for better grouping

### LCP Infrastructure Implementation
- Complete fiber network hierarchy management
- Custom views replacing Django admin
- Search and filter capabilities
- Visual port usage tracking
- Flexible port assignment (multiple NAPs per port allowed)

## Business Rules

### LCP Infrastructure
- LCP contains multiple splitters
- Splitters have different capacities (1:4 to 1:64)
- NAPs connect to splitter ports
- Multiple NAPs can share a port (cascading)
- Port numbers must be within splitter capacity
- NAP codes unique within splitter

### Customers
- Unique email required
- Must belong to a barangay
- Can be soft deleted
- Status workflow: Active → Suspended → Terminated

### Users
- Superusers excluded from management interface
- Only superuser can access admin functions
- Email used as username
- User types: Cashier, Technician

## API Endpoints
- Currently using Django views with HTMX
- REST API planned for mobile app
- HTMX endpoints for dynamic UI

## Security
- Django authentication
- Superuser required for admin functions
- CSRF protection configured for HTMX
- Session-based auth for web

## Sample Data Generators
```bash
make manage ARGS="generate_customers --count=50"
make manage ARGS="generate_routers --count=20"
make manage ARGS="generate_subscription_plans"
make manage ARGS="generate_sample_users"
make manage ARGS="generate_lcp_data"
```

## Important Technical Notes

### HTMX Configuration
- CSRF token configured globally in base template
- Use simple `htmx.ajax('METHOD', 'url')` syntax
- No manual CSRF headers needed

### User Authentication
- Top navigation shows user dropdown
- Displays full name or email
- Profile, password change, logout options

### LCP Management
- Accessible via /lcp/ (not Django admin)
- Full CRUD for LCP, Splitter, NAP
- Validates port assignments
- Tracks fiber network topology

## Known Issues/TODOs
- User Roles management UI not implemented
- Tickets system not implemented
- Payment tracking not implemented
- No SMS integration
- No customer portal
- No mobile app yet

## Next Development Phases

### Phase 4: Billing System
- Invoice generation
- Payment recording
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

## Development Tips
- Always use absolute paths in Desktop Commander
- Chunk large files into 30-line segments
- Check for existing similar code before implementing
- Run `make manage ARGS="check"` after changes
- Use sample data generators for testing
