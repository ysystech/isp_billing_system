ISP Billing System - Project Knowledge Base (Updated December 2024)
====================================================================

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
- **Maps**: Leaflet.js with OpenStreetMap

## Project Structure
```
/Users/aldesabido/pers/isp_billing_system/
├── apps/
│   ├── barangays/               # Barangay master list
│   ├── customers/               # Customer management (with geo-location)
│   ├── dashboard/               # DEPRECATED - merged into home
│   ├── lcp/                     # LCP, Splitter, NAP infrastructure (with geo-location)
│   ├── routers/                 # Router inventory
│   ├── subscriptions/           # Subscription plans
│   ├── customer_installations/  # Customer installations (with geo-location & NAP ports)
│   ├── customer_subscriptions/  # Customer subscriptions
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

## Database Schema Updates

### Core Models with Geo-Location

#### Customer (Enhanced with GeoLocatedModel)
- All original fields PLUS:
- `latitude`, `longitude` - Customer's primary location
- `location_accuracy` - How coordinates were obtained
- `location_notes` - Location landmarks/notes
- REMOVED: `installation_date`, `installation_technician`, `installation_notes` (moved to CustomerInstallation)

#### Barangay
- Master list of service areas (80 barangays in CDO)
- No changes from original

#### Router
- Basic inventory tracking
- No changes from original

#### SubscriptionPlan
- Name, Description, Speed, Price
- No changes from original

### LCP Infrastructure Models (Enhanced with GeoLocatedModel)

#### LCP (Local Convergence Point)
- All original fields PLUS:
- `latitude`, `longitude`, `location_accuracy`, `location_notes`
- `coverage_radius_meters` - Service area radius

#### Splitter
- All original fields PLUS:
- `latitude`, `longitude`, `location_accuracy`, `location_notes`

#### NAP (Network Access Point)
- All original fields PLUS:
- `latitude`, `longitude`, `location_accuracy`, `location_notes`
- `max_distance_meters` - Maximum customer distance

### Customer Service Models (Enhanced)

#### CustomerInstallation
- All original fields PLUS:
- Inherits from `GeoLocatedModel` - Has its own coordinates
- `nap` - ForeignKey to NAP where customer connects
- `nap_port` - Integer (1 to NAP.port_capacity)
- Unique constraint on (nap, nap_port) - prevents double booking
- Properties:
  - `nap_connection_display` - Shows "NAP-001 - Port 5"
  - `network_path` - Full path: LCP → Splitter → NAP → Port

#### CustomerSubscription
- No changes from original

## Features Implemented

### Phase 1-3 Complete ✅
- Customer Management with geo-location
- LCP Infrastructure Management with geo-location
- Customer Installations with NAP port assignment
- Customer Subscriptions

### NEW: Geo-Location System ✅
1. **Reusable Map Widget** (`templates/components/map_widget.html`)
   - Interactive Leaflet.js map
   - Click to set location
   - Address search via Nominatim
   - "Use My Location" GPS button
   - Manual coordinate input
   - Works on Customer, LCP, Splitter, NAP, and Installation forms

2. **Network Visualization Map** (`/network/map/`)
   - Shows all infrastructure and customers on one map
   - Layer controls for each type
   - Different icons for LCP, Splitter, NAP, Customer, Installation
   - Coverage radius visualization
   - Click markers for details

3. **Network Hierarchy Visualization** (`/network/hierarchy/`)
   - Visual representation of LCP → Splitter → NAP → Ports
   - Shows port capacity and usage
   - Educational diagrams

### NEW: NAP Port Management ✅
1. **Port Assignment**
   - Each installation connects to specific NAP port
   - Visual port grid showing availability
   - Real-time validation
   - Prevents double-booking

2. **Port Availability API**
   - `/installations/api/nap/<nap_id>/ports/`
   - Returns port status and occupancy

3. **Network Path Tracking**
   - Complete path from customer to LCP
   - Useful for troubleshooting

## Business Rules

### Geo-Location
- Customers have primary location (billing/contact)
- Installations have service location (actual connection point)
- Installation form pre-fills customer coordinates
- All infrastructure elements can have coordinates

### NAP Port Assignment
- One port = one customer installation
- Ports numbered 1 to NAP.port_capacity
- Cannot assign same port twice
- Port assignment validated on save

### Network Hierarchy
```
LCP (1)
 └─> Splitters (Multiple)
      └─> NAPs (Multiple per splitter port)
           └─> Customer Ports (4-16 per NAP)
                └─> Customer Installations (1 per port)
