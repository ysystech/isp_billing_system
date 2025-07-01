#!/bin/bash
# ISP Billing System - Troubleshooting Script

echo "ISP Billing System - Troubleshooting 502 Error"
echo "=============================================="
echo ""

# Function to run commands on server
run_on_server() {
    ssh prod-billing "$1"
}

# Check service status
echo "1. Checking service status..."
echo "----------------------------"
run_on_server "sudo systemctl status isp_billing --no-pager | head -20"
echo ""

echo "2. Checking if socket file exists..."
echo "-----------------------------------"
run_on_server "ls -la /home/ubuntu/isp_billing_system/isp_billing.sock 2>&1 || echo 'Socket file not found'"
echo ""

echo "3. Checking Gunicorn error logs..."
echo "----------------------------------"
run_on_server "sudo journalctl -u isp_billing -n 50 --no-pager"
echo ""

echo "4. Checking Nginx error log..."
echo "------------------------------"
run_on_server "sudo tail -20 /var/log/nginx/error.log"
echo ""

echo "5. Checking if Python app can start..."
echo "--------------------------------------"
run_on_server "cd /home/ubuntu/isp_billing_system && source venv/bin/activate && python manage.py check"
echo ""

echo "6. Checking .env file exists..."
echo "-------------------------------"
run_on_server "ls -la /home/ubuntu/isp_billing_system/.env"
echo ""

echo "7. Testing database connection..."
echo "---------------------------------"
run_on_server "cd /home/ubuntu/isp_billing_system && source venv/bin/activate && python manage.py dbshell << EOF
\conninfo
\q
EOF"
echo ""

echo "8. Checking directory permissions..."
echo "-----------------------------------"
run_on_server "ls -la /home/ubuntu/isp_billing_system/ | grep -E '(logs|media|static_root)'"
echo ""

echo "9. Quick fix attempt - Restart services..."
echo "-----------------------------------------"
run_on_server "sudo systemctl restart isp_billing"
sleep 3
run_on_server "sudo systemctl status isp_billing --no-pager | head -10"
