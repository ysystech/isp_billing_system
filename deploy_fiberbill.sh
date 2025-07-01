#!/bin/bash
# ISP Billing System - Production Deployment with Domain (fiberbill.com)
# Target: Ubuntu 24.04 on Google Compute Engine
# Complete automated deployment with SSL support

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="fiberbill.com"
SERVER_IP="34.124.190.52"
SERVER_NAME="prod-billing"
APP_DIR="/home/ubuntu/isp_billing_system"
PROJECT_DIR="/Users/aldesabido/pers/isp_billing_system"
PYTHON_VERSION="3.12"
ADMIN_EMAIL="admin@fiberbill.com"

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

print_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
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

# Check if domain is pointing to server
print_info "Checking domain DNS configuration..."
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
    print_status "Domain $DOMAIN is correctly pointing to $SERVER_IP ✓"
else
    print_warning "Domain $DOMAIN is pointing to $DOMAIN_IP instead of $SERVER_IP"
    print_warning "Please update your DNS A record to point to $SERVER_IP"
    echo "Do you want to continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

echo ""
echo "============================================"
echo "ISP Billing System - Production Deployment"
echo "============================================"
echo "Domain: $DOMAIN"
echo "Server: $SERVER_IP"
echo "Python: $PYTHON_VERSION"
echo "App Directory: $APP_DIR"
echo ""

# Generate credentials
print_status "Generating secure credentials..."
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-16)

# Clean up any existing installation
print_status "Cleaning up any existing installation..."
run_on_server "sudo systemctl stop isp_billing isp_billing_celery isp_billing_celerybeat nginx || true"
run_on_server "sudo rm -rf $APP_DIR.backup"
run_on_server "[ -d $APP_DIR ] && mv $APP_DIR $APP_DIR.backup || true"

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
    libpq-dev \
    certbot python3-certbot-nginx"

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
run_on_server "sudo sed -i 's/^bind .*/bind 127.0.0.1/' /etc/redis/redis.conf"
run_on_server "sudo systemctl start redis-server"
run_on_server "sudo systemctl enable redis-server"

print_status "Step 5: Creating application directory structure..."
run_on_server "mkdir -p $APP_DIR"
run_on_server "mkdir -p $APP_DIR/logs"
run_on_server "mkdir -p $APP_DIR/media"
run_on_server "mkdir -p $APP_DIR/static_root"

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
    --exclude='db.sqlite3' \
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
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,$SERVER_IP,localhost

# Database
DATABASE_URL=postgres://isp_billing_system:$POSTGRES_PASSWORD@localhost:5432/isp_billing_system

# Redis
REDIS_URL=redis://:$REDIS_PASSWORD@localhost:6379/0

# Email
DEFAULT_FROM_EMAIL=noreply@$DOMAIN
SERVER_EMAIL=server@$DOMAIN

# Media files
USE_S3_MEDIA=False

# Security (will be enabled after SSL)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Domain settings
FRONTEND_ADDRESS=https://$DOMAIN
CORS_ALLOWED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
CSRF_COOKIE_DOMAIN=.$DOMAIN
SESSION_COOKIE_DOMAIN=.$DOMAIN
EOF"

print_status "Step 12: Running database migrations..."
run_on_server "cd $APP_DIR && source venv/bin/activate && python manage.py migrate --noinput"

print_status "Step 13: Collecting static files..."
run_on_server "cd $APP_DIR && source venv/bin/activate && python manage.py collectstatic --noinput"

print_status "Step 14: Creating Gunicorn service..."
run_on_server "sudo tee /etc/systemd/system/isp_billing.service > /dev/null << 'EOF'
[Unit]
Description=FiberBill Gunicorn Service
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
    --bind unix:$APP_DIR/gunicorn.sock \
    --error-logfile $APP_DIR/logs/gunicorn-error.log \
    --access-logfile $APP_DIR/logs/gunicorn-access.log \
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
Description=FiberBill Celery Worker
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
    --pidfile=$APP_DIR/celery.pid'
ExecStop=/bin/sh -c 'kill \$(cat $APP_DIR/celery.pid)'
ExecReload=/bin/sh -c 'kill -HUP \$(cat $APP_DIR/celery.pid)'
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

