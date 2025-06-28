"""
Management command to map Django permissions to categories.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from apps.roles.models import PermissionCategory, PermissionCategoryMapping


class Command(BaseCommand):
    help = 'Map permissions to categories for better organization'

    def handle(self, *args, **options):
        permission_mappings = {
            'basic': [
                # Dashboard
                ('dashboard', 'view_dashboard', 'View Dashboard', 'Access to main dashboard'),
                ('web', 'view_home', 'View Home Page', 'Access to home page'),
            ],
            'customers': [
                # Customer permissions
                ('customers', 'view_customer', 'View Customers', 'View customer records'),
                ('customers', 'view_customer_list', 'View Customer List', 'Access customer listing page'),
                ('customers', 'view_customer_detail', 'View Customer Details', 'View detailed customer information'),
                ('customers', 'view_customer_sensitive_info', 'View Sensitive Info', 'View sensitive customer data like coordinates'),
                ('customers', 'add_customer', 'Add Customer', 'Create new customer records'),
                ('customers', 'create_customer', 'Create Customer', 'Create new customer records'),
                ('customers', 'change_customer', 'Edit Customer', 'Edit existing customer records'),
                ('customers', 'change_customer_basic', 'Edit Basic Info', 'Edit customer basic information'),
                ('customers', 'change_customer_status', 'Change Status', 'Change customer account status'),
                ('customers', 'change_customer_address', 'Edit Address', 'Edit customer address information'),
                ('customers', 'delete_customer', 'Delete Customer', 'Delete customer records'),
                ('customers', 'remove_customer', 'Remove Customer', 'Remove customer records'),
                ('customers', 'export_customers', 'Export Customers', 'Export customer data to file'),
                ('customers', 'import_customers', 'Import Customers', 'Import customer data from file'),
                ('customers', 'view_customer_coordinates', 'View Coordinates', 'View customer GPS coordinates'),
                
                # Barangay permissions
                ('barangays', 'view_barangay', 'View Barangays', 'View barangay records'),
                ('barangays', 'view_barangay_list', 'View Barangay List', 'Access barangay listing'),
                ('barangays', 'add_barangay', 'Add Barangay', 'Create new barangay'),
                ('barangays', 'change_barangay', 'Edit Barangay', 'Edit barangay information'),
                ('barangays', 'delete_barangay', 'Delete Barangay', 'Delete barangay records'),
                ('barangays', 'manage_barangay_status', 'Manage Status', 'Activate/deactivate barangays'),
                ('barangays', 'view_barangay_statistics', 'View Statistics', 'View barangay statistics'),
            ],
            'billing': [
                # Subscription plans
                ('subscriptions', 'view_subscriptionplan', 'View Plans', 'View subscription plans'),
                ('subscriptions', 'view_subscriptionplan_list', 'View Plan List', 'Access plan listing'),
                ('subscriptions', 'add_subscriptionplan', 'Add Plan', 'Create new subscription plan'),
                ('subscriptions', 'change_subscriptionplan', 'Edit Plan', 'Edit subscription plans'),
                ('subscriptions', 'change_subscriptionplan_pricing', 'Change Pricing', 'Modify plan pricing'),
                ('subscriptions', 'delete_subscriptionplan', 'Delete Plan', 'Delete subscription plans'),
                ('subscriptions', 'activate_deactivate_plans', 'Manage Plan Status', 'Activate/deactivate plans'),
                ('subscriptions', 'create_promotional_plans', 'Create Promotions', 'Create promotional plans'),
                
                # Customer subscriptions
                ('customer_subscriptions', 'view_customersubscription', 'View Subscriptions', 'View customer subscriptions'),
                ('customer_subscriptions', 'view_subscription_list', 'View Subscription List', 'Access subscription listing'),
                ('customer_subscriptions', 'view_subscription_detail', 'View Details', 'View subscription details'),
                ('customer_subscriptions', 'add_customersubscription', 'Add Subscription', 'Create new subscription'),
                ('customer_subscriptions', 'create_subscription', 'Create Subscription', 'Process new subscription'),
                ('customer_subscriptions', 'process_payment', 'Process Payment', 'Process subscription payments'),
                ('customer_subscriptions', 'generate_receipt', 'Generate Receipt', 'Generate payment receipts'),
                ('customer_subscriptions', 'cancel_subscription', 'Cancel Subscription', 'Cancel active subscriptions'),
                ('customer_subscriptions', 'view_payment_history', 'View Payment History', 'View customer payment history'),
                ('customer_subscriptions', 'view_financial_summary', 'View Financial Summary', 'View financial summaries'),
                ('customer_subscriptions', 'process_refund', 'Process Refund', 'Process subscription refunds'),
                ('customer_subscriptions', 'export_subscription_data', 'Export Data', 'Export subscription data'),
            ],
            'infrastructure': [
                # LCP
                ('lcp', 'view_lcp', 'View LCP', 'View LCP records'),
                ('lcp', 'view_lcp_list', 'View LCP List', 'Access LCP listing'),
                ('lcp', 'view_lcp_detail', 'View LCP Details', 'View detailed LCP information'),
                ('lcp', 'add_lcp', 'Add LCP', 'Create new LCP'),
                ('lcp', 'change_lcp', 'Edit LCP', 'Edit LCP information'),
                ('lcp', 'delete_lcp', 'Delete LCP', 'Delete LCP records'),
                ('lcp', 'manage_lcp_infrastructure', 'Manage Infrastructure', 'Manage LCP infrastructure'),
                ('lcp', 'view_lcp_map', 'View on Map', 'View LCP locations on map'),
                ('lcp', 'export_lcp_data', 'Export LCP Data', 'Export LCP data'),
                
                # Splitter
                ('lcp', 'view_splitter', 'View Splitters', 'View splitter records'),
                ('lcp', 'view_splitter_list', 'View Splitter List', 'Access splitter listing'),
                ('lcp', 'view_splitter_detail', 'View Splitter Details', 'View splitter details'),
                ('lcp', 'add_splitter', 'Add Splitter', 'Create new splitter'),
                ('lcp', 'change_splitter', 'Edit Splitter', 'Edit splitter information'),
                ('lcp', 'delete_splitter', 'Delete Splitter', 'Delete splitter records'),
                ('lcp', 'manage_splitter_ports', 'Manage Ports', 'Manage splitter port assignments'),
                
                # NAP
                ('lcp', 'view_nap', 'View NAP', 'View NAP records'),
                ('lcp', 'view_nap_list', 'View NAP List', 'Access NAP listing'),
                ('lcp', 'view_nap_detail', 'View NAP Details', 'View NAP details'),
                ('lcp', 'add_nap', 'Add NAP', 'Create new NAP'),
                ('lcp', 'change_nap', 'Edit NAP', 'Edit NAP information'),
                ('lcp', 'delete_nap', 'Delete NAP', 'Delete NAP records'),
                ('lcp', 'manage_nap_ports', 'Manage NAP Ports', 'Manage NAP port assignments'),
                ('lcp', 'view_nap_availability', 'View Availability', 'View NAP port availability'),
                
                # Network
                ('network', 'view_network_map', 'View Network Map', 'Access network visualization map'),
                ('network', 'view_network_hierarchy', 'View Hierarchy', 'View network hierarchy'),
                ('network', 'export_network_data', 'Export Network Data', 'Export network data'),
                ('network', 'view_coverage_analysis', 'View Coverage', 'View network coverage analysis'),
            ],
            'technical': [
                # Routers
                ('routers', 'view_router', 'View Routers', 'View router inventory'),
                ('routers', 'view_router_list', 'View Router List', 'Access router listing'),
                ('routers', 'view_router_detail', 'View Router Details', 'View router details'),
                ('routers', 'add_router', 'Add Router', 'Add new router to inventory'),
                ('routers', 'change_router', 'Edit Router', 'Edit router information'),
                ('routers', 'delete_router', 'Delete Router', 'Delete router records'),
                ('routers', 'manage_router_inventory', 'Manage Inventory', 'Manage router inventory'),
                ('routers', 'export_router_data', 'Export Router Data', 'Export router data'),
                ('routers', 'bulk_import_routers', 'Bulk Import', 'Bulk import routers'),
                ('routers', 'view_router_mac_address', 'View MAC Address', 'View router MAC addresses'),
                
                # Installations
                ('customer_installations', 'view_customerinstallation', 'View Installations', 'View installations'),
                ('customer_installations', 'view_installation_list', 'View List', 'Access installation listing'),
                ('customer_installations', 'view_installation_detail', 'View Details', 'View installation details'),
                ('customer_installations', 'add_customerinstallation', 'Add Installation', 'Create new installation'),
                ('customer_installations', 'create_installation', 'Create Installation', 'Process new installation'),
                ('customer_installations', 'change_customerinstallation', 'Edit Installation', 'Edit installation'),
                ('customer_installations', 'change_installation_status', 'Change Status', 'Change installation status'),
                ('customer_installations', 'delete_customerinstallation', 'Delete Installation', 'Delete installation'),
                ('customer_installations', 'assign_technician', 'Assign Technician', 'Assign technician to installation'),
                ('customer_installations', 'view_installation_technical_details', 'View Technical Details', 'View technical installation details'),
                ('customer_installations', 'manage_nap_assignments', 'Manage NAP', 'Manage NAP port assignments'),
                ('customer_installations', 'export_installation_data', 'Export Data', 'Export installation data'),
            ],
            'support': [
                # Tickets
                ('tickets', 'view_ticket', 'View Tickets', 'View support tickets'),
                ('tickets', 'view_ticket_list', 'View Ticket List', 'Access ticket listing'),
                ('tickets', 'view_ticket_detail', 'View Ticket Details', 'View ticket details'),
                ('tickets', 'add_ticket', 'Add Ticket', 'Create new ticket'),
                ('tickets', 'create_ticket', 'Create Ticket', 'Create support ticket'),
                ('tickets', 'change_ticket', 'Edit Ticket', 'Edit ticket information'),
                ('tickets', 'delete_ticket', 'Delete Ticket', 'Delete ticket'),
                ('tickets', 'remove_ticket', 'Remove Ticket', 'Remove ticket records'),
                ('tickets', 'assign_ticket', 'Assign Ticket', 'Assign ticket to technician'),
                ('tickets', 'change_ticket_status', 'Change Status', 'Change ticket status'),
                ('tickets', 'change_ticket_priority', 'Change Priority', 'Change ticket priority'),
                ('tickets', 'add_ticket_comment', 'Add Comment', 'Add comments to tickets'),
                ('tickets', 'view_all_tickets', 'View All Tickets', 'View all tickets (not just assigned)'),
                ('tickets', 'export_ticket_data', 'Export Tickets', 'Export ticket data'),
                
                # Ticket comments
                ('tickets', 'view_ticketcomment', 'View Comments', 'View ticket comments'),
                ('tickets', 'add_ticketcomment', 'Add Comment', 'Add ticket comments'),
                ('tickets', 'change_ticketcomment', 'Edit Comment', 'Edit ticket comments'),
                ('tickets', 'delete_ticketcomment', 'Delete Comment', 'Delete ticket comments'),
                ('tickets', 'view_ticket_comments', 'View All Comments', 'View all ticket comments'),
                ('tickets', 'delete_any_comment', 'Delete Any Comment', 'Delete any user\'s comments'),
            ],
            'reports': [
                # Report permissions
                ('reports', 'view_daily_collection_report', 'Daily Collection', 'View daily collection report'),
                ('reports', 'view_subscription_expiry_report', 'Subscription Expiry', 'View subscription expiry report'),
                ('reports', 'export_operational_reports', 'Export Operational', 'Export operational reports'),
                ('reports', 'view_monthly_revenue_report', 'Monthly Revenue', 'View monthly revenue report'),
                ('reports', 'view_ticket_analysis_report', 'Ticket Analysis', 'View ticket analysis report'),
                ('reports', 'view_technician_performance_report', 'Technician Performance', 'View technician performance'),
                ('reports', 'view_customer_acquisition_report', 'Customer Acquisition', 'View customer acquisition'),
                ('reports', 'view_payment_behavior_report', 'Payment Behavior', 'View payment behavior analysis'),
                ('reports', 'export_business_reports', 'Export Business Reports', 'Export business intelligence reports'),
                ('reports', 'view_area_performance_dashboard', 'Area Performance', 'View area performance dashboard'),
                ('reports', 'view_financial_dashboard', 'Financial Dashboard', 'View financial dashboard'),
                ('reports', 'access_advanced_analytics', 'Advanced Analytics', 'Access advanced analytics features'),
                ('reports', 'schedule_reports', 'Schedule Reports', 'Schedule automated reports'),
                ('reports', 'customize_report_parameters', 'Customize Reports', 'Customize report parameters'),
                
                # Dashboard statistics
                ('dashboard', 'view_customer_statistics', 'Customer Stats', 'View customer statistics'),
                ('dashboard', 'view_infrastructure_statistics', 'Infrastructure Stats', 'View infrastructure statistics'),
                ('dashboard', 'view_financial_statistics', 'Financial Stats', 'View financial statistics'),
                ('dashboard', 'view_system_statistics', 'System Stats', 'View system statistics'),
            ],
            'admin': [
                # User management
                ('users', 'view_customuser', 'View Users', 'View user accounts'),
                ('users', 'add_customuser', 'Add User', 'Create new user account'),
                ('users', 'change_customuser', 'Edit User', 'Edit user information'),
                ('users', 'delete_customuser', 'Delete User', 'Delete user account'),
                
                # Role management
                ('roles', 'view_role', 'View Roles', 'View roles'),
                ('roles', 'add_role', 'Add Role', 'Create new role'),
                ('roles', 'change_role', 'Edit Role', 'Edit role permissions'),
                ('roles', 'delete_role', 'Delete Role', 'Delete role'),
                
                # Django admin
                ('admin', 'view_logentry', 'View Admin Logs', 'View admin action logs'),
            ]
        }
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for category_code, mappings in permission_mappings.items():
                try:
                    category = PermissionCategory.objects.get(code=category_code)
                    self.stdout.write(f'\nProcessing category: {category.name}')
                    
                    for app_label, codename, display_name, description in mappings:
                        try:
                            # Get the permission
                            permission = Permission.objects.get(
                                content_type__app_label=app_label,
                                codename=codename
                            )
                            
                            # Create or update mapping
                            mapping, created = PermissionCategoryMapping.objects.update_or_create(
                                category=category,
                                permission=permission,
                                defaults={
                                    'display_name': display_name,
                                    'description': description,
                                    'order': created_count + updated_count
                                }
                            )
                            
                            if created:
                                created_count += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f'  ✓ Created: {display_name}')
                                )
                            else:
                                updated_count += 1
                                self.stdout.write(
                                    self.style.WARNING(f'  ↻ Updated: {display_name}')
                                )
                        
                        except Permission.DoesNotExist:
                            skipped_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'  ⚠ Skipped: {app_label}.{codename} (permission not found)')
                            )
                
                except PermissionCategory.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Category not found: {category_code}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n\nSummary:'
                f'\n  Created: {created_count} mappings'
                f'\n  Updated: {updated_count} mappings' 
                f'\n  Skipped: {skipped_count} mappings'
            )
        )
