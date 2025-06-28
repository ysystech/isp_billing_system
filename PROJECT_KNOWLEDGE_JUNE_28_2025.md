ISP Billing System - Project Knowledge Base (Updated June 28, 2025)
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

## Project Structure
```
/Users/aldesabido/pers/isp_billing_system/
├── apps/
│   ├── barangays/               # Barangay master list
│   ├── customers/               # Customer management (with geo-location)
│   ├── dashboard/               # Dashboard views and widgets
│   ├── lcp/                     # LCP, Splitter, NAP infrastructure (with geo-location)
│   ├── routers/                 # Router inventory
│   ├── subscriptions/           # Subscription plans catalog
│   ├── customer_installations/  # Customer installations (with geo-location & NAP ports)
│   ├── customer_subscriptions/  # Customer subscription payments (prepaid)
│   ├── network/                 # Network visualization and maps
│   ├── users/                   # User authentication & management
│   └── web/                     # Public pages & home dashboard
├── templates/
│   ├── components/              # Reusable components (includes map_widget.html)
│   └── network/                 # Network visualization templates
├── assets/                      # Frontend assets (Vite)
└── requirements/                # Python dependencies
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

#### Router
- Inventory tracking for customer routers
- Fields: serial_number, model, status, notes
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

#### Splitter
- Optical splitter dividing fiber signals
- Fields: lcp (ForeignKey), code, type (1:4, 1:8, 1:16, 1:32, 1:64)
- Geo-location fields included
- Properties: port_capacity, used_ports, available_ports

#### NAP (Network Access Point)
- Customer connection points
- Fields: splitter (ForeignKey), splitter_port, code, name, location
- port_capacity (4-16 typically), is_active, notes
- max_distance_meters - Maximum customer distance
- Geo-location fields included

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

#### CustomerSubscription (NEW - Prepaid Model)
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

## Features Implemented

### Phase 1-3: Infrastructure & Customer Management ✅
- Customer management with full CRUD
- Barangay master list
- Router inventory tracking
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
- API: `/installations/api/nap/<nap_id>/ports/`
- Prevents double-booking

### Subscription System ✅ (NEW)
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

## API Endpoints

### Customer APIs
- `/customers/api/coordinates/` - Get customer coordinates

### Installation APIs
- `/installations/api/nap/<nap_id>/ports/` - NAP port availability

### Subscription APIs
- `/customer-subscriptions/api/latest-subscription/` - Current subscription info
- `/customer-subscriptions/api/calculate-preview/` - Payment preview calculation
- `/customer-subscriptions/api/plan-price/` - Get plan pricing

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

### ✅ Completed (85%)
- **Infrastructure Management**: 100% - Full hierarchy with geo-location
- **Customer Management**: 100% - Complete with geo-location
- **Installation Management**: 100% - NAP ports, network paths
- **Network Visualization**: 100% - Maps and hierarchy views
- **Subscription System**: 100% - Prepaid model with calculations
- **Basic Reporting**: 80% - Dashboard statistics

### ❌ Not Implemented (15%)
- **Invoice Generation**: No PDF invoices yet
- **Financial Reports**: No detailed accounting reports
- **SMS Integration**: No automated notifications
- **Customer Portal**: No self-service interface
- **Mobile App**: Not developed
- **Advanced Analytics**: Limited reporting

## Technical Architecture

### Frontend Patterns
- **HTMX**: Server interactions, partial updates
- **Alpine.js**: Client-side interactivity, data binding
- **Tailwind + DaisyUI**: Consistent styling
- **Leaflet.js**: Interactive maps

### Backend Patterns
- **Django ORM**: All database operations
- **Class-based models**: BaseModel for timestamps
- **Function-based views**: Simpler than CBVs
- **Celery**: Background tasks (configured but not heavily used)

### JavaScript Components
- **mapWidget**: Reusable geo-location picker
- **Port selection grid**: Visual NAP port assignment
- **Subscription preview**: Real-time calculations

## Recent Updates (June 28, 2025)

1. **Subscription Module Overhaul**
   - Removed old payment tracking
   - Implemented prepaid subscription system
   - Added real-time preview calculations
   - DateTime precision for exact timing

2. **Installation Status Management**
   - Added INACTIVE status
   - Auto-sync with subscription status
   - Maintains ACTIVE only with valid subscription

3. **Enhanced Map Integration**
   - Fixed coordinate auto-update issues
   - Improved two-way data binding
   - Better event handling

## Known Issues/TODOs

### High Priority
1. **Invoice System**: Need PDF invoice generation
2. **Payment Receipts**: Official receipts for payments
3. **Overdue Management**: Track and act on expired accounts

### Medium Priority
1. **Bulk Operations**: Import/export customers
2. **Service Tickets**: Customer complaint tracking
3. **Bandwidth Monitoring**: Usage tracking

### Low Priority
1. **SMS Notifications**: Payment reminders
2. **Email Integration**: Automated emails
3. **Mobile App**: Field technician app

## Development Guidelines
1. Use absolute paths in Desktop Commander
2. Chunk large files (30 lines) for better performance
3. Always validate user input server-side
4. Test coordinate features with map widget
5. Follow Django best practices
6. Use HTMX for dynamic updates

## Next Steps for Commercial Operation

The system is approximately 85% ready for commercial use. Critical missing features:

1. **Invoice Generation** - Must have for business operations
2. **Official Receipts** - Legal requirement
3. **Collection Reports** - Track business health
4. **Automated Reminders** - Reduce manual follow-ups

With the subscription system now complete, the main gap is formal billing documentation (invoices/receipts) and financial reporting. The infrastructure and customer management are production-ready.
