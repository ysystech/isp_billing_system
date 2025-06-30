# Role Permissions Empty Categories Fix

## Date: June 30, 2025

## Issue
After running `make set-defaults`, the role permissions page still shows:
- "Debug: permission_data has 0 categories"
- User cannot see any permissions to assign

## Root Cause
The role permissions view filters out permissions that the current user doesn't have. If the user is not a superuser and doesn't have many permissions themselves, they won't see any permissions to assign to roles.

## Solution Applied
Updated the permission filtering logic to include tenant owners:
- Superusers can see all permissions
- Tenant owners can see all permissions 
- Regular users can only see permissions they have

## Code Change
In `apps/roles/views.py`, the role_permissions view now checks:
```python
if (request.user.is_superuser or 
    getattr(request.user, 'is_tenant_owner', False) or 
    perm_name in request.user.get_all_permissions()):
```

## Why This Makes Sense
1. **Tenant Owners**: Should have full control over their tenant, including assigning any permission to roles
2. **Superusers**: Already have full access
3. **Regular Users**: Can only delegate permissions they themselves have (security principle)

## Alternative Solutions

### 1. Grant More Permissions
Grant the user all permissions they need to manage:
```python
from django.contrib.auth.models import Permission
from apps.users.models import CustomUser

user = CustomUser.objects.get(email='your@email.com')
all_perms = Permission.objects.all()
user.user_permissions.set(all_perms)
```

### 2. Make User a Tenant Owner
If the user should manage the tenant:
```python
user.is_tenant_owner = True
user.save()
```

### 3. Create a Super Admin Role
Create a role with all permissions and assign it to admin users.

## Verification
After the fix:
1. Tenant owners will see all permission categories
2. They can assign any permission to roles
3. The debug message should show categories > 0
