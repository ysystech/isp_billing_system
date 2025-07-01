#!/bin/bash

# Verify FiberBill is working after update

echo "=== Verifying FiberBill Deployment ==="
echo "====================================="

# 1. Check HTTP response
echo -e "\n1. Testing HTTPS response..."
response=$(curl -s -o /dev/null -w "%{http_code}" https://fiberbill.com)
echo "HTTP Response Code: $response"

if [ "$response" = "200" ]; then
    echo "✅ Site is responding correctly!"
else
    echo "❌ Site returned error code: $response"
fi

# 2. Check if landing page content is loading
echo -e "\n2. Checking landing page content..."
curl -s https://fiberbill.com | grep -q "FiberBill" && echo "✅ Landing page content found" || echo "❌ Landing page content not found"

# 3. Check static files
echo -e "\n3. Testing static files..."
static_response=$(curl -s -o /dev/null -w "%{http_code}" https://fiberbill.com/static/css/landing.css)
echo "Static file response: $static_response"

# 4. Check all services
echo -e "\n4. Service status..."
for service in isp_billing isp_billing_celery isp_billing_celerybeat nginx postgresql redis; do
    status=$(sudo systemctl is-active $service)
    if [ "$status" = "active" ]; then
        echo "✅ $service: $status"
    else
        echo "❌ $service: $status"
    fi
done

# 5. Check recent errors
echo -e "\n5. Checking for recent errors..."
error_count=$(sudo journalctl -u isp_billing --since "5 minutes ago" | grep -c "ERROR\|CRITICAL")
echo "Errors in last 5 minutes: $error_count"

if [ "$error_count" -gt 0 ]; then
    echo "Recent errors found:"
    sudo journalctl -u isp_billing --since "5 minutes ago" | grep -A 2 "ERROR\|CRITICAL" | head -20
fi

echo -e "\n=== Verification complete ==="
