# FiberBill Production Update Guide

This guide explains how to safely update your FiberBill production deployment.

## Update Scripts

### 1. Full Update Script (`update_production.sh`)
Use this for major updates that may include:
- Database migrations
- Dependency changes
- Frontend build changes
- Static file updates

**Usage:**
```bash
# On your local machine
cd /Users/aldesabido/pers/isp_billing_system

# First, push your changes to Git
git add .
git commit -m "Your update message"
git push origin main

# Copy the update script to server
scp update_production.sh prod-billing:/home/ubuntu/

# SSH into server and run update
ssh prod-billing
./update_production.sh
```

**What it does:**
1. Creates a full backup (database, code, media files)
2. Pulls latest code from Git
3. Updates Python dependencies
4. Builds frontend assets (if npm is installed)
5. Runs database migrations
6. Collects static files
7. Restarts all services
8. Verifies the deployment

### 2. Quick Update Script (`quick_update.sh`)
Use this for minor updates like:
- Template changes
- Small code fixes
- No database changes
- No new dependencies

**Usage:**
```bash
# Copy to server (first time only)
scp quick_update.sh prod-billing:/home/ubuntu/

# SSH and run
ssh prod-billing
./quick_update.sh
```

**What it does:**
1. Pulls latest code
2. Restarts services
3. Verifies site is working
### 3. Rollback Script (`rollback_production.sh`)
Use this if an update fails and you need to restore:

**Usage:**
```bash
# Copy to server (first time only)
scp rollback_production.sh prod-billing:/home/ubuntu/

# SSH and run
ssh prod-billing
./rollback_production.sh
```

**What it does:**
1. Lists available backups
2. Restores database from backup
3. Restores code (if available)
4. Restores environment and media files
5. Restarts services

## Best Practices

### Before Updating
1. **Test locally first** - Make sure your changes work in development
2. **Check migrations** - Run `python manage.py makemigrations` locally
3. **Commit all changes** - Push to Git before updating production
4. **Notify users** - If expecting downtime

### Update Process
1. **Use full update** for first deployment after development
2. **Use quick update** for small fixes during the day
3. **Always check logs** after update: `sudo journalctl -u isp_billing -f`
4. **Test critical features** after update

### If Something Goes Wrong
1. **Check logs first:**
   ```bash
   sudo journalctl -u isp_billing -n 50
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Quick fixes:**
   ```bash
   # Restart services
   sudo systemctl restart isp_billing
   sudo systemctl restart nginx
   
   # Check service status
   sudo systemctl status isp_billing
   ```

3. **Use rollback script** if needed

## Common Issues

### 502 Bad Gateway
- Usually means Gunicorn isn't running
- Check: `sudo systemctl status isp_billing`
- Fix: `sudo systemctl restart isp_billing`

### Static files not loading
- Run: `cd /home/ubuntu/isp_billing_system && source venv/bin/activate && python manage.py collectstatic --noinput`

### Database connection errors
- Check PostgreSQL: `sudo systemctl status postgresql`
- Check credentials in `.env` file

## Monitoring

### Check Services
```bash
# All at once
sudo systemctl status isp_billing nginx postgresql redis

# Application logs
sudo journalctl -u isp_billing -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Check Disk Space
```bash
df -h
du -sh /home/ubuntu/backups/
```

### Clean Old Backups
```bash
# Keep only last 30 days
find /home/ubuntu/backups/ -name "*.gz" -mtime +30 -delete
```

## Security Notes

1. **Always backup** before major updates
2. **Test rollback** procedure occasionally
3. **Monitor disk space** - backups can fill up disk
4. **Keep dependencies updated** - run full update monthly
5. **Check SSL certificate** - auto-renews but verify: `sudo certbot certificates`

## Support

If you encounter issues:
1. Check the logs first
2. Try the quick fixes
3. Use rollback if needed
4. Document the issue for debugging

Remember: The full update script creates backups automatically, so you can always rollback if needed!
