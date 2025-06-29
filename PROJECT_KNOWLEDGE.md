# ISP Billing System - Project Knowledge Base (Updated June 29, 2025)
====================================================================

## Project Overview
A comprehensive billing management system for a small-scale Internet Service Provider (ISP) operating in Cagayan de Oro, Northern Mindanao, Philippines. Built for localized fiber network coverage with manual infrastructure management and personalized customer service.

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

## Project Structure
```
/Users/aldesabido/pers/isp_billing_system/
├── apps/
│   ├── barangays/               # Barangay master list
│   ├── customers/               # Customer management (with geo-location)
│   ├── dashboard/               # Dashboard views and widgets
│   ├── lcp/                     # LCP, Splitter, NAP infrastructure (with geo-location)
│   ├── routers/                 # Router inventory (with MAC address tracking)
│   ├── subscriptions/           # Subscription plans catalog
│   ├── customer_installations/  # Customer installations (with geo-location & NAP ports)
│   ├── customer_subscriptions/  # Customer subscription payments (prepaid)
│   ├── network/                 # Network visualization and maps
│   ├── tickets/                 # Support ticket system
│   ├── reports/                 # Comprehensive reporting system
│   ├── roles/                   # RBAC role management system
│   ├── users/                   # User authentication & management
│   └── web/                     # Public pages & home dashboard
├── templates/
│   ├── components/              # Reusable components (includes map_widget.html)
│   ├── network/                 # Network visualization templates
│   └── roles/                   # Role management templates
├── assets/                      # Frontend assets (Vite)
├── requirements/                # Python dependencies
└── TODO.md                      # Project TODO list
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

# Dependencies
make pip-compile              # Update requirements files
```

## Database Schema

### Core Models with Geo-Location

#### Customer (Enhanced with GeoLocatedModel)
- Personal info: first_name, last_name, email, phone_primary
- Address: street_address, barangay (ForeignKey)
- Geo-location: latitude, longitude, location_accuracy, location_notes
- Status: ACTIVE, INACTIVE, SUSPENDED, TERMINATED
- Timestamps: created_at, updated_at

#### Barangay
- Master list of 80 barangays in CDO
- Fields: name, is_active
- Used for customer addresses and infrastructure locations

#### Router (Updated)
- Inventory tracking for customer routers
- Fields: brand, model, serial_number, **mac_address** (required, unique, validated)
- MAC address format: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
- No geo-location (stored at customer premises)

#### SubscriptionPlan
- Catalog of available internet plans
- Fields: name, description, speed (Mbps), price (₱), day_count (default 30)
- Status: is_active

### LCP Infrastructure Models (Enhanced with GeoLocatedModel)

#### LCP (Local Convergence Point)
- Main fiber distribution hub
- Fields: name, code, location, barangay, is_active, notes
- Geo-location fields included
- coverage_radius_meters - Service area visualization
- Properties: splitter_count, nap_count

#### Splitter
- Optical splitter dividing fiber signals
- Fields: lcp (ForeignKey), code, type (1:4, 1:8, 1:16, 1:32, 1:64)
- location (specific location within LCP)
- Geo-location fields included
- Properties: port_capacity, used_ports, available_ports

#### NAP (Network Access Point)
- Customer connection points
- Fields: splitter (ForeignKey), splitter_port, code, name, location
- port_capacity (4-16 typically), is_active, notes
- max_distance_meters - Maximum customer distance
- Geo-location fields included
- Properties: used_ports, available_ports, connection_path

### Customer Service Models

#### CustomerInstallation
- One-to-one with Customer
- Fields: customer, router, nap, nap_port, installation_date
- installation_technician, installation_notes
- Status: ACTIVE, INACTIVE, SUSPENDED, TERMINATED
- Geo-location fields for service location
- Unique constraint: (nap, nap_port) - prevents double booking
- Properties:
  - current_subscription - Active subscription if any
  - has_active_subscription - Boolean check
  - network_path - Complete fiber path

#### CustomerSubscription (Prepaid Model)
- Prepaid subscription payments
- Fields:
  - customer_installation (ForeignKey)
  - subscription_plan (ForeignKey)
  - subscription_type: one_month, fifteen_days, custom
  - amount - Payment amount
  - start_date, end_date (DateTimeField for precision)
  - days_added - Calculated service days
  - status: ACTIVE, EXPIRED, CANCELLED
  - created_by - Cashier/staff who processed
- Auto-calculations:
  - 1 Month: Full plan price = 30 days
  - 15 Days: Half price = 15 days
  - Custom: (amount/price) × 30 = proportional days
