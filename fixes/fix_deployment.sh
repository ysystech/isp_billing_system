#!/bin/bash

echo "Fixing FiberBill deployment issues..."

# Fix nginx configuration to use correct socket file
echo "1. Fixing nginx configuration..."
sudo sed -i 's/isp_billing\.sock/gunicorn.sock/g' /etc/nginx/sites-available/fiberbill
sudo nginx -t && sudo systemctl reload nginx

# Check if socket exists and has correct permissions
echo "2. Checking socket file..."
if [ -S /home/ubuntu/isp_billing_system/gunicorn.sock ]; then
    echo "Socket exists. Setting permissions..."
    sudo chmod 666 /home/ubuntu/isp_billing_system/gunicorn.sock
else
    echo "Socket doesn't exist. Restarting service..."
    sudo systemctl restart isp_billing
    sleep 5
    if [ -S /home/ubuntu/isp_billing_system/gunicorn.sock ]; then
        sudo chmod 666 /home/ubuntu/isp_billing_system/gunicorn.sock
    fi
fi

# Install cron for automated backups
echo "3. Installing cron for automated backups..."
sudo apt-get update
sudo apt-get install -y cron

# Set up the backup cron job
echo "4. Setting up automated backups..."
BACKUP_SCRIPT="/home/ubuntu/backup_isp_billing.sh"

# Create backup script
cat > "$BACKUP_SCRIPT" << 'EOF'
#!/bin/bash
# ISP Billing System Backup Script
BACKUP_DIR="/home/ubuntu/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="isp_billing_system"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup database
sudo -u postgres pg_dump "$DB_NAME" | gzip > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

# Backup media files
tar czf "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" -C /home/ubuntu/isp_billing_system media/ 2>/dev/null || true

# Backup environment file
cp /home/ubuntu/isp_billing_system/.env "$BACKUP_DIR/env_backup_$TIMESTAMP"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "env_backup_*" -mtime +7 -delete

echo "Backup completed at $(date)"
EOF

chmod +x "$BACKUP_SCRIPT"

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * $BACKUP_SCRIPT >> /home/ubuntu/backup.log 2>&1") | crontab -

echo "5. Testing the website..."
sleep 3
curl -I https://fiberbill.com | head -n 1

echo ""
echo "Deployment fixes completed!"
echo ""
echo "Summary:"
echo "- Nginx configuration fixed to use correct socket"
echo "- Socket permissions updated"
echo "- Cron installed for automated backups"
echo "- Daily backups scheduled at 2 AM"
echo ""
echo "Your admin credentials:"
echo "Username: admin"
echo "Password: 722436Aa!"
echo ""
echo "Access your site at: https://fiberbill.com"
