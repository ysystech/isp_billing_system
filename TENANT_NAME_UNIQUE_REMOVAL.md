# Tenant Name Unique Constraint Removal

## Date: June 30, 2025

## Issue
- Users were getting `IntegrityError` when trying to register with a company name that already exists
- Error: "duplicate key value violates unique constraint 'tenants_name_key'"

## Solution
- Removed the `unique=True` constraint from the `Tenant.name` field
- Created and applied migration `0003_remove_tenant_name_unique`

## Rationale
In a multi-tenant SaaS system, it's common for different companies to have the same or similar names. For example:
- Multiple companies named "ABC Company" in different regions
- Common business names like "Tech Solutions" or "Consulting Group"
- Franchises or subsidiaries with the same name

## Impact
- Users can now register with any company name, even if it already exists
- No changes needed to the registration form or validation
- Each tenant is still uniquely identified by their ID, not their name

## Technical Details
- Model change: `name = models.CharField(max_length=100)` (removed `unique=True`)
- Migration: `apps/tenants/migrations/0003_remove_tenant_name_unique.py`
- Database constraint `tenants_name_key` has been dropped

## Future Considerations
If unique identification is needed in the UI, consider:
1. Displaying tenant ID alongside name in admin interfaces
2. Adding optional fields like domain, subdomain, or slug for unique identification
3. Showing creation date or owner email to differentiate tenants with same name