- Features:
  - Subscription stacking/queueing
  - Auto-expiry when end_date passes
  - Installation status sync (INACTIVE when no active sub)

### Support System Models

#### Ticket
- Customer support ticket tracking
- Fields:
  - ticket_number (auto-generated, unique)
  - customer, customer_installation (ForeignKeys)
  - title, description
  - category: connectivity, billing, installation, equipment, other
  - priority: low, medium, high, urgent
  - status: new, in_progress, resolved, closed, cancelled
  - source: phone, email, walk_in, system
  - assigned_to (staff user)
  - reported_by (user who created)
  - resolution_notes
  - resolved_at, response_time
- Auto-generated ticket numbers: TK-YYYYMMDD-XXXX
- Properties: is_overdue, priority_color, status_color

#### TicketComment
- Comments on tickets
- Fields: ticket, user, comment, created_at
- Allows tracking of ticket communication

### RBAC Models (Role-Based Access Control)

#### Role
- Custom role model extending Django's Group
- Fields: name, code, description, is_active, is_system
- Properties: permissions (through Group), user_count
- System roles cannot be deleted

#### PermissionCategory
- Groups permissions by functional area
- Fields: name, code, description, icon, order
- 11 categories total (after Network merged into Reports)

#### PermissionCategoryMapping
- Maps Django permissions to categories with user-friendly names
- Fields: category, permission, display_name, description, order
- Total: 70 mapped permissions (simplified from 107)

## Features Implemented

### Phase 1-3: Infrastructure & Customer Management ✅
- Customer management with full CRUD
- Barangay master list
- Router inventory tracking (with MAC addresses)
- Subscription plan catalog
- LCP infrastructure hierarchy
- Customer installations with NAP ports

### Geo-Location System ✅
1. **Reusable Map Widget** (`templates/components/map_widget.html`)
   - Interactive Leaflet.js map
   - Click to set location
   - Address search via Nominatim
   - "Use My Location" GPS button
   - Manual coordinate input
   - Two-way binding with form fields

2. **Network Visualization Map** (`/network/map/`)
   - All infrastructure on one map
   - Layer controls for each element type
   - Different icons for LCP, Splitter, NAP, Customer
   - Coverage radius visualization
   - Click for details popup

3. **Network Hierarchy View** (`/network/hierarchy/`)
   - Visual tree structure
   - Port capacity indicators
   - Connection paths

### NAP Port Management ✅
- Visual port grid on installation form
- Real-time availability checking
- Port occupation tracking
- Toggle-style selection (outline = available, solid = selected)
- API: `/installations/api/nap/<nap_id>/ports/`
- Prevents double-booking

### Hierarchical Network Selection ✅
- Installation form uses cascading dropdowns:
  - LCP → Splitter → NAP → Port
- Auto-resets downstream selections when parent changes
- Shows capacity at each level
- API endpoints:
  - `/lcp/api/lcps/`
  - `/lcp/api/lcp/<id>/splitters/`
  - `/lcp/api/splitter/<id>/naps/`
  - `/lcp/api/nap/<id>/hierarchy/`

### Subscription System ✅
1. **Prepaid Model**
   - Pay upfront for service time
   - DateTime precision (to the minute)
   - Three payment options with auto-calculation

2. **Real-time Preview**
   - Shows exact days, hours, minutes
   - Updates as amount changes
   - End date calculation

3. **Subscription Stacking**
   - Queue multiple subscriptions
   - Auto-continues from previous end date
   - Supports plan changes/upgrades

4. **Status Management**
   - Auto-expires subscriptions
   - Updates installation to INACTIVE
   - Reactivates on new subscription

### Acknowledgment Receipt System ✅
- Generate PDF receipts for payments
- Format: AR-YYYY-MMDD-XXXX
- Manual trigger via "Print Receipt" button
- Uses WeasyPrint for PDF generation
- Available in:
  - Subscription list
  - Payment history
  - Active subscriptions
- Shows payment details and print timestamp

### Support Ticket System ✅
1. **Ticket Management**
   - Create, update, view tickets
   - Auto-generated ticket numbers
   - Customer search with installations
   - Priority shown below ticket number in list

2. **Workflow-Based Permissions**
   - Create tickets
   - Assign to technicians
   - Update status/priority
   - Add comments
   - Track response times

3. **Filtering & Search**
   - Filter by status, priority, assigned tech
   - Search by customer or ticket details
   - Statistics dashboard

