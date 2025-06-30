# Role View Permission Fix

## Date: June 30, 2025

## Issue
When trying to view a role (e.g., "Cashier"), users were getting:
"You do not have permission to view the role 'Cashier'."

## Root Cause
The `can_manage_role` function in `apps/roles/helpers/permissions.py` was checking if the user had ALL the permissions that the role contains. This meant:
- To view a Cashier role, you needed all Cashier permissions
- To edit an Admin role, you needed all Admin permissions
- This was overly restrictive, especially for tenant owners

## Solution
Updated the `can_manage_role` function to:
1. Allow superusers to manage any role (existing)
2. **NEW**: Allow tenant owners to manage any role in their tenant
3. For regular users, keep the existing permission check

## Code Change
```python
def can_manage_role(user, role):
    # Superusers can manage any role
    if user.is_superuser:
        return True
    
    # Tenant owners can manage any role in their tenant
    if getattr(user, 'is_tenant_owner', False) and role.tenant == user.tenant:
        return True
    
    # Regular users need all permissions the role has
    # ... existing permission check ...
```

## Impact

### Before:
- Tenant owners couldn't view/edit roles unless they had all permissions
- Very restrictive access control
- Frustrating user experience

### After:
- Tenant owners can view/edit/manage all roles in their tenant
- Makes sense: they own the company account
- Regular users still have permission-based restrictions

## Who Can Access Roles Now:

1. **Superusers**: Can access any role (unchanged)
2. **Tenant Owners**: Can access any role in their tenant (NEW)
3. **Regular Users**: Can only access roles where they have ALL the role's permissions

## Security Consideration
This change is secure because:
- Tenant owners already have full control via `is_tenant_owner` flag
- They can only manage roles within their own tenant
- Cross-tenant access is still prevented
- Regular users remain restricted

## Verification
To verify you're a tenant owner:
```python
from apps.users.models import CustomUser
user = CustomUser.objects.get(email='your@email.com')
print(f"Is tenant owner: {user.is_tenant_owner}")
```

If you should be a tenant owner but aren't:
```python
user.is_tenant_owner = True
user.save()
```
