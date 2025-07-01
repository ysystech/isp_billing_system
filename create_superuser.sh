#!/bin/bash
# Create superuser for ISP Billing System

echo "Creating superuser for ISP Billing System"
echo "=========================================="

# Create superuser script
ssh prod-billing "cd /home/ubuntu/isp_billing_system && cat > create_superuser.py << 'EOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'isp_billing_system.settings_production')
django.setup()

from apps.users.models import CustomUser
from apps.tenants.models import Tenant

# Create first tenant if it doesn't exist
tenant, created = Tenant.objects.get_or_create(
    name='Main ISP Company',
    defaults={'is_active': True}
)

if created:
    print(f'Created tenant: {tenant.name}')
else:
    print(f'Using existing tenant: {tenant.name}')

# Create superuser
username = 'admin'
email = 'admin@ispbilling.com'
password = 'Admin123!@#'

if CustomUser.objects.filter(username=username).exists():
    print(f'User {username} already exists')
    user = CustomUser.objects.get(username=username)
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.is_tenant_owner = True
    user.save()
    print(f'Updated password for {username}')
else:
    user = CustomUser.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        tenant=tenant,
        is_tenant_owner=True
    )
    print(f'Created superuser: {username}')

# Set the tenant creator
if not hasattr(tenant, 'created_by') or tenant.created_by is None:
    tenant.created_by = user
    tenant.save()
    print(f'Set {username} as tenant owner')

print('\\nLogin credentials:')
print(f'URL: http://34.124.190.52/admin/')
print(f'Username: {username}')
print(f'Password: {password}')
print('\\nIMPORTANT: Change this password after first login!')
EOF"

# Run the script
ssh prod-billing "cd /home/ubuntu/isp_billing_system && source venv/bin/activate && python create_superuser.py"

# Clean up
ssh prod-billing "rm /home/ubuntu/isp_billing_system/create_superuser.py"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Access your ISP Billing System:"
echo "Main URL: http://34.124.190.52/"
echo "Admin URL: http://34.124.190.52/admin/"
echo ""
echo "Login Credentials:"
echo "Username: admin"
echo "Password: Admin123!@#"
echo ""
echo "IMPORTANT: Change the password after first login!"
echo ""
echo "To create additional users or ISP companies:"
echo "1. Login to admin panel"
echo "2. Go to Tenants section to create new ISP companies"
echo "3. Go to Users section to create users for each tenant"
echo ""

# Also check if we can access the site now
echo "Testing site access..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L http://34.124.190.52/accounts/login/ || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✓ Site is accessible!"
else
    echo "Site returned HTTP $HTTP_STATUS"
    echo "Checking services..."
    ssh prod-billing "sudo systemctl status isp_billing --no-pager | head -5"
fi
