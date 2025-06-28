# CustomerSubscription Removal Plan

## 1. Database Migration to Remove CustomerSubscription Model

Create migration to drop the table:
```bash
python manage.py makemigrations customer_subscriptions --empty -n remove_customer_subscription
```

## 2. Files to Delete Completely

### App Directory
- `/apps/customer_subscriptions/` - entire directory

### Templates
- `/templates/customer_subscriptions/` - entire directory
- `/templates/dashboard/widgets/subscriptions_widget.html`

## 3. Code Modifications Required

### apps/customer_installations/models.py
Remove these properties from CustomerInstallation model:
- `current_subscription`
- `is_expired`
- `days_until_expiry`
- `last_subscription`

### apps/web/views.py
Remove subscription statistics section from home view

### apps/dashboard/views.py
Remove CustomerSubscription import and related code

### isp_billing_system/settings.py
Remove 'apps.customer_subscriptions' from INSTALLED_APPS

### isp_billing_system/urls.py
Remove customer_subscriptions URL include

### templates/web/components/app_nav_menu_items.html
Remove "Subscriptions" menu item that links to customer_subscriptions

### templates/web/app_home.html
Remove subscription statistics display

### templates/customer_installations/installation_list.html
Remove subscription status column

### templates/customer_installations/installation_detail.html
Remove subscription history section

## 4. Import Cleanup
Remove all imports of:
- `from apps.customer_subscriptions.models import CustomerSubscription`
- Any customer_subscriptions related imports

## 5. Management Commands to Update
- Update or remove generate_subscriptions command
- Update hard_delete_records command to remove customer_subscriptions references
