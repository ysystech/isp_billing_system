"""
Management command to create default roles with predefined permissions.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.db import transaction
from apps.roles.models import Role, RolePermissionPreset
from apps.roles.utils import create_role


class Command(BaseCommand):
    help = 'Create default roles with predefined permissions for the ISP billing system'

    def handle(self, *args, **options):
        # Define roles and their permissions
        roles_config = {
            'Super Admin': {
                'description': 'Full system access - can manage all aspects of the system',
                'is_system': True,
                'permissions': 'all'  # Special case - gets all permissions
            },
            'Manager': {
                'description': 'Can manage all business operations except system administration',
                'is_system': True,
                'permissions': [
                    # Basic
                    'dashboard.view_dashboard',
                    
                    # Customer Management - Full access
                    'customers.view_customer',
                    'customers.view_customer_list',
                    'customers.view_customer_detail',
                    'customers.view_customer_sensitive_info',
                    'customers.add_customer',
                    'customers.create_customer',
                    'customers.change_customer',
                    'customers.change_customer_basic',
                    'customers.change_customer_status',
                    'customers.change_customer_address',
                    'customers.delete_customer',
                    'customers.remove_customer',
                    'customers.export_customers',
                    'customers.import_customers',
                    'customers.view_customer_coordinates',
                    
                    # Barangay - Full access
                    'barangays.view_barangay',
                    'barangays.view_barangay_list',
                    'barangays.add_barangay',
                    'barangays.change_barangay',
                    'barangays.delete_barangay',
                    'barangays.manage_barangay_status',
                    'barangays.view_barangay_statistics',
                    
                    # Subscription Plans - Full access
                    'subscriptions.view_subscriptionplan',
                    'subscriptions.view_subscriptionplan_list',
                    'subscriptions.add_subscriptionplan',
                    'subscriptions.change_subscriptionplan',
                    'subscriptions.change_subscriptionplan_pricing',
                    'subscriptions.delete_subscriptionplan',
                    'subscriptions.activate_deactivate_plans',
                    'subscriptions.create_promotional_plans',
                    
                    # Customer Subscriptions - Full access
                    'customer_subscriptions.view_customersubscription',
                    'customer_subscriptions.view_subscription_list',
                    'customer_subscriptions.view_subscription_detail',
                    'customer_subscriptions.add_customersubscription',
                    'customer_subscriptions.create_subscription',
                    'customer_subscriptions.process_payment',
                    'customer_subscriptions.generate_receipt',
                    'customer_subscriptions.cancel_subscription',
                    'customer_subscriptions.view_payment_history',
                    'customer_subscriptions.view_financial_summary',
                    'customer_subscriptions.process_refund',
                    'customer_subscriptions.export_subscription_data',
                    
                    # Infrastructure - View and manage
                    'lcp.view_lcp',
                    'lcp.view_lcp_list',
                    'lcp.view_lcp_detail',
                    'lcp.add_lcp',
                    'lcp.change_lcp',
                    'lcp.manage_lcp_infrastructure',
                    'lcp.view_lcp_map',
                    'lcp.export_lcp_data',
                    
                    'lcp.view_splitter',
                    'lcp.view_splitter_list',
                    'lcp.view_splitter_detail',
                    'lcp.add_splitter',
                    'lcp.change_splitter',
                    'lcp.manage_splitter_ports',
                    
                    'lcp.view_nap',
                    'lcp.view_nap_list',
                    'lcp.view_nap_detail',
                    'lcp.add_nap',
                    'lcp.change_nap',
                    'lcp.manage_nap_ports',
                    'lcp.view_nap_availability',
                    
                    # Routers - Full access
                    'routers.view_router',
                    'routers.view_router_list',
                    'routers.view_router_detail',
                    'routers.add_router',
                    'routers.change_router',
                    'routers.delete_router',
                    'routers.manage_router_inventory',
                    'routers.export_router_data',
                    'routers.bulk_import_routers',
                    'routers.view_router_mac_address',
                    
                    # Installations - Full access
                    'customer_installations.view_customerinstallation',
                    'customer_installations.view_installation_list',
                    'customer_installations.view_installation_detail',
                    'customer_installations.add_customerinstallation',
                    'customer_installations.create_installation',
                    'customer_installations.change_customerinstallation',
                    'customer_installations.change_installation_status',
                    'customer_installations.assign_technician',
                    'customer_installations.view_installation_technical_details',
                    'customer_installations.manage_nap_assignments',
                    'customer_installations.export_installation_data',
                    
                    # Tickets - Full access
                    'tickets.view_ticket',
                    'tickets.view_ticket_list',
                    'tickets.view_ticket_detail',
                    'tickets.add_ticket',
                    'tickets.create_ticket',
                    'tickets.change_ticket',
                    'tickets.delete_ticket',
                    'tickets.remove_ticket',
                    'tickets.assign_ticket',
                    'tickets.change_ticket_status',
                    'tickets.change_ticket_priority',
                    'tickets.add_ticket_comment',
                    'tickets.view_all_tickets',
                    'tickets.export_ticket_data',
                    'tickets.view_ticketcomment',
                    'tickets.add_ticketcomment',
                    'tickets.change_ticketcomment',
                    'tickets.delete_ticketcomment',
                    'tickets.view_ticket_comments',
                    'tickets.delete_any_comment',
                    
                    # Reports - Full access
                    'reports.view_daily_collection_report',
                    'reports.view_subscription_expiry_report',
                    'reports.export_operational_reports',
                    'reports.view_monthly_revenue_report',
                    'reports.view_ticket_analysis_report',
                    'reports.view_technician_performance_report',
                    'reports.view_customer_acquisition_report',
                    'reports.view_payment_behavior_report',
                    'reports.export_business_reports',
                    'reports.view_area_performance_dashboard',
                    'reports.view_financial_dashboard',
                    'reports.access_advanced_analytics',
                    'reports.schedule_reports',
                    'reports.customize_report_parameters',
                    
                    # Dashboard statistics
                    'dashboard.view_customer_statistics',
                    'dashboard.view_infrastructure_statistics',
                    'dashboard.view_financial_statistics',
                    'dashboard.view_system_statistics',
                ]
            },
            'Cashier': {
                'description': 'Can process payments, manage subscriptions, and view customer information',
                'is_system': True,
                'permissions': [
                    # Basic
                    'dashboard.view_dashboard',
                    
                    # Customer Management - View only
                    'customers.view_customer',
                    'customers.view_customer_list',
                    'customers.view_customer_detail',
                    
                    # Barangay - View only
                    'barangays.view_barangay',
                    'barangays.view_barangay_list',
                    
                    # Subscription Plans - View only
                    'subscriptions.view_subscriptionplan',
                    'subscriptions.view_subscriptionplan_list',
                    
                    # Customer Subscriptions - Process payments
                    'customer_subscriptions.view_customersubscription',
                    'customer_subscriptions.view_subscription_list',
                    'customer_subscriptions.view_subscription_detail',
                    'customer_subscriptions.add_customersubscription',
                    'customer_subscriptions.create_subscription',
                    'customer_subscriptions.process_payment',
                    'customer_subscriptions.generate_receipt',
                    'customer_subscriptions.view_payment_history',
                    
                    # Installations - View only
                    'customer_installations.view_customerinstallation',
                    'customer_installations.view_installation_list',
                    'customer_installations.view_installation_detail',
                    
                    # Reports - Limited access
                    'reports.view_daily_collection_report',
                    'reports.view_subscription_expiry_report',
                    
                    # Dashboard - Limited statistics
                    'dashboard.view_customer_statistics',
                    'dashboard.view_financial_statistics',
                ]
            },
            'Technician': {
                'description': 'Can manage installations, handle tickets, and view technical infrastructure',
                'is_system': True,
                'permissions': [
                    # Basic
                    'dashboard.view_dashboard',
                    
                    # Customer Management - View only
                    'customers.view_customer',
                    'customers.view_customer_list',
                    'customers.view_customer_detail',
                    'customers.view_customer_coordinates',
                    
                    # Infrastructure - View only
                    'lcp.view_lcp',
                    'lcp.view_lcp_list',
                    'lcp.view_lcp_detail',
                    'lcp.view_lcp_map',
                    
                    'lcp.view_splitter',
                    'lcp.view_splitter_list',
                    'lcp.view_splitter_detail',
                    
                    'lcp.view_nap',
                    'lcp.view_nap_list',
                    'lcp.view_nap_detail',
                    'lcp.view_nap_availability',
                    
                    # Routers - View and manage
                    'routers.view_router',
                    'routers.view_router_list',
                    'routers.view_router_detail',
                    'routers.add_router',
                    'routers.change_router',
                    'routers.view_router_mac_address',
                    
                    # Installations - Full technical access
                    'customer_installations.view_customerinstallation',
                    'customer_installations.view_installation_list',
                    'customer_installations.view_installation_detail',
                    'customer_installations.add_customerinstallation',
                    'customer_installations.create_installation',
                    'customer_installations.change_customerinstallation',
                    'customer_installations.change_installation_status',
                    'customer_installations.view_installation_technical_details',
                    'customer_installations.manage_nap_assignments',
                    
                    # Tickets - Manage assigned tickets
                    'tickets.view_ticket',
                    'tickets.view_ticket_list',
                    'tickets.view_ticket_detail',
                    'tickets.change_ticket',
                    'tickets.change_ticket_status',
                    'tickets.add_ticket_comment',
                    'tickets.view_ticketcomment',
                    'tickets.add_ticketcomment',
                    
                    # Reports - Technical reports only
                    'reports.view_technician_performance_report',
                    
                    # Dashboard - Infrastructure statistics
                    'dashboard.view_infrastructure_statistics',
                ]
            },
            'Customer Service': {
                'description': 'Can manage customers, create tickets, and view subscriptions',
                'is_system': True,
                'permissions': [
                    # Basic
                    'dashboard.view_dashboard',
                    
                    # Customer Management - Create and edit
                    'customers.view_customer',
                    'customers.view_customer_list',
                    'customers.view_customer_detail',
                    'customers.add_customer',
                    'customers.create_customer',
                    'customers.change_customer',
                    'customers.change_customer_basic',
                    'customers.change_customer_address',
                    
                    # Barangay - View only
                    'barangays.view_barangay',
                    'barangays.view_barangay_list',
                    
                    # Subscription Plans - View only
                    'subscriptions.view_subscriptionplan',
                    'subscriptions.view_subscriptionplan_list',
                    
                    # Customer Subscriptions - View only
                    'customer_subscriptions.view_customersubscription',
                    'customer_subscriptions.view_subscription_list',
                    'customer_subscriptions.view_subscription_detail',
                    'customer_subscriptions.view_payment_history',
                    
                    # Installations - View only
                    'customer_installations.view_customerinstallation',
                    'customer_installations.view_installation_list',
                    'customer_installations.view_installation_detail',
                    
                    # Tickets - Create and manage
                    'tickets.view_ticket',
                    'tickets.view_ticket_list',
                    'tickets.view_ticket_detail',
                    'tickets.add_ticket',
                    'tickets.create_ticket',
                    'tickets.change_ticket',
                    'tickets.assign_ticket',
                    'tickets.change_ticket_status',
                    'tickets.change_ticket_priority',
                    'tickets.add_ticket_comment',
                    'tickets.view_all_tickets',
                    'tickets.view_ticketcomment',
                    'tickets.add_ticketcomment',
                    
                    # Dashboard - Customer statistics
                    'dashboard.view_customer_statistics',
                ]
            },
            'Marketing': {
                'description': 'Can view customer data, reports, and export information for campaigns',
                'is_system': True,
                'permissions': [
                    # Basic
                    'dashboard.view_dashboard',
                    
                    # Customer Management - View and export
                    'customers.view_customer',
                    'customers.view_customer_list',
                    'customers.view_customer_detail',
                    'customers.export_customers',
                    
                    # Barangay - View with statistics
                    'barangays.view_barangay',
                    'barangays.view_barangay_list',
                    'barangays.view_barangay_statistics',
                    
                    # Subscription Plans - View only
                    'subscriptions.view_subscriptionplan',
                    'subscriptions.view_subscriptionplan_list',
                    
                    # Customer Subscriptions - View analytics
                    'customer_subscriptions.view_customersubscription',
                    'customer_subscriptions.view_subscription_list',
                    'customer_subscriptions.export_subscription_data',
                    
                    # Reports - Marketing relevant reports
                    'reports.view_customer_acquisition_report',
                    'reports.view_payment_behavior_report',
                    'reports.view_area_performance_dashboard',
                    'reports.export_business_reports',
                    
                    # Dashboard - All statistics
                    'dashboard.view_customer_statistics',
                    'dashboard.view_infrastructure_statistics',
                    'dashboard.view_financial_statistics',
                    'dashboard.view_system_statistics',
                ]
            },
            'Report Viewer': {
                'description': 'Read-only access to view reports and dashboards',
                'is_system': False,
                'permissions': [
                    # Basic
                    'dashboard.view_dashboard',
                    
                    # Reports - View all reports
                    'reports.view_daily_collection_report',
                    'reports.view_subscription_expiry_report',
                    'reports.view_monthly_revenue_report',
                    'reports.view_ticket_analysis_report',
                    'reports.view_technician_performance_report',
                    'reports.view_customer_acquisition_report',
                    'reports.view_payment_behavior_report',
                    'reports.view_area_performance_dashboard',
                    'reports.view_financial_dashboard',
                    
                    # Dashboard - All statistics
                    'dashboard.view_customer_statistics',
                    'dashboard.view_infrastructure_statistics',
                    'dashboard.view_financial_statistics',
                    'dashboard.view_system_statistics',
                ]
            }
        }
        
        created_roles = []
        updated_roles = []
        
        with transaction.atomic():
            for role_name, config in roles_config.items():
                self.stdout.write(f'\nProcessing role: {role_name}')
                
                try:
                    # Check if role exists
                    try:
                        role = Role.objects.get(name=role_name)
                        # Update existing role
                        role.description = config['description']
                        role.is_system = config['is_system']
                        role.save()
                        
                        # Clear existing permissions
                        role.group.permissions.clear()
                        
                        updated_roles.append(role_name)
                        action = 'Updated'
                    except Role.DoesNotExist:
                        # Create new role
                        role = create_role(
                            name=role_name,
                            description=config['description'],
                            is_system=config['is_system']
                        )
                        created_roles.append(role_name)
                        action = 'Created'
                    
                    # Assign permissions
                    if config['permissions'] == 'all':
                        # Super Admin gets all permissions
                        all_permissions = Permission.objects.all()
                        role.group.permissions.set(all_permissions)
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ {action} with ALL permissions ({all_permissions.count()} total)')
                        )
                    else:
                        # Add specific permissions
                        added_count = 0
                        skipped_count = 0
                        
                        for perm_string in config['permissions']:
                            try:
                                app_label, codename = perm_string.split('.')
                                permission = Permission.objects.get(
                                    content_type__app_label=app_label,
                                    codename=codename
                                )
                                role.add_permission(permission)
                                added_count += 1
                            except (ValueError, Permission.DoesNotExist):
                                skipped_count += 1
                                self.stdout.write(
                                    self.style.WARNING(f'    ⚠ Permission not found: {perm_string}')
                                )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ {action} with {added_count} permissions'
                                f'{f" ({skipped_count} skipped)" if skipped_count > 0 else ""}'
                            )
                        )
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error: {str(e)}')
                    )
        
        # Create role presets for easy assignment
        self.stdout.write('\n\nCreating role permission presets...')
        
        preset_configs = {
            'Basic User Access': {
                'description': 'Minimum permissions for any logged-in user',
                'permissions': [
                    'dashboard.view_dashboard',
                ]
            },
            'Billing Operations': {
                'description': 'Permissions for billing and payment processing',
                'permissions': [
                    'customer_subscriptions.view_customersubscription',
                    'customer_subscriptions.process_payment',
                    'customer_subscriptions.generate_receipt',
                    'customer_subscriptions.view_payment_history',
                ]
            },
            'Technical Operations': {
                'description': 'Permissions for technical field work',
                'permissions': [
                    'customer_installations.create_installation',
                    'customer_installations.change_installation_status',
                    'customer_installations.manage_nap_assignments',
                    'tickets.change_ticket_status',
                ]
            },
            'Customer Management': {
                'description': 'Permissions for managing customer records',
                'permissions': [
                    'customers.add_customer',
                    'customers.change_customer',
                    'customers.view_customer_detail',
                ]
            },
            'Report Access': {
                'description': 'Permissions for viewing reports',
                'permissions': [
                    'reports.view_daily_collection_report',
                    'reports.view_monthly_revenue_report',
                    'reports.view_customer_acquisition_report',
                ]
            }
        }
        
        for preset_name, preset_config in preset_configs.items():
            preset, created = RolePermissionPreset.objects.update_or_create(
                name=preset_name,
                defaults={'description': preset_config['description']}
            )
            
            # Clear and add permissions
            preset.permissions.clear()
            for perm_string in preset_config['permissions']:
                try:
                    app_label, codename = perm_string.split('.')
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename
                    )
                    preset.permissions.add(permission)
                except (ValueError, Permission.DoesNotExist):
                    pass
            
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ {"Created" if created else "Updated"} preset: {preset_name}')
            )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n\nSummary:'
                f'\n  Created roles: {len(created_roles)}'
                f'\n  Updated roles: {len(updated_roles)}'
                f'\n  Total roles: {Role.objects.count()}'
                f'\n  Permission presets: {RolePermissionPreset.objects.count()}'
            )
        )
        
        if created_roles:
            self.stdout.write(f'\nCreated: {", ".join(created_roles)}')
        if updated_roles:
            self.stdout.write(f'Updated: {", ".join(updated_roles)}')
