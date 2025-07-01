#!/bin/bash
# FiberBill Quick Update Script
# For minor updates without database migrations

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== FiberBill Quick Update ===${NC}"
echo "This script does a quick code update without migrations"

cd /home/ubuntu/isp_billing_system

# Pull latest code
echo -e "\n${YELLOW}Pulling latest code...${NC}"
git pull origin main

# Restart services
echo -e "\n${YELLOW}Restarting services...${NC}"
sudo systemctl restart isp_billing

# If using Celery
if systemctl is-active --quiet isp_billing_celery; then
    sudo systemctl restart isp_billing_celery
fi

if systemctl is-active --quiet isp_billing_celerybeat; then
    sudo systemctl restart isp_billing_celerybeat
fi

# Test the site
echo -e "\n${YELLOW}Testing site...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://fiberbill.com)

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Site is up (HTTP $HTTP_STATUS)${NC}"
else
    echo -e "${RED}✗ Site returned HTTP $HTTP_STATUS${NC}"
fi

echo -e "\n${GREEN}Quick update completed!${NC}"
