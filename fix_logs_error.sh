#!/bin/bash

# Fix the logs directory issue

echo "=== Fixing FiberBill Logs Directory Issue ==="

# Create the logs directory
echo "1. Creating logs directory..."
sudo mkdir -p /home/ubuntu/isp_billing_system/logs
sudo chown ubuntu:ubuntu /home/ubuntu/isp_billing_system/logs
sudo chmod 755 /home/ubuntu/isp_billing_system/logs

# Create empty log files if needed
echo "2. Creating log files..."
sudo touch /home/ubuntu/isp_billing_system/logs/gunicorn.log
sudo touch /home/ubuntu/isp_billing_system/logs/gunicorn-error.log
sudo chown ubuntu:ubuntu /home/ubuntu/isp_billing_system/logs/*.log
sudo chmod 644 /home/ubuntu/isp_billing_system/logs/*.log

# Restart the service
echo "3. Restarting isp_billing service..."
sudo systemctl restart isp_billing

# Wait a moment
sleep 3

# Check status
echo "4. Checking service status..."
sudo systemctl status isp_billing --no-pager | head -20

# Test the site
echo "5. Testing site response..."
curl -I https://fiberbill.com | head -10

echo "=== Fix complete ==="
