# LCP Module Tenant Fix

## Date: June 30, 2025

## Issue
When creating a Splitter or NAP, getting error:
```
IntegrityError at /lcp/1/splitter/create/
null value in column "tenant_id" of relation "lcp_splitter" violates not-null constraint
```

## Root Cause
The LCP module views were not properly setting the tenant when creating Splitter and NAP objects. The views also lacked the @tenant_required decorator and proper tenant filtering.

## Solution
Updated all LCP module views to:
1. Add @tenant_required decorator
2. Set tenant when creating objects
3. Filter all queries by tenant
4. Pass tenant to forms for filtering related fields

## Changes Made

### 1. Updated Views (`apps/lcp/views.py`)
- Added `@tenant_required` decorator to all views
- Set `tenant = request.tenant` when creating LCP, Splitter, and NAP objects
- Added `.filter(tenant=request.tenant)` to all querysets
- Pass `tenant` parameter to LCPForm for filtering barangays

### 2. Updated Forms (`apps/lcp/forms.py`)
- Modified LCPForm to accept tenant parameter
- Filter barangay queryset by tenant in form initialization

## Fixed Views
- `lcp_list` - Filter LCPs by tenant
- `lcp_detail` - Ensure LCP belongs to tenant
- `lcp_create` - Set tenant when creating
- `lcp_edit` - Maintain tenant
- `lcp_delete` - Check tenant ownership
- `splitter_create` - **Fixed: Now sets tenant**
- `splitter_edit` - Filter by tenant
- `splitter_delete` - Check tenant ownership
- `nap_create` - **Fixed: Now sets tenant**
- `nap_edit` - Filter by tenant
- `nap_delete` - Check tenant ownership
- All API views - Filter by tenant

## Key Changes in Create Views

### Splitter Create
```python
splitter = form.save(commit=False)
splitter.lcp = lcp
splitter.tenant = request.tenant  # Added this line
splitter.save()
```

### NAP Create
```python
nap = form.save(commit=False)
nap.splitter = splitter
nap.tenant = request.tenant  # Added this line
nap.save()
```

## Testing
After these changes:
1. Creating a Splitter now works without IntegrityError
2. Creating a NAP now works without IntegrityError
3. All LCP infrastructure is properly isolated by tenant
4. Barangay dropdown only shows barangays from current tenant

## Tenant Isolation
The LCP module now properly implements multi-tenant isolation:
- Each tenant can only see their own LCPs, Splitters, and NAPs
- Creating new infrastructure automatically assigns to current tenant
- Cross-tenant access returns 404 errors
