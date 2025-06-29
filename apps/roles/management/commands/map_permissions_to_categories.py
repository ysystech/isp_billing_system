"""
Management command to map permissions to categories.
This command updates the permission mappings with user-friendly names.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from apps.roles.models import PermissionCategory, PermissionCategoryMapping


class Command(BaseCommand):
    help = 'Map permissions to categories with user-friendly names'

    def handle(self, *args, **options):
        # Define the mappings - organize permissions by category
        # Format: (app_label, codename, display_name, description)
        
        # Skip Django's default permissions when we have custom ones
        skip_permissions = [
            # Skip these default permissions as we have custom equivalents
            ('customers', 'add_customer'),  # We use create_customer
            ('customers', 'change_customer'),  # We use change_customer_basic, change_customer_status, etc.
            ('customers', 'delete_customer'),  # We use remove_customer
            ('customers', 'view_customer'),  # We use view_customer_list
            ('customer_subscriptions', 'add_customersubscription'),  # We use create_subscription
            ('customer_subscriptions', 'change_customersubscription'),  # We use specific permissions
            ('customer_subscriptions', 'delete_customersubscription'),  # We use cancel_subscription
            ('customer_subscriptions', 'view_customersubscription'),  # We use view_subscription_list
            ('customer_installations', 'add_customerinstallation'),  # We use create_installation
            ('customer_installations', 'change_customerinstallation'),  # We use specific permissions
            ('customer_installations', 'view_customerinstallation'),  # We use view_installation_list
            ('tickets', 'add_ticket'),  # We use create_ticket
            ('tickets', 'change_ticket'),  # We use specific permissions
            ('tickets', 'delete_ticket'),  # We use remove_ticket
            ('tickets', 'view_ticket'),  # We use view_ticket_list
            ('tickets', 'add_ticketcomment'),  # We use add_ticket_comment
            ('routers', 'change_router'),  # We have specific permissions
            ('routers', 'view_router'),  # We use view_router_list
            ('lcp', 'change_lcp'),  # We use manage_lcp_infrastructure
            ('lcp', 'change_splitter'),  # We use manage_splitter_ports
            ('lcp', 'change_nap'),  # We use manage_nap_ports
            ('lcp', 'view_lcp'),  # We use view_lcp_list
            ('lcp', 'view_splitter'),  # We use view_splitter_list
            ('lcp', 'view_nap'),  # We use view_nap_list
            ('subscriptions', 'view_subscriptionplan'),  # We use view_subscriptionplan_list
            ('barangays', 'view_barangay'),  # We use view_barangay_list
        ]
        
        permission_mappings = {
            'dashboard': [
                ('dashboard', 'view_dashboard', 'View Dashboard', 'Access main dashboard'),
                ('reports', 'view_customer_statistics', 'Customer Stats', 'View customer statistics'),
                ('reports', 'view_infrastructure_statistics', 'Infrastructure Stats', 'View infrastructure statistics'),
                ('reports', 'view_financial_statistics', 'Financial Stats', 'View financial statistics'),
                ('reports', 'view_system_statistics', 'System Stats', 'View system statistics'),
            ],            'customers': [
                # Customer-specific permissions only - removed view_customer as redundant
                ('customers', 'view_customer_list', 'View Customer List', 'Access customer listing page'),
                ('customers', 'view_customer_detail', 'View Customer Details', 'View detailed customer information'),
                ('customers', 'view_customer_sensitive_info', 'View Sensitive Info', 'View sensitive customer data like coordinates'),
                ('customers', 'create_customer', 'Create Customer', 'Create new customer records'),
                ('customers', 'change_customer_basic', 'Edit Basic Info', 'Edit customer basic information'),
                ('customers', 'change_customer_status', 'Change Status', 'Change customer account status'),
                ('customers', 'change_customer_address', 'Edit Address', 'Edit customer address information'),
                ('customers', 'remove_customer', 'Remove Customer', 'Remove customer records'),
                ('customers', 'export_customers', 'Export Customers', 'Export customer data to file'),
                ('customers', 'import_customers', 'Import Customers', 'Import customer data from file'),
                ('customers', 'view_customer_coordinates', 'View Coordinates', 'View customer GPS coordinates'),
            ],
            'barangays': [
                # Barangay permissions - removed view_barangay as redundant
                ('barangays', 'view_barangay_list', 'View Barangay List', 'Access barangay listing'),
                ('barangays', 'add_barangay', 'Add Barangay', 'Create new barangay'),
                ('barangays', 'change_barangay', 'Edit Barangay', 'Edit barangay information'),
                ('barangays', 'delete_barangay', 'Delete Barangay', 'Delete barangay records'),
                ('barangays', 'manage_barangay_status', 'Manage Status', 'Activate/deactivate barangays'),
                ('barangays', 'view_barangay_statistics', 'View Statistics', 'View barangay statistics'),
            ],
            'routers': [
                # Router permissions - removed view_router as redundant
                ('routers', 'view_router_list', 'View Router List', 'Access router listing'),
                ('routers', 'view_router_detail', 'View Router Details', 'View router details'),
                ('routers', 'add_router', 'Add Router', 'Add new router to inventory'),
                ('routers', 'delete_router', 'Delete Router', 'Delete router records'),
                ('routers', 'manage_router_inventory', 'Manage Inventory', 'Manage router inventory'),
                ('routers', 'export_router_data', 'Export Router Data', 'Export router data'),
                ('routers', 'bulk_import_routers', 'Bulk Import', 'Bulk import routers'),
                ('routers', 'view_router_mac_address', 'View MAC Address', 'View router MAC addresses'),
            ],
            'plans': [
                # Subscription plan permissions - removed view_subscriptionplan as redundant
                ('subscriptions', 'view_subscriptionplan_list', 'View Plan List', 'Access plan listing'),
                ('subscriptions', 'add_subscriptionplan', 'Add Plan', 'Create new subscription plan'),
                ('subscriptions', 'change_subscriptionplan', 'Edit Plan', 'Edit subscription plans'),
                ('subscriptions', 'change_subscriptionplan_pricing', 'Change Pricing', 'Modify plan pricing'),
                ('subscriptions', 'delete_subscriptionplan', 'Delete Plan', 'Delete subscription plans'),
                ('subscriptions', 'activate_deactivate_plans', 'Manage Plan Status', 'Activate/deactivate plans'),
                ('subscriptions', 'create_promotional_plans', 'Create Promotions', 'Create promotional plans'),
            ],            'lcp': [
                # LCP Infrastructure permissions - removed view_lcp, view_splitter, view_nap as redundant
                ('lcp', 'view_lcp_list', 'View LCP List', 'Access LCP listing'),
                ('lcp', 'view_lcp_detail', 'View LCP Details', 'View detailed LCP information'),
                ('lcp', 'add_lcp', 'Add LCP', 'Create new LCP'),
                ('lcp', 'delete_lcp', 'Delete LCP', 'Delete LCP records'),
                ('lcp', 'manage_lcp_infrastructure', 'Manage LCP', 'Manage LCP infrastructure'),
                ('lcp', 'view_lcp_map', 'View on Map', 'View LCP locations on map'),
                ('lcp', 'export_lcp_data', 'Export LCP Data', 'Export LCP data'),
                
                # Splitter
                ('lcp', 'view_splitter_list', 'View Splitter List', 'Access splitter listing'),
                ('lcp', 'view_splitter_detail', 'View Splitter Details', 'View splitter details'),
                ('lcp', 'add_splitter', 'Add Splitter', 'Create new splitter'),
                ('lcp', 'delete_splitter', 'Delete Splitter', 'Delete splitter records'),
                ('lcp', 'manage_splitter_ports', 'Manage Splitter Ports', 'Manage splitter port assignments'),
                
                # NAP
                ('lcp', 'view_nap_list', 'View NAP List', 'Access NAP listing'),
                ('lcp', 'view_nap_detail', 'View NAP Details', 'View NAP details'),
                ('lcp', 'add_nap', 'Add NAP', 'Create new NAP'),
                ('lcp', 'delete_nap', 'Delete NAP', 'Delete NAP records'),
                ('lcp', 'manage_nap_ports', 'Manage NAP Ports', 'Manage NAP port assignments'),
                ('lcp', 'view_nap_availability', 'View Availability', 'View NAP port availability'),
            ],
            'network': [
                # Network visualization permissions
                ('network', 'view_network_map', 'View Network Map', 'Access network visualization map'),
                ('network', 'view_network_hierarchy', 'View Hierarchy', 'View network hierarchy'),
                ('network', 'export_network_data', 'Export Network Data', 'Export network data'),
                ('network', 'view_coverage_analysis', 'View Coverage', 'View network coverage analysis'),
            ],
            'installations': [
                # Customer installation permissions - removed view_customerinstallation as redundant
                ('customer_installations', 'view_installation_list', 'View Installation List', 'Access installation listing'),
                ('customer_installations', 'view_installation_detail', 'View Installation Details', 'View installation details'),
                ('customer_installations', 'create_installation', 'Create Installation', 'Process new installation'),
                ('customer_installations', 'change_installation_status', 'Change Status', 'Change installation status'),
                ('customer_installations', 'delete_customerinstallation', 'Delete Installation', 'Delete installation'),
                ('customer_installations', 'assign_technician', 'Assign Technician', 'Assign technician to installation'),
                ('customer_installations', 'view_installation_technical_details', 'View Technical Details', 'View technical installation details'),
                ('customer_installations', 'manage_nap_assignments', 'Manage NAP', 'Manage NAP port assignments'),
                ('customer_installations', 'export_installation_data', 'Export Data', 'Export installation data'),
            ],            'subscriptions': [
                # Customer subscription permissions - removed view_customersubscription as redundant
                ('customer_subscriptions', 'view_subscription_list', 'View Subscription List', 'Access subscription listing'),
                ('customer_subscriptions', 'view_subscription_detail', 'View Subscription Details', 'View subscription details'),
                ('customer_subscriptions', 'create_subscription', 'Create Subscription', 'Process new subscription'),
                ('customer_subscriptions', 'process_payment', 'Process Payment', 'Process subscription payments'),
                ('customer_subscriptions', 'generate_receipt', 'Generate Receipt', 'Generate payment receipts'),
                ('customer_subscriptions', 'cancel_subscription', 'Cancel Subscription', 'Cancel active subscriptions'),
                ('customer_subscriptions', 'view_payment_history', 'View Payment History', 'View customer payment history'),
                ('customer_subscriptions', 'view_financial_summary', 'View Financial Summary', 'View financial summaries'),
                ('customer_subscriptions', 'process_refund', 'Process Refund', 'Process subscription refunds'),
                ('customer_subscriptions', 'export_subscription_data', 'Export Data', 'Export subscription data'),
                ('reports', 'view_active_subscriptions', 'View Active Subscriptions', 'View currently active subscriptions'),
            ],
            'tickets': [
                # Support ticket permissions - removed view_ticket and add_ticketcomment as redundant
                ('tickets', 'view_ticket_list', 'View Ticket List', 'Access ticket listing'),
                ('tickets', 'view_ticket_detail', 'View Ticket Details', 'View ticket details'),
                ('tickets', 'create_ticket', 'Create Ticket', 'Create support ticket'),
                ('tickets', 'remove_ticket', 'Remove Ticket', 'Remove ticket records'),
                ('tickets', 'assign_ticket', 'Assign Ticket', 'Assign ticket to technician'),
                ('tickets', 'change_ticket_status', 'Change Status', 'Change ticket status'),
                ('tickets', 'change_ticket_priority', 'Change Priority', 'Change ticket priority'),
                ('tickets', 'add_ticket_comment', 'Add Comment', 'Add comments to tickets'),
                ('tickets', 'view_all_tickets', 'View All Tickets', 'View all tickets (not just assigned)'),
                ('tickets', 'export_ticket_data', 'Export Tickets', 'Export ticket data'),
                
                # Ticket comments - removed duplicate add_ticketcomment
                ('tickets', 'view_ticketcomment', 'View Comments', 'View ticket comments'),
                ('tickets', 'change_ticketcomment', 'Edit Comment', 'Edit own comments'),
                ('tickets', 'delete_ticketcomment', 'Delete Comment', 'Delete own comments'),
                ('tickets', 'delete_any_comment', 'Delete Any Comment', 'Delete any comment'),
            ],            'reports': [
                # Reports and analytics permissions - view_reports is a master permission for accessing the reports section
                ('reports', 'view_reports', 'Access Reports', 'Access reports dashboard'),
                ('reports', 'view_daily_collection_report', 'Daily Collection', 'View daily collection report'),
                ('reports', 'view_subscription_expiry_report', 'Subscription Expiry', 'View subscription expiry report'),
                ('reports', 'export_operational_reports', 'Export Operational', 'Export operational reports'),
                ('reports', 'view_monthly_revenue_report', 'Monthly Revenue', 'View monthly revenue report'),
                ('reports', 'view_ticket_analysis_report', 'Ticket Analysis', 'View ticket analysis report'),
                ('reports', 'view_technician_performance_report', 'Technician Performance', 'View technician performance'),
                ('reports', 'view_customer_acquisition_report', 'Customer Acquisition', 'View customer acquisition trends'),
                ('reports', 'view_payment_behavior_report', 'Payment Behavior', 'View payment behavior analysis'),
                ('reports', 'export_business_reports', 'Export Business Reports', 'Export business intelligence reports'),
                ('reports', 'view_area_performance_dashboard', 'Area Performance', 'View area performance dashboard'),
                ('reports', 'view_financial_dashboard', 'Financial Dashboard', 'View financial dashboard'),
                ('reports', 'access_advanced_analytics', 'Advanced Analytics', 'Access advanced analytics features'),
                ('reports', 'schedule_reports', 'Schedule Reports', 'Schedule automated reports'),
                ('reports', 'customize_report_parameters', 'Customize Reports', 'Customize report parameters'),
            ],
            'users': [
                # User and role management permissions
                ('users', 'view_customuser', 'View Users', 'View user accounts'),
                ('users', 'add_customuser', 'Add User', 'Create new user accounts'),
                ('users', 'change_customuser', 'Edit User', 'Edit user accounts'),
                ('users', 'delete_customuser', 'Delete User', 'Delete user accounts'),
                
                # Role management
                ('roles', 'view_role', 'View Roles', 'View system roles'),
                ('roles', 'add_role', 'Add Role', 'Create new roles'),
                ('roles', 'change_role', 'Edit Role', 'Edit role permissions'),
                ('roles', 'delete_role', 'Delete Role', 'Delete roles'),
                
                # Admin logs
                ('admin', 'view_logentry', 'View Admin Logs', 'View admin action logs'),
            ],
        }
        
        # Get categories - updated to use new category codes
        categories = {
            'dashboard': PermissionCategory.objects.get(code='dashboard'),
            'customers': PermissionCategory.objects.get(code='customers'),
            'barangays': PermissionCategory.objects.get(code='barangays'),
            'routers': PermissionCategory.objects.get(code='routers'),
            'plans': PermissionCategory.objects.get(code='plans'),
            'lcp': PermissionCategory.objects.get(code='lcp'),
            'network': PermissionCategory.objects.get(code='network'),
            'installations': PermissionCategory.objects.get(code='installations'),
            'subscriptions': PermissionCategory.objects.get(code='subscriptions'),
            'tickets': PermissionCategory.objects.get(code='tickets'),
            'reports': PermissionCategory.objects.get(code='reports'),
            'users': PermissionCategory.objects.get(code='users'),
        }
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        # Clear existing mappings first to ensure clean data
        PermissionCategoryMapping.objects.all().delete()
        self.stdout.write("Cleared all existing permission mappings")
        
        # Process each category
        for category_key, permissions in permission_mappings.items():
            try:
                category = categories[category_key]
            except KeyError:
                self.stdout.write(f"⚠️  Category '{category_key}' not found, skipping...")
                continue
                
            self.stdout.write(f"\nProcessing category: {category.name}")
            
            for app_label, codename, display_name, description in permissions:
                # Skip if in skip list
                if (app_label, codename) in skip_permissions:
                    self.stdout.write(f"  ⏭️  Skipped: {display_name} (redundant)")
                    skipped_count += 1
                    continue
                    
                try:
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename
                    )
                    
                    mapping, created = PermissionCategoryMapping.objects.update_or_create(
                        category=category,
                        permission=permission,
                        defaults={
                            'display_name': display_name,
                            'description': description,
                            'order': 0
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"  ✓ Created: {display_name}")
                        created_count += 1
                    else:
                        self.stdout.write(f"  ↻ Updated: {display_name}")
                        updated_count += 1
                        
                except Permission.DoesNotExist:
                    self.stdout.write(f"  ⚠ Skipped: {app_label}.{codename} (permission not found)")
                    skipped_count += 1
        
        # Remove any mappings for permissions in the skip list
        for app_label, codename in skip_permissions:
            try:
                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                deleted_count, _ = PermissionCategoryMapping.objects.filter(permission=permission).delete()
                if deleted_count > 0:
                    self.stdout.write(f"  🗑️  Removed redundant mapping: {app_label}.{codename}")
            except Permission.DoesNotExist:
                pass
        
        self.stdout.write(f"\n\nSummary:")
        self.stdout.write(f"  Created: {created_count} mappings")
        self.stdout.write(f"  Updated: {updated_count} mappings")
        self.stdout.write(f"  Skipped: {skipped_count} mappings")
        self.stdout.write(self.style.SUCCESS("\nPermission mappings configured successfully!"))