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
            ('customers', 'change_customer'),  # We use change_customer_basic
            ('customers', 'delete_customer'),  # We use remove_customer
            ('customers', 'view_customer'),  # We use view_customer_list
            ('customers', 'view_customer_sensitive_info'),  # Covered by view_customer_detail
            ('customers', 'view_customer_coordinates'),  # Covered by view_customer_detail
            ('customers', 'change_customer_status'),  # Covered by change_customer_basic
            ('customers', 'change_customer_address'),  # Covered by change_customer_basic
            ('customers', 'import_customers'),  # Feature not implemented yet
            ('customer_subscriptions', 'add_customersubscription'),  # We use create_subscription
            ('customer_subscriptions', 'change_customersubscription'),  # We use cancel_subscription for management
            ('customer_subscriptions', 'delete_customersubscription'),  # We use cancel_subscription
            ('customer_subscriptions', 'view_customersubscription'),  # We use view_subscription_list
            ('customer_subscriptions', 'view_subscription_detail'),  # Covered by view_subscription_list
            ('customer_subscriptions', 'process_payment'),  # Covered by create_subscription
            ('customer_subscriptions', 'view_payment_history'),  # Covered by view_subscription_list
            ('customer_subscriptions', 'view_financial_summary'),  # Covered by view_subscription_list
            ('customer_subscriptions', 'process_refund'),  # Covered by cancel_subscription
            ('reports', 'view_active_subscriptions'),  # Covered by view_subscription_list
            ('customer_installations', 'add_customerinstallation'),  # We use create_installation
            ('customer_installations', 'change_customerinstallation'),  # We use change_installation_status
            ('customer_installations', 'view_customerinstallation'),  # We use view_installation_list
            ('customer_installations', 'view_installation_detail'),  # Covered by view_installation_list
            ('customer_installations', 'assign_technician'),  # Covered by change_installation_status
            ('customer_installations', 'view_installation_technical_details'),  # Covered by view_installation_list
            ('customer_installations', 'manage_nap_assignments'),  # Covered by change_installation_status
            ('tickets', 'add_ticket'),  # We use create_ticket
            ('tickets', 'change_ticket'),  # We use edit_ticket now
            ('tickets', 'delete_ticket'),  # We use remove_ticket
            ('tickets', 'view_ticket'),  # We use view_ticket_list
            ('tickets', 'add_ticketcomment'),  # We use add_ticket_comment
            ('tickets', 'view_ticket_detail'),  # Covered by view_ticket_list
            ('tickets', 'change_ticket_priority'),  # Covered by change_ticket_status
            ('tickets', 'view_all_tickets'),  # Covered by view_ticket_list
            ('tickets', 'view_ticketcomment'),  # Covered by view_ticket_list
            ('tickets', 'change_ticketcomment'),  # Not needed in simplified workflow
            ('tickets', 'delete_ticketcomment'),  # Not needed in simplified workflow
            ('tickets', 'delete_any_comment'),  # Not needed in simplified workflow
            ('tickets', 'assign_ticket'),  # Removed as requested
            ('routers', 'view_router'),  # We use view_router_list
            ('routers', 'view_router_detail'),  # Covered by view_router_list
            ('routers', 'manage_router_inventory'),  # Not needed - CRUD is enough
            ('routers', 'export_router_data'),  # Not needed - CRUD is enough
            ('routers', 'bulk_import_routers'),  # Not needed - CRUD is enough
            ('routers', 'view_router_mac_address'),  # Covered by view_router_list
            ('lcp', 'change_lcp'),  # We use manage_lcp_infrastructure
            ('lcp', 'change_splitter'),  # We use manage_lcp_infrastructure
            ('lcp', 'change_nap'),  # We use manage_lcp_infrastructure
            ('lcp', 'view_lcp'),  # We use view_lcp_list
            ('lcp', 'view_splitter'),  # We use view_lcp_list
            ('lcp', 'view_nap'),  # We use view_lcp_list
            ('lcp', 'view_lcp_map'),  # Covered by view_lcp_detail
            ('lcp', 'export_lcp_data'),  # Not essential for basic management
            ('lcp', 'view_splitter_list'),  # Covered by view_lcp_list
            ('lcp', 'view_splitter_detail'),  # Covered by view_lcp_detail
            ('lcp', 'add_splitter'),  # Covered by add_lcp
            ('lcp', 'delete_splitter'),  # Covered by delete_lcp
            ('lcp', 'manage_splitter_ports'),  # Covered by manage_lcp_infrastructure
            ('lcp', 'view_nap_list'),  # Covered by view_lcp_list
            ('lcp', 'view_nap_detail'),  # Covered by view_lcp_detail
            ('lcp', 'add_nap'),  # Covered by add_lcp
            ('lcp', 'delete_nap'),  # Covered by delete_lcp
            ('lcp', 'manage_nap_ports'),  # Covered by manage_lcp_infrastructure
            ('lcp', 'view_nap_availability'),  # Covered by view_lcp_detail
            ('network', 'view_network_hierarchy'),  # Covered by view_network_map
            ('network', 'export_network_data'),  # Covered by view_network_map
            ('network', 'view_coverage_analysis'),  # Covered by view_network_map
            ('subscriptions', 'view_subscriptionplan'),  # We use view_subscriptionplan_list
            ('subscriptions', 'change_subscriptionplan_pricing'),  # Covered by change_subscriptionplan
            ('subscriptions', 'activate_deactivate_plans'),  # Covered by change_subscriptionplan
            ('subscriptions', 'create_promotional_plans'),  # Not needed - edit plan is enough
            ('barangays', 'view_barangay'),  # We use view_barangay_list
            ('barangays', 'manage_barangay_status'),  # Not needed - CRUD is enough
            ('barangays', 'view_barangay_statistics'),  # Not needed - CRUD is enough
            # Reports permissions removed during simplification
            ('reports', 'view_reports'),  # Replaced by view_reports_dashboard
            ('reports', 'view_customer_statistics'),  # Removed - simplified
            ('reports', 'view_financial_statistics'),  # Removed - simplified
            ('reports', 'view_infrastructure_statistics'),  # Removed - simplified
            ('reports', 'view_system_statistics'),  # Removed - simplified
            ('reports', 'access_advanced_analytics'),  # Removed - simplified
            ('reports', 'customize_report_parameters'),  # Removed - simplified
            ('reports', 'export_business_reports'),  # Consolidated to export_reports
            ('reports', 'export_operational_reports'),  # Consolidated to export_reports
            ('reports', 'schedule_reports'),  # Removed - simplified
            ('reports', 'view_active_subscriptions'),  # Removed - part of dashboard
        ]
        
        permission_mappings = {
            'dashboard': [
                ('dashboard', 'view_dashboard', 'View Dashboard', 'Access main dashboard'),
                ('dashboard', 'view_customer_overview', 'Customer Overview', 'View customer overview widget'),
                ('dashboard', 'view_subscription_overview', 'Subscription Overview', 'View subscription overview widget'),
                ('dashboard', 'view_financial_overview', 'Financial Overview', 'View financial overview widget'),
                ('dashboard', 'view_technical_overview', 'Technical Overview', 'View technical overview widget'),
            ],'customers': [
                # Customer-specific permissions - simplified to essential permissions only
                ('customers', 'view_customer_list', 'View Customer List', 'Access customer listing page'),
                ('customers', 'view_customer_detail', 'View Customer Details', 'View detailed customer information including coordinates and sensitive data'),
                ('customers', 'create_customer', 'Create Customer', 'Create new customer records'),
                ('customers', 'change_customer_basic', 'Edit Customer', 'Edit all customer information including basic info, status, and address'),
                ('customers', 'remove_customer', 'Remove Customer', 'Remove customer records'),
                ('customers', 'export_customers', 'Export Customers', 'Export customer data to file'),
            ],
            'barangays': [
                # Barangay permissions - simple CRUD only
                ('barangays', 'view_barangay_list', 'View Barangay List', 'Access barangay listing'),
                ('barangays', 'add_barangay', 'Add Barangay', 'Create new barangay'),
                ('barangays', 'change_barangay', 'Edit Barangay', 'Edit barangay information'),
                ('barangays', 'delete_barangay', 'Delete Barangay', 'Delete barangay records'),
            ],
            'routers': [
                # Router permissions - simple CRUD only
                ('routers', 'view_router_list', 'View Router List', 'Access router listing and details'),
                ('routers', 'add_router', 'Add Router', 'Add new router to inventory'),
                ('routers', 'change_router', 'Edit Router', 'Edit router information'),
                ('routers', 'delete_router', 'Delete Router', 'Delete router records'),
            ],
            'plans': [
                # Subscription plan permissions - simplified CRUD
                ('subscriptions', 'view_subscriptionplan_list', 'View Plan List', 'Access plan listing and details'),
                ('subscriptions', 'add_subscriptionplan', 'Add Plan', 'Create new subscription plan'),
                ('subscriptions', 'change_subscriptionplan', 'Edit Plan', 'Edit subscription plans including pricing and status'),
                ('subscriptions', 'delete_subscriptionplan', 'Delete Plan', 'Delete subscription plans'),
            ],            'lcp': [
                # LCP Infrastructure permissions - unified management
                ('lcp', 'view_lcp_list', 'View List', 'View lists of LCP, Splitter, and NAP in tables'),
                ('lcp', 'view_lcp_detail', 'View Details', 'View detailed LCP info including Splitters, NAPs and infrastructure hierarchy'),
                ('lcp', 'add_lcp', 'Create', 'Create LCP, Splitter, and NAP records'),
                ('lcp', 'manage_lcp_infrastructure', 'Edit', 'Edit LCP records and all infrastructure components'),
                ('lcp', 'delete_lcp', 'Delete', 'Delete LCP and all related infrastructure'),
            ],
            'installations': [
                # Customer installation permissions - simplified to 5 core permissions
                ('customer_installations', 'view_installation_list', 'View Installations', 'View installation list, details, and technical information'),
                ('customer_installations', 'create_installation', 'Create Installation', 'Process new customer installations'),
                ('customer_installations', 'change_installation_status', 'Edit Installation', 'Edit installations including status, technician assignment, and NAP management'),
                ('customer_installations', 'delete_customerinstallation', 'Delete Installation', 'Delete installation records'),
                ('customer_installations', 'export_installation_data', 'Export Installation Data', 'Export installation data to file'),
            ],            'subscriptions': [
                # Customer subscription permissions - simplified to 5 core permissions
                ('customer_subscriptions', 'view_subscription_list', 'View Subscriptions', 'View all subscription data including list, details, history, and financial summary'),
                ('customer_subscriptions', 'create_subscription', 'Create Subscription', 'Create new subscriptions and process payments'),
                ('customer_subscriptions', 'cancel_subscription', 'Manage Subscription', 'Cancel subscriptions, process refunds, and modify subscription details'),
                ('customer_subscriptions', 'generate_receipt', 'Generate Receipt', 'Generate and print acknowledgment receipts'),
                ('customer_subscriptions', 'export_subscription_data', 'Export Subscription Data', 'Export subscription data and reports'),
            ],
            'tickets': [
                # Support ticket permissions - workflow-based structure
                ('tickets', 'view_ticket_list', 'View Tickets', 'View ticket list, details, and all comments'),
                ('tickets', 'create_ticket', 'Create Ticket', 'Create new support tickets'),
                ('tickets', 'edit_ticket', 'Edit Ticket', 'Edit all ticket information except status'),
                ('tickets', 'change_ticket_status', 'Update Ticket Status', 'Change ticket status via the dedicated status control'),
                ('tickets', 'add_ticket_comment', 'Add Comments', 'Add comments to tickets'),
                ('tickets', 'remove_ticket', 'Delete Ticket', 'Delete ticket records'),
                ('tickets', 'export_ticket_data', 'Export Ticket Data', 'Export ticket data and reports'),
            ],'reports': [
                # Reports and analytics permissions - simplified to 11 permissions
                ('reports', 'view_reports_dashboard', 'Access Reports', 'Access reports dashboard'),
                ('reports', 'view_daily_collection_report', 'Daily Collection', 'View daily collection report'),
                ('reports', 'view_subscription_expiry_report', 'Subscription Expiry', 'View subscription expiry report'),
                ('reports', 'view_monthly_revenue_report', 'Monthly Revenue', 'View monthly revenue report'),
                ('reports', 'view_ticket_analysis_report', 'Ticket Analysis', 'View ticket analysis report'),
                ('reports', 'view_technician_performance_report', 'Technician Performance', 'View technician performance'),
                ('reports', 'view_customer_acquisition_report', 'Customer Acquisition', 'View customer acquisition trends'),
                ('reports', 'view_payment_behavior_report', 'Payment Behavior', 'View payment behavior analysis'),
                ('reports', 'view_area_performance_dashboard', 'Area Performance', 'View area performance dashboard'),
                ('reports', 'view_financial_dashboard', 'Financial Dashboard', 'View financial dashboard'),
                ('reports', 'export_reports', 'Export Reports', 'Export all reports to files'),
                # Network visualization moved here
                ('network', 'view_network_map', 'View Network Visualization', 'Access network map, hierarchy, and all visualization features'),
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
                
                # Admin logs - TODO: Implement audit log viewing functionality
                # Currently this permission exists but there's no user-facing audit log viewer
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
                    # Try to get the most specific permission first
                    permissions_qs = Permission.objects.filter(
                        content_type__app_label=app_label,
                        codename=codename
                    )
                    
                    if permissions_qs.count() > 1:
                        # If multiple permissions exist, prefer the one with the matching model name
                        permission = permissions_qs.filter(
                            content_type__model=app_label.rstrip('s')
                        ).first() or permissions_qs.first()
                    else:
                        permission = permissions_qs.first()
                    
                    if not permission:
                        raise Permission.DoesNotExist
                    
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