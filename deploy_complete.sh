#!/bin/bash
# ISP Billing System - Complete Automated Deployment to GCE
# This script handles the entire deployment process including all dependencies and fixes
# Target: Ubuntu 24.04 on Google Compute Engine

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="34.124.190.52"
SERVER_NAME="prod-billing"
APP_DIR="/home/ubuntu/isp_billing_system"
PROJECT_DIR="/Users/aldesabido/pers/isp_billing_system"
PYTHON_VERSION="3.12"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Function to run commands on server
run_on_server() {
    ssh -o StrictHostKeyChecking=no $SERVER_NAME "$1"
}

# Function to copy files to server
copy_to_server() {
    scp -o StrictHostKeyChecking=no -r "$1" $SERVER_NAME:"$2"
}

# Check SSH connection
print_status "Testing SSH connection to $SERVER_IP..."
if ! ssh -o ConnectTimeout=5 $SERVER_NAME "echo 'SSH connection successful'"; then
    print_error "Cannot connect to server. Please check your SSH configuration."
    exit 1
fi

echo ""
echo "=========================================="
echo "ISP Billing System - Automated Deployment"
echo "=========================================="
echo "Server: $SERVER_IP"
echo "Python: $PYTHON_VERSION"
echo "App Directory: $APP_DIR"
echo ""

# Generate credentials
print_status "Generating secure credentials..."
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-16)

# We'll generate Django secret key on the server after Python is installed

print_status "Step 1: Updating system and fixing locale..."
run_on_server "sudo apt update && sudo apt upgrade -y"
run_on_server "sudo locale-gen en_US.UTF-8 && sudo update-locale LANG=en_US.UTF-8"

print_status "Step 2: Installing system dependencies..."
# Core dependencies
run_on_server "sudo apt install -y \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev python3-pip \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    git curl wget \
    build-essential \
    libpq-dev"

# WeasyPrint dependencies (for PDF generation)
print_status "Installing WeasyPrint dependencies..."
run_on_server "sudo apt install -y \
    libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev \
    libcairo2 libcairo2-dev \
    python3-cffi python3-brotli \
    libpango1.0-dev libharfbuzz-dev libpangoft2-1.0-0"

# Install Node.js
print_status "Installing Node.js..."
run_on_server "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
run_on_server "sudo apt install -y nodejs"

print_status "Step 3: Setting up PostgreSQL..."
run_on_server "sudo systemctl start postgresql"
run_on_server "sudo systemctl enable postgresql"

# Create database and user
run_on_server "sudo -u postgres psql << EOF
-- Drop existing database and user if they exist
DROP DATABASE IF EXISTS isp_billing_system;
DROP USER IF EXISTS isp_billing_system;

-- Create new database and user
CREATE DATABASE isp_billing_system;
CREATE USER isp_billing_system WITH PASSWORD '$POSTGRES_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE isp_billing_system TO isp_billing_system;
ALTER DATABASE isp_billing_system OWNER TO isp_billing_system;

-- Grant necessary permissions
GRANT CREATE ON SCHEMA public TO isp_billing_system;
EOF"

print_status "Step 4: Configuring Redis with password..."
run_on_server "sudo systemctl stop redis-server"
run_on_server "sudo sed -i 's/^# requirepass .*/requirepass $REDIS_PASSWORD/' /etc/redis/redis.conf"
run_on_server "sudo systemctl start redis-server"
run_on_server "sudo systemctl enable redis-server"

print_status "Step 5: Creating application directory..."
run_on_server "mkdir -p $APP_DIR"
run_on_server "mkdir -p $APP_DIR/logs"
run_on_server "mkdir -p $APP_DIR/media"

print_status "Step 6: Preparing and copying project files..."
# Create a clean copy of the project
TEMP_DIR=$(mktemp -d)
print_status "Creating clean project copy..."

# Use rsync to copy only necessary files
rsync -av \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='media' \
    --exclude='static_root' \
    --exclude='.env' \
    --exclude='*.log' \
    --exclude='*.sqlite3' \
    --exclude='.kamal' \
    --exclude='deployment_credentials.txt' \
    --exclude='.DS_Store' \
    "$PROJECT_DIR/" "$TEMP_DIR/"

# Create tarball
cd "$TEMP_DIR"
tar czf /tmp/isp_billing_system.tar.gz .
cd - > /dev/null

# Copy and extract on server
print_status "Uploading project files to server..."
copy_to_server /tmp/isp_billing_system.tar.gz /tmp/
run_on_server "cd $APP_DIR && tar xzf /tmp/isp_billing_system.tar.gz && rm /tmp/isp_billing_system.tar.gz"

# Clean up
rm -rf "$TEMP_DIR"
rm -f /tmp/isp_billing_system.tar.gz

print_status "Step 7: Setting up Python virtual environment..."
run_on_server "cd $APP_DIR && python${PYTHON_VERSION} -m venv venv"
run_on_server "cd $APP_DIR && source venv/bin/activate && pip install --upgrade pip setuptools wheel"

