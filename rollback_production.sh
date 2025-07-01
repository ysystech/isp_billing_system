#!/bin/bash
# FiberBill Rollback Script
# Restore from backup if update fails

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_DIR="/home/ubuntu/backups"
APP_DIR="/home/ubuntu/isp_billing_system"

echo -e "${RED}=== FiberBill Rollback Script ===${NC}"
echo "This will restore your application from a backup"

# List available backups
echo -e "\n${YELLOW}Available backups:${NC}"
ls -lht "$BACKUP_DIR"/pre_update_db_*.sql.gz 2>/dev/null | head -10 || echo "No database backups found"

# Get backup timestamp
echo -e "\n${YELLOW}Enter backup timestamp (YYYYMMDD_HHMMSS):${NC}"
read -p "Timestamp: " TIMESTAMP

# Verify backup files exist
if [ ! -f "$BACKUP_DIR/pre_update_db_$TIMESTAMP.sql.gz" ]; then
    echo -e "${RED}Database backup not found for timestamp: $TIMESTAMP${NC}"
    exit 1
fi

echo -e "\n${RED}WARNING: This will restore the database to the selected backup.${NC}"
echo "Current data will be lost!"
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled."
    exit 0
fi
# Stop services
echo -e "\n${YELLOW}Stopping services...${NC}"
sudo systemctl stop isp_billing
sudo systemctl stop isp_billing_celery 2>/dev/null || true
sudo systemctl stop isp_billing_celerybeat 2>/dev/null || true

# Restore database
echo -e "\n${YELLOW}Restoring database...${NC}"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS isp_billing_system;"
sudo -u postgres psql -c "CREATE DATABASE isp_billing_system;"
gunzip -c "$BACKUP_DIR/pre_update_db_$TIMESTAMP.sql.gz" | sudo -u postgres psql isp_billing_system

# Restore code if backup exists
if [ -f "$BACKUP_DIR/pre_update_code_$TIMESTAMP.tar.gz" ]; then
    echo -e "\n${YELLOW}Restoring code...${NC}"
    cd /home/ubuntu
    tar xzf "$BACKUP_DIR/pre_update_code_$TIMESTAMP.tar.gz"
fi

# Restore environment file
if [ -f "$BACKUP_DIR/pre_update_env_$TIMESTAMP" ]; then
    echo -e "\n${YELLOW}Restoring environment file...${NC}"
    cp "$BACKUP_DIR/pre_update_env_$TIMESTAMP" "$APP_DIR/.env"
fi

# Restore media files if backup exists
if [ -f "$BACKUP_DIR/pre_update_media_$TIMESTAMP.tar.gz" ]; then
    echo -e "\n${YELLOW}Restoring media files...${NC}"
    cd "$APP_DIR"
    tar xzf "$BACKUP_DIR/pre_update_media_$TIMESTAMP.tar.gz"
fi

# Restart services
echo -e "\n${YELLOW}Restarting services...${NC}"
sudo systemctl start isp_billing
sudo systemctl start isp_billing_celery 2>/dev/null || true
sudo systemctl start isp_billing_celerybeat 2>/dev/null || true

# Verify
echo -e "\n${YELLOW}Verifying rollback...${NC}"
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://fiberbill.com)

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Rollback successful! Site is responding.${NC}"
else
    echo -e "${RED}✗ Site returned HTTP $HTTP_STATUS${NC}"
    echo "Check logs: sudo journalctl -u isp_billing -f"
fi

echo -e "\n${GREEN}Rollback completed!${NC}"