print_status "Step 16: Creating Celery Beat service..."
run_on_server "sudo tee /etc/systemd/system/isp_billing_celerybeat.service > /dev/null << 'EOF'
[Unit]
Description=FiberBill Celery Beat
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

print_status "Step 17: Configuring Nginx for domain..."
run_on_server "sudo tee /etc/nginx/sites-available/fiberbill > /dev/null << 'EOF'
# Redirect www to non-www
server {
    listen 80;
    listen [::]:80;
    server_name www.$DOMAIN;
    return 301 \$scheme://$DOMAIN\$request_uri;
}

# Main server block
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection \"1; mode=block\";
    add_header Referrer-Policy \"strict-origin-when-cross-origin\";
    
    client_max_body_size 20M;
    
    access_log /var/log/nginx/fiberbill_access.log;
    error_log /var/log/nginx/fiberbill_error.log;

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
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/gunicorn.sock;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
    }
}
EOF"

print_status "Step 18: Setting permissions..."
# Fix permissions for www-data access
run_on_server "sudo usermod -a -G ubuntu www-data"
run_on_server "sudo chmod 755 /home/ubuntu"
run_on_server "sudo chown -R ubuntu:www-data $APP_DIR"
run_on_server "sudo chmod -R 755 $APP_DIR"
run_on_server "sudo chmod -R 775 $APP_DIR/media $APP_DIR/static_root $APP_DIR/logs"
run_on_server "sudo chmod 640 $APP_DIR/.env"

print_status "Step 19: Enabling services..."
# Enable Nginx site
run_on_server "sudo ln -sf /etc/nginx/sites-available/fiberbill /etc/nginx/sites-enabled/"
run_on_server "sudo rm -f /etc/nginx/sites-enabled/default"
run_on_server "sudo rm -f /etc/nginx/sites-enabled/isp_billing"
run_on_server "sudo nginx -t"

# Reload systemd and enable services
run_on_server "sudo systemctl daemon-reload"
run_on_server "sudo systemctl enable postgresql redis-server nginx"
run_on_server "sudo systemctl enable isp_billing isp_billing_celery isp_billing_celerybeat"

# Start services
print_status "Step 20: Starting services..."
run_on_server "sudo systemctl restart postgresql redis-server"
run_on_server "sudo systemctl restart isp_billing"
run_on_server "sudo systemctl restart isp_billing_celery"
run_on_server "sudo systemctl restart isp_billing_celerybeat"
run_on_server "sudo systemctl restart nginx"

print_status "Step 21: Creating initial superuser..."
run_on_server "cd $APP_DIR && cat > create_superuser.py << 'EOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'isp_billing_system.settings_production')
django.setup()

from apps.users.models import CustomUser
from apps.tenants.models import Tenant

# Create first tenant
tenant, created = Tenant.objects.get_or_create(
    name='FiberBill Admin',
    defaults={'is_active': True}
)

# Create superuser
username = 'admin'
email = '$ADMIN_EMAIL'
password = 'FiberBill2025!'

if CustomUser.objects.filter(username=username).exists():
    user = CustomUser.objects.get(username=username)
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.is_tenant_owner = True
    user.save()
    print(f'Updated password for {username}')
else:
    user = CustomUser.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        tenant=tenant,
        is_tenant_owner=True
    )
    print(f'Created superuser: {username}')

if not hasattr(tenant, 'created_by') or tenant.created_by is None:
    tenant.created_by = user
    tenant.save()
EOF"

run_on_server "cd $APP_DIR && source venv/bin/activate && python create_superuser.py"
run_on_server "rm $APP_DIR/create_superuser.py"

sleep 5  # Give services time to start

print_status "Step 22: Setting up SSL with Let's Encrypt..."
if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
    print_status "Obtaining SSL certificate for $DOMAIN..."
    run_on_server "sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m $ADMIN_EMAIL --redirect"
    
    # Update Django settings for HTTPS
    print_status "Updating Django settings for HTTPS..."
    run_on_server "sed -i 's/SECURE_SSL_REDIRECT=False/SECURE_SSL_REDIRECT=True/' $APP_DIR/.env"
    run_on_server "sed -i 's/SESSION_COOKIE_SECURE=False/SESSION_COOKIE_SECURE=True/' $APP_DIR/.env"
    run_on_server "sed -i 's/CSRF_COOKIE_SECURE=False/CSRF_COOKIE_SECURE=True/' $APP_DIR/.env"
    run_on_server "sudo systemctl restart isp_billing"
    
    print_status "SSL certificate installed successfully!"
    SSL_ENABLED="yes"
