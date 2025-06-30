import os
import re
from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = 'Audit views for missing permission decorators'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\nAuditing views for permission decorators...\n'))
        
        # Get all apps
        for app_config in apps.get_app_configs():
            if app_config.path.startswith('/Users/aldesabido/pers/isp_billing_system/apps/'):
                app_name = app_config.name.split('.')[-1]
                views_path = os.path.join(app_config.path, 'views.py')
                
                if os.path.exists(views_path):
                    self.audit_views_file(app_name, views_path)

    def audit_views_file(self, app_name, views_path):
        with open(views_path, 'r') as f:
            content = f.read()
        
        # Find all function definitions
        func_pattern = r'def\s+(\w+)\s*\(.*?\):'
        functions = re.findall(func_pattern, content)
        
        if not functions:
            return
        
        self.stdout.write(f'\n{self.style.SUCCESS(app_name.upper())} ({views_path})')
        self.stdout.write('-' * 80)
        
        # Check each function for decorators
        for func_name in functions:
            # Skip private functions
            if func_name.startswith('_'):
                continue
            
            # Find the function and its decorators
            func_match = re.search(
                rf'(@\w+(?:\(.*?\))?\s*)*\ndef\s+{func_name}\s*\(', 
                content, 
                re.MULTILINE | re.DOTALL
            )
            
            if func_match:
                decorators = func_match.group(0)
                has_login = '@login_required' in decorators
                has_tenant = '@tenant_required' in decorators
                has_permission = '@permission_required' in decorators
                
                # Check if it's likely a view (has request parameter)
                func_def_match = re.search(
                    rf'def\s+{func_name}\s*\((.*?)\):', 
                    content, 
                    re.MULTILINE | re.DOTALL
                )
                if func_def_match and 'request' in func_def_match.group(1):
                    status_parts = []
                    
                    if has_login:
                        status_parts.append(self.style.SUCCESS('✓ login'))
                    else:
                        status_parts.append(self.style.ERROR('✗ login'))
                    
                    if has_tenant:
                        status_parts.append(self.style.SUCCESS('✓ tenant'))
                    else:
                        status_parts.append(self.style.ERROR('✗ tenant'))
                    
                    if has_permission:
                        # Extract permission name
                        perm_match = re.search(
                            rf'@permission_required\([\'"]([^\'\"]+)[\'\"].*?\)\s*(?:@\w+.*?\s*)*def\s+{func_name}',
                            content,
                            re.MULTILINE | re.DOTALL
                        )
                        if perm_match:
                            perm_name = perm_match.group(1)
                            status_parts.append(self.style.SUCCESS(f'✓ perm: {perm_name}'))
                        else:
                            status_parts.append(self.style.SUCCESS('✓ permission'))
                    else:
                        status_parts.append(self.style.WARNING('⚠ NO PERMISSION'))
                    
                    status = ' | '.join(status_parts)
                    self.stdout.write(f'  {func_name:<30} {status}')