### RBAC Permission System ✅ (NEW - December 2024)
1. **Simplified Permission Structure**
   - Reduced from 107 to 70 permissions
   - 11 permission categories (Network merged into Reports)
   - Workflow-based permissions for tickets
   - Consistent 4-5 permissions per module

2. **Permission Categories & Counts**
   ```
   Dashboard: 5 permissions
   Customer Management: 6 permissions
   Barangay Management: 4 permissions (CRUD only)
   Router Management: 4 permissions (CRUD only)
   Subscription Plans: 4 permissions (CRUD only)
   LCP Infrastructure: 5 permissions (unified management)
   Installations: 5 permissions (core operations)
   Customer Subscriptions: 5 permissions (streamlined)
   Support Tickets: 7 permissions (workflow-based)
   Reports & Analytics: 16 permissions (includes network viz)
   User Management: 9 permissions (users + roles + audit)
   ```

3. **Role Management Features**
   - Create custom roles with specific permissions
   - Visual permission assignment interface
   - System roles protection
   - User-friendly permission names and descriptions
   - Category-based organization

4. **Management Commands**
   - `setup_permission_categories` - Initialize categories
   - `map_permissions_to_categories` - Map permissions
   - `create_default_roles` - Create default roles
   - `assign_user_roles` - Assign roles to users

### Reporting System ✅
1. **Operational Reports**
   - Daily Collection Report
   - Subscription Expiry Report

2. **Business Intelligence Reports**
   - Monthly Revenue Report
   - Ticket Analysis Report
   - Technician Performance Report
   - Customer Acquisition Report
   - Payment Behavior Report

3. **Strategic Planning**
   - Area Performance Dashboard
   - Financial Dashboard
   - Network Visualization (moved to Reports category)

## Business Rules

### Geo-Location
- Customers: Billing/contact address location
- Installations: Actual service connection location
- Infrastructure: Physical equipment locations
- All support manual entry or GPS positioning

### Network Hierarchy
```
ISP Core Network
    └── LCP (serves 100-500 customers)
         └── Splitter (1:8, 1:16, 1:32 ports)
              └── NAP (4-16 customer ports)
                   └── Customer Installation (1 port)
                        └── Router (at customer premises)
```

### Subscription Rules
- **Prepaid only** - Pay before service
- **Flexible amounts** - Full, half, or custom payment
- **Time precision** - Tracks to the minute
- **Auto-queue** - New subs start after current
- **Status sync** - Installation INACTIVE without active sub

### Ticket Workflow
1. Someone creates the ticket
2. Someone assigns a technician
3. Assigned technician updates status
4. Anyone can add comments
- Auto-generated ticket numbers
- Priority levels affect visual indicators
- Response time tracking

### RBAC Rules
- System roles cannot be deleted
- Permissions grouped by functional area
- Role changes take effect immediately
- Users can have multiple roles (permissions aggregate)
- Superusers bypass all permission checks

## API Endpoints

### Customer APIs
- `/customers/api/coordinates/` - Get customer coordinates

### Installation APIs
- `/installations/api/nap/<nap_id>/ports/` - NAP port availability

### LCP Infrastructure APIs
- `/lcp/api/lcps/` - List all active LCPs
- `/lcp/api/lcp/<lcp_id>/splitters/` - Get splitters for LCP
- `/lcp/api/splitter/<splitter_id>/naps/` - Get NAPs for splitter
- `/lcp/api/nap/<nap_id>/hierarchy/` - Get full hierarchy for NAP

### Subscription APIs
- `/customer-subscriptions/api/latest-subscription/` - Current subscription info
- `/customer-subscriptions/api/calculate-preview/` - Payment preview calculation
- `/customer-subscriptions/api/plan-price/` - Get plan pricing

### Ticket APIs
- `/tickets/ajax/search-customers/` - Search customers for tickets
- `/tickets/ajax/customer-installations/` - Get customer installations

### Network APIs
- `/network/map/data/` - All network elements for map

## Sample Data Generators
```bash
# Customers
make manage ARGS="generate_customers --count=50"

# Infrastructure
make manage ARGS="generate_lcp_data"

# Installations
make manage ARGS="generate_installations --count=20"

# Subscriptions
make manage ARGS="generate_subscriptions --count=20"

# Other
make manage ARGS="generate_routers --count=20"
make manage ARGS="generate_subscription_plans"
make manage ARGS="generate_sample_users"
```

## System Status