else
    print_warning "Skipping SSL setup - domain not pointing to server yet"
    SSL_ENABLED="no"
fi

print_status "Step 23: Setting up log rotation..."
run_on_server "sudo tee /etc/logrotate.d/fiberbill > /dev/null << 'EOF'
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
    endscript
}
EOF"

print_status "Step 24: Setting up automated backups..."
run_on_server "mkdir -p $APP_DIR/backups"
run_on_server "cat > $APP_DIR/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=\"$APP_DIR/backups\"
DATE=\$(date +%Y%m%d_%H%M%S)

# Backup database
PGPASSWORD=\"$POSTGRES_PASSWORD\" pg_dump -U isp_billing_system -h localhost isp_billing_system > \$BACKUP_DIR/db_\$DATE.sql

# Backup media files
tar czf \$BACKUP_DIR/media_\$DATE.tar.gz -C $APP_DIR media/

# Keep only last 7 days
find \$BACKUP_DIR -name \"*.sql\" -mtime +7 -delete
find \$BACKUP_DIR -name \"*.tar.gz\" -mtime +7 -delete
EOF"

run_on_server "chmod +x $APP_DIR/backup.sh"
run_on_server "(crontab -l 2>/dev/null; echo \"0 2 * * * $APP_DIR/backup.sh\") | crontab -"

# Final verification
print_status "Step 25: Verifying deployment..."
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

# Save credentials
cat > deployment_credentials.txt << EOF
FiberBill - Deployment Credentials
==================================
Generated: $(date)

Domain Configuration:
- Primary Domain: https://$DOMAIN
- Server IP: $SERVER_IP
- SSL Enabled: $SSL_ENABLED

Admin Access:
- Admin URL: https://$DOMAIN/admin/
- Username: admin
- Password: FiberBill2025!
- Email: $ADMIN_EMAIL

Database:
- PostgreSQL Database: isp_billing_system
- PostgreSQL User: isp_billing_system
- PostgreSQL Password: $POSTGRES_PASSWORD

Redis:
- Redis Password: $REDIS_PASSWORD

Django:
- Secret Key: $SECRET_KEY

Application Paths:
- App Directory: $APP_DIR
- Logs: $APP_DIR/logs/
- Backups: $APP_DIR/backups/

Service Management:
- Restart app: sudo systemctl restart isp_billing
- View logs: sudo journalctl -u isp_billing -f
- Check status: sudo systemctl status isp_billing

SSL Certificate Renewal:
- Auto-renewal is configured via certbot
- Manual renewal: sudo certbot renew

Backup Management:
- Automatic daily backups at 2 AM
- Manual backup: $APP_DIR/backup.sh
- Backup location: $APP_DIR/backups/

IMPORTANT: Keep this file secure!
EOF

chmod 600 deployment_credentials.txt

echo ""
echo "============================================"
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}DEPLOYMENT SUCCESSFUL!${NC}"
else
    echo -e "${YELLOW}DEPLOYMENT COMPLETED WITH WARNINGS${NC}"
fi
echo "============================================"
echo ""
if [ "$SSL_ENABLED" = "yes" ]; then
    echo "Your FiberBill application is live at:"
    echo -e "${GREEN}https://$DOMAIN${NC}"
    echo ""
    echo "Admin panel:"
    echo -e "${GREEN}https://$DOMAIN/admin/${NC}"
else
    echo "Your FiberBill application is live at:"
    echo -e "${YELLOW}http://$DOMAIN${NC}"
    echo ""
    echo "Admin panel:"
    echo -e "${YELLOW}http://$DOMAIN/admin/${NC}"
    echo ""
    echo "To enable SSL later, run:"
    echo "ssh $SERVER_NAME"
    echo "sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi
echo ""
echo "Login credentials:"
echo "Username: admin"
echo "Password: FiberBill2025!"
echo ""
echo "First steps:"
echo "1. Change the admin password"
echo "2. Create your first ISP company"
echo "3. Configure email settings"
echo "4. Set up payment gateway (if needed)"
echo ""
echo "Credentials saved to: deployment_credentials.txt"
echo ""

print_status "Deployment complete! Welcome to FiberBill!"
