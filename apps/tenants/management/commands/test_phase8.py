"""
Management command to test Phase 8 implementation.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

from apps.tenants.models import Tenant
from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.subscriptions.models import SubscriptionPlan
from apps.customer_installations.models import CustomerInstallation
from apps.customer_subscriptions.models import CustomerSubscription
from apps.audit_logs.models import AuditLogEntry
from apps.customer_subscriptions.tasks import (
    update_expired_subscriptions_for_tenant,
    update_expired_subscriptions_all_tenants,
    send_expiration_reminders_for_tenant
)


class Command(BaseCommand):
    help = 'Test Phase 8 tenant-aware background tasks implementation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup-only',
            action='store_true',
            help='Only cleanup test data without running tests',
        )
        parser.add_argument(
            '--keep-data',
            action='store_true', 
            help='Keep test data after running tests',
        )

    def handle(self, *args, **options):
        if options['cleanup_only']:
            self.cleanup_test_data()
            return

        self.stdout.write(self.style.WARNING('='*60))
        self.stdout.write(self.style.WARNING('PHASE 8 TEST - Tenant-Aware Background Tasks'))
        self.stdout.write(self.style.WARNING('='*60))
        try:
            with transaction.atomic():
                self.test_signal_handlers()
                self.test_task_isolation()
                self.test_all_tenants_execution()
                self.test_inactive_tenant_handling()
                self.test_audit_logging()
                
                self.stdout.write(self.style.SUCCESS('\nAll tests completed successfully!'))
                
                # Rollback to avoid keeping test data
                if not options.get('keep_data'):
                    self.stdout.write('\nRolling back test data...')
                    raise Exception("Rollback test data")
                    
        except Exception as e:
            if str(e) == "Rollback test data":
                self.stdout.write(self.style.SUCCESS('Test data rolled back'))
            else:
                self.stdout.write(self.style.ERROR(f'Test failed: {e}'))
                raise

    def cleanup_test_data(self):
        """Clean up any existing test data"""
        self.stdout.write('\nCleaning up test data...')
        # First delete users to avoid ProtectedError
        deleted_users = CustomUser.objects.filter(
            tenant__name__startswith="Phase8Test"
        ).delete()[0]
        self.stdout.write(f'  Deleted {deleted_users} test users')
        
        # Now delete tenants (will cascade delete other data)
        count = Tenant.objects.filter(name__startswith="Phase8Test").delete()[0]
        self.stdout.write(f'  Deleted {count} test tenants and related data')

    def test_signal_handlers(self):
        """Test that signals create system users"""
        self.stdout.write('\n1. Testing signal handlers...')
        
        # Create test tenant
        tenant = Tenant.objects.create(name="Phase8Test Signal", is_active=True)        
        # Check system user was created
        sys_user = CustomUser.objects.filter(username=f"system_{tenant.id}").first()
        
        if sys_user:
            self.stdout.write(self.style.SUCCESS('  ✓ System user created by signal'))
            self.stdout.write(f'    Username: {sys_user.username}')
            self.stdout.write(f'    Tenant: {sys_user.tenant.name}')
        else:
            self.stdout.write(self.style.ERROR('  ✗ System user NOT created'))

    def test_task_isolation(self):
        """Test that tasks only process their tenant's data"""
        self.stdout.write('\n2. Testing task isolation...')
        
        # Create two tenants with test data
        tenant1 = Tenant.objects.create(name="Phase8Test ISP 1", is_active=True)
        tenant2 = Tenant.objects.create(name="Phase8Test ISP 2", is_active=True)
        
        # Create test data for both tenants
        for i, tenant in enumerate([tenant1, tenant2], 1):
            # Create barangay
            barangay = Barangay.objects.create(
                tenant=tenant,
                name=f"Test Barangay {i}",
                code=f"TB{i}",
                description="Test barangay for Phase 8"
            )
            
            # Create subscription plan
            plan = SubscriptionPlan.objects.create(
                tenant=tenant,
                name=f"Plan T{i}",
                speed=10 * i,
                price=500 * i,
                day_count=30
            )            
            # Create customer
            customer = Customer.objects.create(
                tenant=tenant,
                first_name=f"Test{i}",
                last_name=f"User{i}",
                email=f"test{i}@tenant{i}.com",
                phone_primary=f"0900000000{i}",
                street_address=f"Test Street {i}",
                barangay=barangay,
                status=Customer.ACTIVE
            )
            
            # Create a test user to be the technician
            technician = CustomUser.objects.create_user(
                username=f"tech{i}",
                email=f"tech{i}@tenant{i}.com",
                password="testpass123",
                tenant=tenant
            )
            
            # Create installation
            installation = CustomerInstallation.objects.create(
                tenant=tenant,
                customer=customer,
                installation_date=timezone.now().date(),
                installation_technician=technician,
                status='ACTIVE'
            )
            
            # Create expired subscription
            CustomerSubscription.objects.create(
                tenant=tenant,
                customer_installation=installation,
                subscription_plan=plan,
                subscription_type='one_month',
                amount=plan.price,
                start_date=timezone.now() - timedelta(days=60),
                end_date=timezone.now() - timedelta(days=1),
                days_added=30,
                status='ACTIVE',
                created_by=technician
            )        
        # Run task for tenant 1 only
        result = update_expired_subscriptions_for_tenant(tenant1.id)
        self.stdout.write(f'  Task result: {result}')
        
        # Check isolation
        t1_expired = CustomerSubscription.objects.filter(
            tenant=tenant1, status='EXPIRED'
        ).count()
        t2_expired = CustomerSubscription.objects.filter(
            tenant=tenant2, status='EXPIRED'
        ).count()
        
        if t1_expired == 1 and t2_expired == 0:
            self.stdout.write(self.style.SUCCESS('  ✓ Task isolation working correctly'))
        else:
            self.stdout.write(self.style.ERROR('  ✗ Task isolation FAILED'))

    def test_all_tenants_execution(self):
        """Test execution for all tenants"""
        self.stdout.write('\n3. Testing all-tenants execution...')
        
        # Get test tenants
        tenants = Tenant.objects.filter(name__startswith="Phase8Test ISP")
        
        if tenants.count() < 2:
            self.stdout.write(self.style.ERROR('  Not enough test tenants'))
            return
        
        # Reset all subscriptions to ACTIVE
        CustomerSubscription.objects.filter(
            tenant__in=tenants
        ).update(status='ACTIVE')
        
        # Run for all tenants
        results = update_expired_subscriptions_all_tenants()
        
        self.stdout.write(f'  Processed {len(results)} tenants')
        for tenant_id, result in results.items():
            self.stdout.write(f'  - Tenant {tenant_id}: {result}')
        
        if len(results) >= 2:
            self.stdout.write(self.style.SUCCESS('  ✓ Multi-tenant execution working'))
        else:
            self.stdout.write(self.style.ERROR('  ✗ Multi-tenant execution FAILED'))
    def test_inactive_tenant_handling(self):
        """Test that inactive tenants are skipped"""
        self.stdout.write('\n4. Testing inactive tenant handling...')
        
        # Make one tenant inactive
        tenant = Tenant.objects.filter(name="Phase8Test ISP 2").first()
        if tenant:
            tenant.is_active = False
            tenant.save()
            
            # Run all tenants task
            results = update_expired_subscriptions_all_tenants()
            
            if tenant.id not in results:
                self.stdout.write(self.style.SUCCESS('  ✓ Inactive tenant correctly skipped'))
            else:
                self.stdout.write(self.style.ERROR('  ✗ Inactive tenant NOT skipped'))

    def test_audit_logging(self):
        """Test audit logging in background tasks"""
        self.stdout.write('\n5. Testing audit logging...')
        
        initial_count = AuditLogEntry.objects.count()
        
        # Run a task that modifies data
        tenant = Tenant.objects.filter(name__startswith="Phase8Test").first()
        if tenant:
            # Reset a subscription
            sub = CustomerSubscription.objects.filter(
                tenant=tenant, status='EXPIRED'
            ).first()
            if sub:
                sub.status = 'ACTIVE'
                sub.save()
            
            # Run task
            update_expired_subscriptions_for_tenant(tenant.id)
            
            # Check audit logs
            new_count = AuditLogEntry.objects.count()
            if new_count > initial_count:
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ Audit logs created: {new_count - initial_count}'
                ))
                
                latest = AuditLogEntry.objects.order_by('-id').first()
                self.stdout.write(f'  - User: {latest.log_entry.user.username}')
                self.stdout.write(f'  - Tenant: {latest.tenant.name}')
                self.stdout.write(f'  - User Agent: {latest.user_agent}')
            else:
                self.stdout.write(self.style.WARNING('  ⚠ No audit logs created'))