```

## API Endpoints

### Customer APIs
- `/customers/api/coordinates/` - Get customer coordinates (POST)

### Network APIs
- `/network/map/data/` - Get all network elements for map
- `/installations/api/nap/<nap_id>/ports/` - Get NAP port availability

## Recent Architecture Decisions

### 1. Geo-Location on Both Customer and Installation
- Customer location = primary/billing address
- Installation location = actual service location
- Handles multiple properties per customer
- Installation inherits customer location as default

### 2. Installation Tracking Removed from Customer
- Moved installation_date, technician, notes to CustomerInstallation
- Cleaner separation of concerns
- Supports multiple installations per customer

### 3. Dashboard Consolidation
- Removed separate /dashboard/ app
- Merged into home page
- Single entry point for all users

## JavaScript Components

### mapWidget (Alpine.js)
- Reusable map component
- Handles coordinate selection
- Address search integration
- GPS location support

### Installation Form Enhancement
- Dynamic NAP port selection
- Real-time availability checking
- Visual port grid
- Customer coordinate inheritance

## Important Technical Notes

### Map Integration
- Uses Leaflet.js (free, no API key)
- OpenStreetMap tiles
- Leaflet Search plugin for geocoding
- All map resources loaded via CDN in base template

### Coordinate System
- Decimal degrees (7 decimal places)
- Centered on CDO: 8.4542, 124.6319
- Simple distance calculation for <10km

### HTMX + Alpine.js Pattern
- HTMX for server interactions
- Alpine.js for client-side interactivity
- Map widget uses Alpine.js data binding

## Sample Data Generators
```bash
make manage ARGS="generate_customers --count=50"
make manage ARGS="generate_routers --count=20"
make manage ARGS="generate_subscription_plans"
make manage ARGS="generate_sample_users"
make manage ARGS="generate_lcp_data"
```

## Utility Commands
```bash
# Hard delete all subscriptions, installations, and plans
make manage ARGS="hard_delete_records --confirm"
```

## Known Issues/TODOs
- User Roles management UI not implemented
- Tickets system not implemented
- Payment/Billing system not implemented ← CRITICAL
- No SMS integration
- No customer portal
- No mobile app yet

## Next Development Priority

### CRITICAL: Phase 4 - Billing System
The system cannot operate commercially without billing functionality:

1. **Invoice Generation**
   - Monthly/weekly/quincenal billing cycles
   - PDF invoice generation
   - Bulk invoice creation

2. **Payment Recording**
   - Record payments against invoices
   - Multiple payment methods
   - Partial payments

3. **Financial Reporting**
   - Outstanding balances
   - Collection efficiency
   - Revenue reports

4. **Collection Management**
   - Overdue accounts
   - Payment reminders
   - Service suspension automation

## Development Tips
- Always use absolute paths in Desktop Commander
- Chunk large files into 30-line segments when editing
- Check for existing similar code before implementing
- Run `make manage ARGS="check"` after model changes
- Map widget is reusable - use it for any geo-located model
- Test coordinate features with "Use My Location" button

## Recent Accomplishments
1. ✅ Implemented comprehensive geo-location system
2. ✅ Created reusable map widget component  
3. ✅ Built network visualization map
4. ✅ Added NAP port management to installations
5. ✅ Created network hierarchy visualization
6. ✅ Implemented proper fiber network tracking (LCP → Customer)

## System Readiness
- **Infrastructure Management**: 100% Complete
- **Customer Management**: 100% Complete
- **Network Visualization**: 100% Complete
- **Installation Tracking**: 100% Complete
- **Billing System**: 0% - NEEDS IMPLEMENTATION
- **Overall**: ~70% ready for commercial operation

The system now properly tracks the complete fiber network from LCP to customer premises with visual maps and port management. The critical missing piece is the billing system, without which the ISP cannot collect payments from customers.