### ✅ Completed (96%)
- **Infrastructure Management**: 100% - Full hierarchy with geo-location
- **Customer Management**: 100% - Complete with geo-location
- **Installation Management**: 100% - NAP ports, network paths, hierarchical selection
- **Network Visualization**: 100% - Maps and hierarchy views
- **Subscription System**: 100% - Prepaid model with calculations
- **Receipt Generation**: 100% - Acknowledgment receipts
- **Ticket System**: 100% - Full support ticket management
- **Reporting System**: 95% - Comprehensive business reports
- **Router Management**: 100% - Includes MAC address tracking
- **RBAC System**: 100% - Complete role-based access control

### ❌ Not Implemented (4%)
- **Audit Logs**: Permission exists but no UI implementation
- **Customer Portal**: No self-service interface
- **SMS Integration**: No automated notifications
- **Mobile App**: Not developed
- **Email Notifications**: Manual only
- **Bandwidth Monitoring**: Not implemented

## Technical Architecture

### Frontend Patterns
- **HTMX**: Server interactions, partial updates
- **Alpine.js**: Client-side interactivity, data binding
- **Tailwind + DaisyUI**: Consistent styling
- **Leaflet.js**: Interactive maps
- **Widget Tweaks**: Django form styling

### Backend Patterns
- **Django ORM**: All database operations
- **Class-based models**: BaseModel for timestamps
- **Function-based views**: Simpler than CBVs
- **Celery**: Background tasks (configured but lightly used)
- **WeasyPrint**: PDF generation for receipts
- **Django Groups**: Role implementation via Role model

### JavaScript Components
- **mapWidget**: Reusable geo-location picker
- **Port selection grid**: Visual NAP port assignment
- **Subscription preview**: Real-time calculations
- **Hierarchical dropdowns**: LCP → Splitter → NAP selection

## Recent Updates (June 29, 2025)

1. **RBAC Permission Simplification**
   - Reduced from 107 to 70 permissions
   - Simplified Barangay Management to 4 CRUD permissions
   - Simplified Router Management to 4 CRUD permissions
   - Simplified Subscription Plans to 4 CRUD permissions
   - Restructured LCP Infrastructure to 5 unified permissions
   - Streamlined Installations to 5 core permissions
   - Optimized Customer Subscriptions to 5 permissions
   - Redesigned Support Tickets to 7 workflow-based permissions
   - Moved Network Management into Reports & Analytics
   - Kept User Management at 9 permissions for security

2. **Permission Organization**
   - 11 categories (down from 12)
   - Consistent naming patterns
   - Workflow-aligned permissions for tickets
   - User-friendly display names and descriptions

3. **TODO Items Documented**
   - Audit Log UI implementation needed
   - Reports simplification pending decision
   - Created TODO.md for tracking

## Known Issues/TODOs

### High Priority
1. **Audit Log UI**: Create user-facing audit log viewer
2. **Email notifications**: Automate customer communications
3. **Backup system**: Automated database backups

### Medium Priority
1. **Reports Simplification**: Reduce from 16 to 11 permissions
2. **Bulk Operations**: Import/export customers
3. **Advanced search**: Global search across entities
4. **Performance optimization**: Query optimization for large datasets

### Low Priority
1. **SMS Notifications**: Payment reminders
2. **Customer Portal**: Self-service interface
3. **Mobile App**: Field technician app

## Configuration Notes

### Environment Variables
- Database: PostgreSQL connection
- Redis: Cache and Celery broker
- Timezone: Asia/Manila (UTC+8)
- Debug: Set to False for production

### Security Considerations
- CSRF protection enabled
- Login required for all app views
- Permission-based access control via RBAC
- Superuser bypass for all permissions
- System roles protected from deletion

### Third-party Services
- OpenStreetMap: Map tiles
- Nominatim: Geocoding service
- No external payment gateways (prepaid only)

## Development Guidelines
1. Use absolute paths in Desktop Commander
2. Chunk large files (30 lines) for better performance
3. Always validate user input server-side
4. Test coordinate features with map widget
5. Follow Django best practices
6. Use HTMX for dynamic updates
7. Maintain backward compatibility
8. Check user permissions before sensitive operations

## Next Steps for Full Production

The system is approximately 96% ready for commercial use. Recommended steps:

1. **Implement Audit Logs UI** for compliance and tracking
2. **Configure email settings** for notifications
3. **Set up regular backups**
4. **Performance testing** with expected load
5. **Security audit** before public deployment
6. **User training** on new RBAC system
7. **Create role templates** for common positions

With the core billing, infrastructure management, RBAC system, and support systems complete, the ISP can begin operations while incrementally adding convenience features like audit logs, customer portals, and automated notifications.
