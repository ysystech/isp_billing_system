#!/bin/bash

# Quick fix script for common 500 errors

echo "=== FiberBill Quick Fix Script ==="
echo "=================================="

# 1. Restart services
echo -e "\n1. Restarting services..."
sudo systemctl restart isp_billing
sudo systemctl restart isp_billing_celery
sudo systemctl restart isp_billing_celerybeat
sudo systemctl restart nginx

sleep 3

# 2. Check if services are running
echo -e "\n2. Checking service status..."
sudo systemctl status isp_billing --no-pager | grep "Active:"

# 3. Fix permissions
echo -e "\n3. Fixing file permissions..."
sudo chown -R ubuntu:ubuntu /home/ubuntu/isp_billing_system
sudo chmod -R 755 /home/ubuntu/isp_billing_system/staticfiles
sudo chmod -R 755 /home/ubuntu/isp_billing_system/media

# 4. Collect static files
echo -e "\n4. Collecting static files..."
cd /home/ubuntu/isp_billing_system
source venv/bin/activate
python manage.py collectstatic --noinput

# 5. Check for migration issues
echo -e "\n5. Running migrations..."
python manage.py migrate

# 6. Quick health check
echo -e "\n6. Testing site..."
curl -I https://fiberbill.com

echo -e "\n=== Fix complete ==="
echo "Check if the site is working now"
