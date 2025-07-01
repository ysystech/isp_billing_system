#!/bin/bash
# Debug and fix 502 Bad Gateway issue

echo "Debugging ISP Billing System 502 Error"
echo "======================================"

# Check if the socket file exists
echo "1. Checking socket file..."
ssh prod-billing "ls -la /home/ubuntu/isp_billing_system/isp_billing.sock"

# Check Nginx error log
echo -e "\n2. Checking Nginx error logs..."
ssh prod-billing "sudo tail -20 /var/log/nginx/error.log"

# Check permissions
echo -e "\n3. Checking permissions..."
ssh prod-billing "ls -la /home/ubuntu/isp_billing_system/"

# Check if www-data user can access the socket
echo -e "\n4. Checking www-data access..."
ssh prod-billing "sudo -u www-data test -r /home/ubuntu/isp_billing_system/isp_billing.sock && echo 'www-data can read socket' || echo 'www-data cannot read socket'"

# Check Gunicorn detailed logs
echo -e "\n5. Checking Gunicorn logs..."
ssh prod-billing "sudo journalctl -u isp_billing -n 50 --no-pager"

# Let's fix the issue
echo -e "\n6. Applying fixes..."

# Fix 1: Update Gunicorn service to use simpler config
ssh prod-billing "sudo tee /etc/systemd/system/isp_billing.service > /dev/null << 'EOF'
[Unit]
Description=ISP Billing System
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/isp_billing_system
Environment=\"PATH=/home/ubuntu/isp_billing_system/venv/bin\"
EnvironmentFile=/home/ubuntu/isp_billing_system/.env
ExecStart=/home/ubuntu/isp_billing_system/venv/bin/gunicorn \\
    --workers 3 \\
    --bind unix:/home/ubuntu/isp_billing_system/isp_billing.sock \\
    --log-level debug \\
    --access-logfile - \\
    --error-logfile - \\
    isp_billing_system.wsgi:application

[Install]
WantedBy=multi-user.target
EOF"

# Fix 2: Ensure socket directory permissions
ssh prod-billing "sudo chown ubuntu:www-data /home/ubuntu/isp_billing_system"
ssh prod-billing "sudo chmod 755 /home/ubuntu/isp_billing_system"

# Fix 3: Create a test with TCP instead of socket (temporary)
echo -e "\n7. Testing with TCP binding..."
ssh prod-billing "cd /home/ubuntu/isp_billing_system && source venv/bin/activate && timeout 10 gunicorn --bind 127.0.0.1:8000 isp_billing_system.wsgi:application &"
sleep 3
ssh prod-billing "curl -I http://127.0.0.1:8000 2>/dev/null | head -n 1"

# Fix 4: Update Nginx config to be more robust
ssh prod-billing "sudo tee /etc/nginx/sites-available/isp_billing > /dev/null << 'EOF'
server {
    listen 80 default_server;
    server_name 34.124.190.52;
    
    client_max_body_size 10M;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/ubuntu/isp_billing_system/static_root/;
    }
    
    location /media/ {
        alias /home/ubuntu/isp_billing_system/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/isp_billing_system/isp_billing.sock;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
    }
}
EOF"

# Restart services
echo -e "\n8. Restarting services..."
ssh prod-billing "sudo systemctl daemon-reload"
ssh prod-billing "sudo systemctl restart isp_billing"
ssh prod-billing "sudo systemctl restart nginx"

# Wait a moment
sleep 3

# Check status
echo -e "\n9. Checking service status..."
ssh prod-billing "sudo systemctl status isp_billing --no-pager | head -10"
ssh prod-billing "ls -la /home/ubuntu/isp_billing_system/isp_billing.sock"

# Test the site
echo -e "\n10. Testing site..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://34.124.190.52 || echo "000")
echo "HTTP Status: $HTTP_STATUS"

# If still not working, let's try a different approach
if [ "$HTTP_STATUS" != "200" ] && [ "$HTTP_STATUS" != "302" ]; then
    echo -e "\nTrying alternative fix..."
    
    # Use TCP socket instead
    ssh prod-billing "sudo tee /etc/systemd/system/isp_billing.service > /dev/null << 'EOF'
[Unit]
Description=ISP Billing System
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/isp_billing_system
Environment=\"PATH=/home/ubuntu/isp_billing_system/venv/bin\"
EnvironmentFile=/home/ubuntu/isp_billing_system/.env
ExecStart=/home/ubuntu/isp_billing_system/venv/bin/gunicorn \\
    --workers 3 \\
    --bind 127.0.0.1:8000 \\
    --log-level info \\
    isp_billing_system.wsgi:application

[Install]
WantedBy=multi-user.target
EOF"

    # Update Nginx to use TCP
    ssh prod-billing "sudo tee /etc/nginx/sites-available/isp_billing > /dev/null << 'EOF'
server {
    listen 80 default_server;
    server_name 34.124.190.52;
    
    client_max_body_size 10M;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/ubuntu/isp_billing_system/static_root/;
    }
    
    location /media/ {
        alias /home/ubuntu/isp_billing_system/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
    }
}
EOF"

    ssh prod-billing "sudo systemctl daemon-reload"
    ssh prod-billing "sudo systemctl restart isp_billing"
    ssh prod-billing "sudo systemctl restart nginx"
    
    sleep 3
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://34.124.190.52 || echo "000")
    echo -e "\nHTTP Status after TCP fix: $HTTP_STATUS"
fi

echo -e "\nDiagnostics complete. Check http://34.124.190.52"

# Show recent logs
echo -e "\nRecent Gunicorn logs:"
ssh prod-billing "sudo journalctl -u isp_billing -n 20 --no-pager"
