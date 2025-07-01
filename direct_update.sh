#!/bin/bash
# Direct update script for FiberBill
# Run this from your LOCAL machine to update production

set -e

echo "=== FiberBill Direct Update Script ==="
echo "This will sync your local files to production"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "Error: This script must be run from the project root directory"
    echo "Please cd to /Users/aldesabido/pers/isp_billing_system first"
    exit 1
fi

echo "Step 1: Syncing files to production..."
rsync -avz --progress \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '.env' \
    --exclude 'media' \
    --exclude 'staticfiles' \
    --exclude 'logs' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude '.DS_Store' \
    --exclude 'db.sqlite3' \
    --exclude 'node_modules' \
    --exclude 'deployment_credentials.txt' \
    . prod-billing:/home/ubuntu/isp_billing_system/

echo ""
echo "Step 2: Running update commands on server..."
ssh prod-billing << 'EOF'
cd /home/ubuntu/isp_billing_system
source venv/bin/activate

echo "- Running migrations..."
python manage.py migrate --noinput

echo "- Collecting static files..."
python manage.py collectstatic --noinput

echo "- Restarting services..."
sudo systemctl restart isp_billing

echo "- Checking status..."
sleep 3
if systemctl is-active --quiet isp_billing; then
    echo "✓ Services running successfully"
else
    echo "✗ Service failed to start"
    sudo journalctl -u isp_billing -n 20
fi

# Test the site
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://fiberbill.com)
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✓ Website is responding (HTTP $HTTP_STATUS)"
else
    echo "✗ Website returned HTTP $HTTP_STATUS"
fi
EOF

echo ""
echo "=== Update completed! ==="
echo "Check your site at: https://fiberbill.com"
