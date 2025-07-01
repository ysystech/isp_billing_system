#!/bin/bash

# Debug script for FiberBill production issues

echo "=== FiberBill Production Debug Script ==="
echo "========================================"

# Check service status
echo -e "\n1. Checking service status..."
sudo systemctl status isp_billing --no-pager | head -20

# Check recent logs
echo -e "\n2. Recent application logs..."
sudo journalctl -u isp_billing -n 50 --no-pager | tail -30

# Check Nginx errors
echo -e "\n3. Recent Nginx errors..."
sudo tail -20 /var/log/nginx/error.log

# Check if Gunicorn is running
echo -e "\n4. Checking Gunicorn processes..."
ps aux | grep gunicorn | grep -v grep

# Check database connection
echo -e "\n5. Checking PostgreSQL status..."
sudo systemctl status postgresql --no-pager | head -10

# Check disk space
echo -e "\n6. Checking disk space..."
df -h | grep -E "^/dev|Filesystem"

# Check Python errors in detail
echo -e "\n7. Checking for Python errors in logs..."
sudo journalctl -u isp_billing --since "1 hour ago" | grep -E "ERROR|CRITICAL|Traceback|500" | tail -20

# Check environment file
echo -e "\n8. Checking if .env file exists..."
if [ -f /home/ubuntu/isp_billing_system/.env ]; then
    echo ".env file exists"
    echo "Checking for required variables..."
    grep -E "SECRET_KEY|DATABASE_URL|DEBUG" /home/ubuntu/isp_billing_system/.env | sed 's/=.*/=***/'
else
    echo "WARNING: .env file not found!"
fi

# Check if migrations are up to date
echo -e "\n9. Checking migration status..."
cd /home/ubuntu/isp_billing_system
source venv/bin/activate
python manage.py showmigrations | tail -20

echo -e "\n=== Debug complete ==="
echo "Look for errors above, especially in the logs section"
