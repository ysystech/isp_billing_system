# Router Duplicate Validation Enhancement

## Date: June 30, 2025

## Problem
When creating a router with a duplicate serial number or MAC address, users were seeing:
```
IntegrityError at /routers/create/
duplicate key value violates unique constraint "routers_router_tenant_id_serial_number_64dd7066_uniq"
DETAIL:  Key (tenant_id, serial_number)=(3, 123123123) already exists.
```

This raw database error was confusing and not user-friendly.

## Solution
Implemented proper form validation to show user-friendly error messages:

### 1. Form-Level Validation
**File**: `apps/routers/forms.py`
- Added `clean_serial_number()` method to check for duplicates
- Added `clean_mac_address()` method to check for duplicates
- Shows friendly messages like "A router with serial number 'X' already exists in your inventory."

### 2. View-Level Error Handling
**Files**: `apps/routers/views.py`
- Added try-except blocks around save operations
- Catches IntegrityError and adds appropriate form errors
- Provides fallback error handling for unexpected database errors

### 3. Tenant Awareness
- Validation is tenant-scoped
- Different tenants can have routers with the same serial numbers
- Form receives tenant parameter to perform proper validation

## User Experience

### Before:
- Raw database error page
- Technical jargon about constraints
- No guidance on how to fix the issue

### After:
- Form stays on the same page
- Clear error message next to the field
- User-friendly language
- Easy to understand what went wrong

## Example Error Messages
- "A router with serial number 'SN123456' already exists in your inventory."
- "A router with MAC address '00:11:22:33:44:55' already exists in your inventory."

## Testing
Created comprehensive tests in `apps/routers/test_duplicate_validation.py`:
- ✅ Duplicate serial number validation
- ✅ Duplicate MAC address validation
- ✅ Successful creation with unique values
- ✅ Multi-tenant isolation (same serial in different tenants)

All tests pass successfully.

## Technical Details
1. **Form Validation**: Runs before save, prevents database errors
2. **Database Constraints**: Still enforced as a safety net
3. **Error Display**: Uses Django's form error system
4. **Multi-Tenant**: Each tenant has its own namespace for uniqueness
