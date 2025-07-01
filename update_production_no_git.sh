#!/bin/bash
# FiberBill Update Script (No Git Version)
# This script updates your production deployment using file sync

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/home/ubuntu/isp_billing_system"
TEMP_DIR="/tmp/isp_update_$(date +%s)"

echo -e "${GREEN}=== FiberBill Update Script (File Sync) ===${NC}"
echo "Starting update process at $(date)"

# Function to sync files from local
sync_files() {
    echo -e "\n${YELLOW}Step 1: Please run this command on your LOCAL machine:${NC}"
    echo -e "${GREEN}cd /Users/aldesabido/pers/isp_billing_system${NC}"
    echo -e "${GREEN}rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.env' --exclude 'media' --exclude 'staticfiles' --exclude 'logs' --exclude '*.pyc' --exclude '.git' . prod-billing:$TEMP_DIR/${NC}"
    echo ""
    echo "Press Enter after running the rsync command on your local machine..."
    read
    
    # Check if files were synced
    if [ ! -d "$TEMP_DIR" ]; then
        echo -e "${RED}Error: No files found in $TEMP_DIR${NC}"
        echo "Please run the rsync command on your local machine first."
        exit 1
    fi
    
    echo -e "${GREEN}✓ Files received${NC}"
}

# Function to update code
update_code() {
    echo -e "\n${YELLOW}Step 2: Updating application files...${NC}"
    
    # Copy new files to app directory (excluding configs and data)
    rsync -av --exclude '.env' --exclude 'media' --exclude 'staticfiles' --exclude 'logs' --exclude 'venv' "$TEMP_DIR/" "$APP_DIR/"
    
    # Clean up temp directory
    rm -rf "$TEMP_DIR"
    
    echo -e "${GREEN}✓ Code updated${NC}"
}
# Function to update dependencies
update_dependencies() {
    echo -e "\n${YELLOW}Step 3: Updating dependencies...${NC}"
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Update Python packages
    echo "- Updating Python packages..."
    pip install --upgrade pip
    pip install -r requirements/production.txt
    
    echo -e "${GREEN}✓ Dependencies updated${NC}"
}

# Function to build frontend assets
build_frontend() {
    echo -e "\n${YELLOW}Step 4: Building frontend assets...${NC}"
    
    cd "$APP_DIR"
    
    # Check if npm is installed
    if command -v npm &> /dev/null; then
        echo "- Installing npm packages..."
        npm install
        
        echo "- Building production assets..."
        npm run build
    else
        echo -e "${YELLOW}⚠ npm not found, skipping frontend build${NC}"
    fi
    
    echo -e "${GREEN}✓ Frontend build completed${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "\n${YELLOW}Step 5: Running database migrations...${NC}"
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Check for pending migrations
    echo "- Checking for pending migrations..."
    python manage.py showmigrations --plan | grep "\[ \]" || true
    
    # Run migrations
    echo "- Applying migrations..."
    python manage.py migrate --noinput
    
    echo -e "${GREEN}✓ Migrations completed${NC}"
}

# Function to collect static files
collect_static() {
    echo -e "\n${YELLOW}Step 6: Collecting static files...${NC}"
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    python manage.py collectstatic --noinput
    
    echo -e "${GREEN}✓ Static files collected${NC}"
}

# Function to restart services
restart_services() {
    echo -e "\n${YELLOW}Step 7: Restarting services...${NC}"
    
    # Restart Gunicorn
    echo "- Restarting Gunicorn..."
    sudo systemctl restart isp_billing
    
    # Restart Celery if it's running
    if systemctl is-active --quiet isp_billing_celery; then
        echo "- Restarting Celery..."
        sudo systemctl restart isp_billing_celery
    fi
    
    # Restart Celery Beat if it's running
    if systemctl is-active --quiet isp_billing_celerybeat; then
        echo "- Restarting Celery Beat..."
        sudo systemctl restart isp_billing_celerybeat
    fi
    
    # Reload Nginx
    echo "- Reloading Nginx..."
    sudo nginx -t && sudo systemctl reload nginx
    
    echo -e "${GREEN}✓ Services restarted${NC}"
}

# Function to verify deployment
verify_deployment() {
    echo -e "\n${YELLOW}Step 8: Verifying deployment...${NC}"
    
    # Check if services are running
    echo "- Checking service status..."
    
    if systemctl is-active --quiet isp_billing; then
        echo -e "  ${GREEN}✓ Gunicorn is running${NC}"
    else
        echo -e "  ${RED}✗ Gunicorn is not running${NC}"
    fi
    
    if systemctl is-active --quiet nginx; then
        echo -e "  ${GREEN}✓ Nginx is running${NC}"
    else
        echo -e "  ${RED}✗ Nginx is not running${NC}"
    fi
    
    # Test the website
    echo "- Testing website response..."
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://fiberbill.com)
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo -e "  ${GREEN}✓ Website is responding (HTTP $HTTP_STATUS)${NC}"
    else
        echo -e "  ${RED}✗ Website returned HTTP $HTTP_STATUS${NC}"
    fi
}

# Main execution
main() {
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then 
        echo -e "${RED}Please don't run this script as root${NC}"
        exit 1
    fi
    
    # Confirm update
    echo -e "\n${YELLOW}This will update your FiberBill production deployment using file sync.${NC}"
    echo -e "${YELLOW}NOTE: Backup is currently disabled for testing phase.${NC}"
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Update cancelled."
        exit 0
    fi
    
    # Run update steps
    sync_files
    update_code
    update_dependencies
    build_frontend
    run_migrations
    collect_static
    restart_services
    verify_deployment
    
    echo -e "\n${GREEN}=== Update completed successfully! ===${NC}"
    echo "Update finished at $(date)"
}

# Run main function
main