print_status "Step 8: Installing Python dependencies..."
run_on_server "cd $APP_DIR && source venv/bin/activate && pip install -r requirements/requirements.txt"
run_on_server "cd $APP_DIR && source venv/bin/activate && pip install -r requirements/prod-requirements.txt"
run_on_server "cd $APP_DIR && source venv/bin/activate && pip install gunicorn gevent"

print_status "Step 9: Building frontend assets..."
run_on_server "cd $APP_DIR && npm install"
run_on_server "cd $APP_DIR && npm run build"

print_status "Step 10: Generating Django secret key..."
SECRET_KEY=$(run_on_server "cd $APP_DIR && source venv/bin/activate && python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'")

print_status "Step 11: Creating production configuration..."
run_on_server "cat > $APP_DIR/.env << EOF
# Django Settings
SECRET_KEY=$SECRET_KEY
DEBUG=False
DJANGO_SETTINGS_MODULE=isp_billing_system.settings_production
ALLOWED_HOSTS=$SERVER_IP

# Database
DATABASE_URL=postgres://isp_billing_system:$POSTGRES_PASSWORD@localhost:5432/isp_billing_system

# Redis
REDIS_URL=redis://:$REDIS_PASSWORD@localhost:6379/0

# Email (configure these later)
DEFAULT_FROM_EMAIL=admin@$SERVER_IP
SERVER_EMAIL=noreply@$SERVER_IP

# Media files
USE_S3_MEDIA=False

# Security
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
EOF"

print_status "Step 12: Running database migrations..."
run_on_server "cd $APP_DIR && source venv/bin/activate && python manage.py migrate --noinput"

print_status "Step 13: Collecting static files..."
run_on_server "cd $APP_DIR && source venv/bin/activate && python manage.py collectstatic --noinput"

print_status "Step 14: Creating Gunicorn service..."
run_on_server "sudo tee /etc/systemd/system/isp_billing.service > /dev/null << 'EOF'
[Unit]
Description=ISP Billing System Gunicorn Service
After=network.target postgresql.service

[Service]
Type=notify
User=ubuntu
Group=www-data
WorkingDirectory=$APP_DIR
Environment=\"PATH=$APP_DIR/venv/bin\"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn \
    --workers 3 \
    --worker-class gevent \
    --worker-connections 1000 \
    --bind unix:$APP_DIR/isp_billing.sock \
    --access-logfile $APP_DIR/logs/access.log \
    --error-logfile $APP_DIR/logs/error.log \
    --capture-output \
    --enable-stdio-inheritance \
    isp_billing_system.wsgi:application

ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF"

print_status "Step 15: Creating Celery service..."
run_on_server "sudo tee /etc/systemd/system/isp_billing_celery.service > /dev/null << 'EOF'
[Unit]
Description=ISP Billing System Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=forking
User=ubuntu
Group=www-data
WorkingDirectory=$APP_DIR
Environment=\"PATH=$APP_DIR/venv/bin\"
EnvironmentFile=$APP_DIR/.env
ExecStart=/bin/sh -c '${APP_DIR}/venv/bin/celery -A isp_billing_system worker \
    --loglevel=INFO \
    --logfile=$APP_DIR/logs/celery.log \
    --detach \
    --pidfile=/tmp/celery.pid'
ExecStop=/bin/sh -c 'kill \$(cat /tmp/celery.pid)'
ExecReload=/bin/sh -c 'kill -HUP \$(cat /tmp/celery.pid)'
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

print_status "Step 16: Creating Celery Beat service..."
run_on_server "sudo tee /etc/systemd/system/isp_billing_celerybeat.service > /dev/null << 'EOF'
[Unit]
Description=ISP Billing System Celery Beat
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
Group=www-data
WorkingDirectory=$APP_DIR
Environment=\"PATH=$APP_DIR/venv/bin\"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/celery -A isp_billing_system beat \
    --loglevel=INFO \
    --logfile=$APP_DIR/logs/celerybeat.log
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

print_status "Step 17: Configuring Nginx..."
run_on_server "sudo tee /etc/nginx/sites-available/isp_billing > /dev/null << 'EOF'
upstream isp_billing_app {
    server unix:$APP_DIR/isp_billing.sock fail_timeout=0;
}

server {
    listen 80 default_server;
    server_name $SERVER_IP;
    
    client_max_body_size 20M;
    
    access_log /var/log/nginx/isp_billing_access.log;
    error_log /var/log/nginx/isp_billing_error.log;

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }
    
    location /static/ {
        alias $APP_DIR/static_root/;
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }
    
    location /media/ {
        alias $APP_DIR/media/;
        expires 7d;
    }

    location / {
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
        proxy_buffering off;
        
        if (!-f \$request_filename) {
            proxy_pass http://isp_billing_app;
            break;
        }
    }
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection \"1; mode=block\";
}
EOF"

