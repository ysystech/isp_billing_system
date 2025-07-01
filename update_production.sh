#!/bin/bash
# FiberBill Update Script
# This script safely updates your production FiberBill deployment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/home/ubuntu/isp_billing_system"
BACKUP_DIR="/home/ubuntu/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${GREEN}=== FiberBill Update Script ===${NC}"
echo "Starting update process at $(date)"

# Function to create backup - COMMENTED OUT FOR TESTING PHASE
create_backup() {
    echo -e "\n${YELLOW}Step 1: Skipping backup (testing phase)...${NC}"
    echo -e "${YELLOW}Note: Backup process is disabled during testing phase${NC}"
    echo -e "${YELLOW}Uncomment the backup code below for production use${NC}"
    
    # # Create backup directory if it doesn't exist
    # mkdir -p "$BACKUP_DIR"
    # 
    # # Backup database
    # echo "- Backing up database..."
    # sudo -u postgres pg_dump isp_billing_system | gzip > "$BACKUP_DIR/pre_update_db_$TIMESTAMP.sql.gz"
    # 
    # # Backup current code
    # echo "- Backing up current code..."
    # tar czf "$BACKUP_DIR/pre_update_code_$TIMESTAMP.tar.gz" -C /home/ubuntu isp_billing_system/ --exclude='venv' --exclude='logs' --exclude='media' --exclude='__pycache__'
    # 
    # # Backup media files
    # echo "- Backing up media files..."
    # tar czf "$BACKUP_DIR/pre_update_media_$TIMESTAMP.tar.gz" -C "$APP_DIR" media/ 2>/dev/null || true
    # 
    # # Backup environment file
    # cp "$APP_DIR/.env" "$BACKUP_DIR/pre_update_env_$TIMESTAMP"
    # 
    # echo -e "${GREEN}✓ Backup completed${NC}"
}
# Function to update code
update_code() {
    echo -e "\n${YELLOW}Step 2: Updating code from Git...${NC}"
    
    cd "$APP_DIR"
    
    # Check for uncommitted changes
    if [[ -n $(git status -s) ]]; then
        echo -e "${RED}Warning: Uncommitted changes detected${NC}"
        echo "Stashing changes..."
        git stash push -m "Auto-stash before update $TIMESTAMP"
    fi
    
    # Fetch and pull latest changes
    echo "- Fetching latest changes..."
    git fetch origin
    
    echo "- Current branch: $(git branch --show-current)"
    echo "- Pulling latest changes..."
    git pull origin main
    
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
    pip install -r requirements/prod-requirements.txt
    
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

# Function to show logs
show_logs() {
    echo -e "\n${YELLOW}Recent application logs:${NC}"
    sudo journalctl -u isp_billing -n 20 --no-pager
}

# Main execution
main() {
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then 
        echo -e "${RED}Please don't run this script as root${NC}"
        exit 1
    fi
    
    # Confirm update
    echo -e "\n${YELLOW}This will update your FiberBill production deployment.${NC}"
    echo -e "${YELLOW}NOTE: Backup is currently disabled for testing phase.${NC}"
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Update cancelled."
        exit 0
    fi
    
    # Run update steps
    create_backup
    update_code
    update_dependencies
    build_frontend
    run_migrations
    collect_static
    restart_services
    verify_deployment
    
    echo -e "\n${GREEN}=== Update completed successfully! ===${NC}"
    echo "Update finished at $(date)"
    
    # Show recent logs
    echo -e "\n${YELLOW}Do you want to see recent application logs? (y/N)${NC}"
    read -p "" -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        show_logs
    fi
}

# Run main function
main
