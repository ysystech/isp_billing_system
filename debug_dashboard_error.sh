#!/bin/bash

# Debug authenticated user issue

echo "=== Debugging Authenticated User Error ==="
echo "========================================="

# 1. Check recent Python errors
echo -e "\n1. Recent Python errors in logs..."
sudo journalctl -u isp_billing --since "10 minutes ago" | grep -E "Traceback|ERROR|Error|Exception" -A 5 -B 2

# 2. Test the redirect
echo -e "\n2. Testing authenticated redirect..."
# This will show us where the redirect is going
curl -I -L https://fiberbill.com/dashboard/ 2>/dev/null | head -20

# 3. Check if dashboard app is properly configured
echo -e "\n3. Checking Django URLs..."
cd /home/ubuntu/isp_billing_system
source venv/bin/activate
python manage.py show_urls | grep dashboard | head -10

# 4. Check for import errors in dashboard
echo -e "\n4. Testing dashboard imports..."
python -c "
try:
    from apps.dashboard.views import home
    print('✅ Dashboard views import OK')
except Exception as e:
    print(f'❌ Dashboard import error: {e}')
"

# 5. Check current code
echo -e "\n5. Current web/views.py redirect line..."
grep -n "redirect.*dashboard" /home/ubuntu/isp_billing_system/apps/web/views.py

# 6. Try to access dashboard directly in shell
echo -e "\n6. Testing dashboard view in Django shell..."
python manage.py shell << EOF
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.dashboard.views import home as dashboard_home

try:
    # Get a user
    User = get_user_model()
    user = User.objects.first()
    if user:
        print(f"Testing with user: {user}")
        # Create a fake request
        factory = RequestFactory()
        request = factory.get('/dashboard/')
        request.user = user
        # Try to call the view
        response = dashboard_home(request)
        print(f"✅ Dashboard view returned: {response.status_code if hasattr(response, 'status_code') else 'OK'}")
    else:
        print("❌ No users found in database")
except Exception as e:
    print(f"❌ Dashboard error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
EOF

echo -e "\n=== Debug complete ==="
