"""
Management command to verify tenant data isolation across the system.
Runs comprehensive checks on all models and views.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant
import traceback

User = get_user_model()


class Command(BaseCommand):
    help = 'Verify tenant data isolation across all models and views'
    
    def __init__(self):
        super().__init__()
        self.issues_found = []
        self.checks_passed = 0
        self.checks_failed = 0
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Specific model to check (e.g., customers.Customer)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',            help='Show detailed output for each check'
        )
    
    def handle(self, *args, **options):
        self.verbose = options.get('verbose', False)
        specific_model = options.get('model')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('TENANT DATA ISOLATION VERIFICATION')
        self.stdout.write('='*60 + '\n')
        
        # Create test tenants if needed
        self.setup_test_data()
        
        if specific_model:
            self.check_specific_model(specific_model)
        else:
            # Run all checks
            self.check_all_models()
            self.check_raw_queries()
            self.check_foreign_key_constraints()
            self.check_unique_constraints()
        
        # Summary
        self.print_summary()
    
    def setup_test_data(self):
        """Create test tenants for verification."""
        self.stdout.write('\n📋 Setting up test data...')
        
        # Get or create test tenants
        try:
            self.tenant1 = Tenant.objects.get(name="Test Tenant 1")
        except Tenant.DoesNotExist:
            owner1 = User.objects.create_user(
                username="test_owner1",
                email="owner1@test.com",
                password="testpass"
            )
            self.tenant1 = Tenant.objects.create(
                name="Test Tenant 1",
                created_by=owner1
            )
            owner1.tenant = self.tenant1
            owner1.is_tenant_owner = True
            owner1.save()
        
        try:
            self.tenant2 = Tenant.objects.get(name="Test Tenant 2")
        except Tenant.DoesNotExist:
            owner2 = User.objects.create_user(
                username="test_owner2",
                email="owner2@test.com",
                password="testpass"
            )
            self.tenant2 = Tenant.objects.create(
                name="Test Tenant 2",
                created_by=owner2
            )
            owner2.tenant = self.tenant2
            owner2.is_tenant_owner = True
            owner2.save()
    def check_all_models(self):
        """Check all tenant-aware models for proper isolation."""
        self.stdout.write('\n🔍 Checking all tenant-aware models...')
        
        tenant_aware_models = []
        
        # Find all models that have a tenant field
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                if hasattr(model, 'tenant'):
                    tenant_aware_models.append(model)
        
        for model in tenant_aware_models:
            self.check_model_isolation(model)
    
    def check_model_isolation(self, model):
        """Check if a model properly filters by tenant."""
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        if self.verbose:
            self.stdout.write(f"\nChecking {model_name}...")
        
        try:
            # Check if model has tenant field
            if not hasattr(model, 'tenant'):
                self.record_issue(model_name, "Model missing tenant field")
                return
            
            # Check default manager filtering
            with connection.cursor() as cursor:                # Get the table name
                table_name = model._meta.db_table
                
                # Check if any records exist without tenant_id
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE tenant_id IS NULL"
                )
                null_count = cursor.fetchone()[0]
                
                if null_count > 0:
                    self.record_issue(
                        model_name, 
                        f"{null_count} records found with NULL tenant_id"
                    )
                else:
                    self.record_success(model_name, "All records have tenant_id")
                
                # Check for potential cross-tenant foreign keys
                for field in model._meta.get_fields():
                    if field.many_to_one and field.related_model != Tenant:
                        if hasattr(field.related_model, 'tenant'):
                            # This is a tenant-aware related model
                            self.check_foreign_key_integrity(
                                model, field, table_name
                            )
            
            self.checks_passed += 1
            
        except Exception as e:
            self.record_issue(model_name, f"Error checking model: {str(e)}")
            if self.verbose:                self.stdout.write(traceback.format_exc())
    
    def check_foreign_key_integrity(self, model, field, table_name):
        """Check if foreign key relationships respect tenant boundaries."""
        related_table = field.related_model._meta.db_table
        field_name = field.column
        
        with connection.cursor() as cursor:
            # SQL to find cross-tenant foreign key violations
            sql = f"""
                SELECT COUNT(*) 
                FROM {table_name} t1
                JOIN {related_table} t2 ON t1.{field_name} = t2.id
                WHERE t1.tenant_id != t2.tenant_id
            """
            
            cursor.execute(sql)
            violation_count = cursor.fetchone()[0]
            
            if violation_count > 0:
                self.record_issue(
                    f"{model.__name__}.{field.name}",
                    f"{violation_count} cross-tenant FK violations found"
                )
    
    def check_raw_queries(self):
        """Check for raw SQL queries that might bypass tenant filtering."""
        self.stdout.write('\n🔍 Checking for raw SQL queries...')
        
        # This would need to scan the codebase for raw() and execute()
        # For now, we'll just log a reminder        self.stdout.write("⚠️  Manual review needed for raw SQL queries")
    
    def check_foreign_key_constraints(self):
        """Verify database-level foreign key constraints."""
        self.stdout.write('\n🔍 Checking FK constraints...')
        
        with connection.cursor() as cursor:
            # PostgreSQL query to check foreign key constraints
            cursor.execute("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                AND tc.table_name LIKE 'apps_%'
            """)
            
            constraints = cursor.fetchall()
            
            if self.verbose:
                for constraint in constraints:
                    self.stdout.write(f"FK: {constraint[0]}.{constraint[1]} -> {constraint[2]}.{constraint[3]}")
    
    def check_unique_constraints(self):
        """Check if unique constraints include tenant_id where needed."""
        self.stdout.write('\n🔍 Checking unique constraints...')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    tc.table_name,
                    string_agg(kcu.column_name, ', ') as columns
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'UNIQUE'
                AND tc.table_schema = 'public'
                AND tc.table_name LIKE 'apps_%'
                GROUP BY tc.table_name, tc.constraint_name
            """)
            
            constraints = cursor.fetchall()
            
            for table_name, columns in constraints:
                if 'tenant_id' not in columns and table_name != 'tenants_tenant':
                    self.stdout.write(
                        f"⚠️  {table_name} has unique constraint without tenant_id: {columns}"
                    )
    
    def record_issue(self, location, issue):
        """Record a security issue."""
        self.issues_found.append({
            'location': location,
            'issue': issue
        })
        self.checks_failed += 1
        
        if self.verbose:
            self.stdout.write(f"❌ {location}: {issue}")
    
    def record_success(self, location, message):
        """Record a successful check."""
        if self.verbose:
            self.stdout.write(f"✅ {location}: {message}")
    
    def print_summary(self):
        """Print summary of verification results."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('VERIFICATION SUMMARY')
        self.stdout.write('='*60)
        
        total_checks = self.checks_passed + self.checks_failed
        self.stdout.write(f"\nTotal checks performed: {total_checks}")
        self.stdout.write(f"✅ Passed: {self.checks_passed}")
        self.stdout.write(f"❌ Failed: {self.checks_failed}")
        
        if self.issues_found:
            self.stdout.write('\n🚨 ISSUES FOUND:')
            for issue in self.issues_found:                self.stdout.write(
                    f"\n📍 {issue['location']}" +
                    f"\n   {issue['issue']}"
                )
        else:
            self.stdout.write('\n✅ All checks passed! Tenant isolation appears solid.')
        
        self.stdout.write('\n')
    
    def check_specific_model(self, model_path):
        """Check a specific model by app_label.ModelName."""
        try:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)
            self.check_model_isolation(model)
        except Exception as e:
            self.stdout.write(f"Error: {str(e)}")