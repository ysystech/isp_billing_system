# Fixed: NoReverseMatch Error

## Issue
After removing CustomerSubscription app, there were still template references causing:
```
NoReverseMatch: 'customer_subscriptions' is not a registered namespace
```

## Fixes Applied

1. **templates/customer_installations/installation_list.html**
   - Removed "Add Payment" button that referenced `customer_subscriptions:subscription_create`
   - Changed from button group to single "View" button

2. **apps/utils/management/commands/hard_delete_records.py**
   - Removed CustomerSubscription import
   - Removed CustomerSubscription deletion logic
   - Updated help text and output messages

3. **apps/dashboard/views.py**
   - Removed CustomerSubscription import
   - Removed subscription statistics calculation
   - Removed subscription_stats from context

4. **templates/dashboard/user_dashboard.html**
   - Removed subscription statistics widget section

## Result
The error should now be resolved. The installations page at `/installations/` should load without errors.

All references to the removed customer_subscriptions app have been cleaned up.
