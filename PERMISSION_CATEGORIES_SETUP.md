# Permission Categories Setup Issue

## Date: June 30, 2025

## Issue
When trying to manage role permissions at `/roles/{id}/permissions/`, the page shows:
- "Debug: permission_data has 0 categories"
- "No permission categories found. The permission_data variable is empty."

## Root Cause
The permission categories and mappings have not been populated in the database. These are system-wide configurations that need to be set up using management commands.

## Solution
Run the following management commands to populate permission categories and mappings:

```bash
# Step 1: Create permission categories
make manage ARGS="setup_permission_categories"

# Step 2: Map permissions to categories
make manage ARGS="map_permissions_to_categories"
```

## What These Commands Do

### 1. setup_permission_categories
Creates the following permission categories:
- Dashboard (dashboard)
- Customer Management (customers)
- Barangay Management (barangays)
- Router Management (routers)
- Subscription Plans (plans)
- LCP Infrastructure (lcp)
- Network Management (network)
- Installations (installations)
- Customer Subscriptions (subscriptions)
- Support Tickets (tickets)
- User Management (users)
- Reports & Analytics (reports)

### 2. map_permissions_to_categories
- Maps Django permissions to appropriate categories
- Provides user-friendly display names
- Adds descriptions for each permission
- Organizes permissions for better UI/UX

## Important Notes

### System-Wide Configuration
- PermissionCategory and PermissionCategoryMapping are NOT tenant-specific
- They are shared across all tenants
- This is intentional as permission structure is consistent

### One-Time Setup
- These commands only need to be run once per deployment
- They update existing records if run multiple times
- Safe to run in production

## Verification
After running the commands:
1. Go to `/roles/{id}/permissions/`
2. You should see permission categories with organized permissions
3. Each category will have relevant permissions grouped together

## Alternative: Admin Panel
You can also manage these through Django admin:
1. Go to `/admin/`
2. Navigate to Roles > Permission Categories
3. Manually create categories and mappings

## Future Considerations
Consider adding these commands to:
- Deployment scripts
- Initial setup documentation
- Docker entrypoint scripts
- Migration process