print_status "Step 18: Setting up log rotation..."
run_on_server "sudo tee /etc/logrotate.d/isp_billing > /dev/null << 'EOF'
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu www-data
    sharedscripts
    postrotate
        systemctl reload isp_billing >/dev/null 2>&1 || true
        systemctl reload isp_billing_celery >/dev/null 2>&1 || true
    endscript
}
EOF"

print_status "Step 19: Setting permissions..."
run_on_server "sudo chown -R ubuntu:www-data $APP_DIR"
run_on_server "sudo chmod -R 755 $APP_DIR"
run_on_server "sudo chmod -R 775 $APP_DIR/media $APP_DIR/static_root $APP_DIR/logs"
run_on_server "sudo chmod 600 $APP_DIR/.env"

print_status "Step 20: Enabling and starting services..."
# Enable Nginx site
run_on_server "sudo ln -sf /etc/nginx/sites-available/isp_billing /etc/nginx/sites-enabled/"
run_on_server "sudo rm -f /etc/nginx/sites-enabled/default"
run_on_server "sudo nginx -t"

# Reload systemd and enable services
run_on_server "sudo systemctl daemon-reload"
run_on_server "sudo systemctl enable postgresql redis-server nginx"
run_on_server "sudo systemctl enable isp_billing isp_billing_celery isp_billing_celerybeat"

# Start services
run_on_server "sudo systemctl restart postgresql redis-server"
run_on_server "sudo systemctl restart isp_billing"
run_on_server "sudo systemctl restart isp_billing_celery"
run_on_server "sudo systemctl restart isp_billing_celerybeat"
run_on_server "sudo systemctl restart nginx"

print_status "Step 21: Verifying deployment..."
sleep 5  # Give services time to start

# Check if services are running
SERVICES=("isp_billing" "isp_billing_celery" "isp_billing_celerybeat" "nginx" "postgresql" "redis-server")
ALL_GOOD=true

for service in "${SERVICES[@]}"; do
    if run_on_server "sudo systemctl is-active --quiet $service"; then
        print_status "$service is running ✓"
    else
        print_error "$service is not running ✗"
        ALL_GOOD=false
    fi
done

# Test HTTP response
print_status "Testing HTTP response..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ]; then
    print_status "Web server is responding (HTTP $HTTP_STATUS) ✓"
else
    print_warning "Web server returned HTTP $HTTP_STATUS"
    ALL_GOOD=false
fi

# Save credentials
cat > deployment_credentials.txt << EOF
ISP Billing System - Deployment Credentials
===========================================
Generated: $(date)

Server Information:
- IP Address: $SERVER_IP
- SSH Access: ssh $SERVER_NAME
- Application URL: http://$SERVER_IP

Database Credentials:
- PostgreSQL Database: isp_billing_system
- PostgreSQL User: isp_billing_system
- PostgreSQL Password: $POSTGRES_PASSWORD

Redis:
- Redis Password: $REDIS_PASSWORD

Django:
- Secret Key: $SECRET_KEY
- Admin URL: http://$SERVER_IP/admin/

Application Paths:
- App Directory: $APP_DIR
- Virtual Environment: $APP_DIR/venv
- Logs: $APP_DIR/logs/
- Static Files: $APP_DIR/static_root/
- Media Files: $APP_DIR/media/

Service Management:
- View status: sudo systemctl status isp_billing
- Restart app: sudo systemctl restart isp_billing
- View logs: sudo journalctl -u isp_billing -f

Useful Commands:
- Create superuser: cd $APP_DIR && source venv/bin/activate && python manage.py createsuperuser
- Django shell: cd $APP_DIR && source venv/bin/activate && python manage.py shell
- Database shell: cd $APP_DIR && source venv/bin/activate && python manage.py dbshell
- Collect static: cd $APP_DIR && source venv/bin/activate && python manage.py collectstatic --noinput
EOF

chmod 600 deployment_credentials.txt

echo ""
echo "=========================================="
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}DEPLOYMENT SUCCESSFUL!${NC}"
else
    echo -e "${YELLOW}DEPLOYMENT COMPLETED WITH WARNINGS${NC}"
fi
echo "=========================================="
echo ""
echo "Application URL: http://$SERVER_IP"
echo ""
echo "Next Steps:"
echo "1. Create a superuser account:"
echo "   ssh $SERVER_NAME"
echo "   cd $APP_DIR && source venv/bin/activate"
echo "   python manage.py createsuperuser"
echo ""
echo "2. Access the admin panel:"
echo "   http://$SERVER_IP/admin/"
echo ""
echo "3. Register your first ISP company:"
echo "   http://$SERVER_IP/accounts/signup/"
echo ""
echo "Credentials saved to: deployment_credentials.txt"
echo "Keep this file secure!"
echo ""

if [ "$ALL_GOOD" = false ]; then
    echo "Some services may need attention. Check logs with:"
    echo "  ssh $SERVER_NAME"
    echo "  sudo journalctl -u isp_billing -n 50"
fi

print_status "Deployment script completed!"
