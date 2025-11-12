# 🚀 Quick Deployment Guide - Smart Weight Bridge System

## ⚡ One-Command Deployment

### Prerequisites
- Ubuntu 20.04+ or CentOS 8+ server
- Root/sudo access
- Internet connection

### Step 1: Download and Deploy
```bash
# Copy the deployment script to your server
scp deploy_package.sh root@your-server:/tmp/

# SSH into your server
ssh root@your-server

# Run the deployment script
cd /tmp
chmod +x deploy_package.sh
sudo ./deploy_package.sh
```

### Step 2: Access Your System
After deployment completes, access the system at:
- **URL**: `http://your-server-ip`
- **Admin Login**: `admin` / `admin123`
- **Operator Login**: `operator1` / `operator123`

## 🔧 Smart Weight Machine Configuration

### 1. Connect Smart Weight Machine
- Connect Smart Weight machine to server's USB or serial port
- Identify the port (usually `/dev/ttyUSB0` for USB or `/dev/ttyS0` for serial)

### 2. Configure in System
1. Login as administrator
2. Navigate to the system
3. Configure Smart Weight settings:
   - **Port**: `/dev/ttyUSB0` (or your actual port)
   - **Baud Rate**: `9600` (check your machine manual)
   - **Data Bits**: `8`
   - **Stop Bits**: `1`
   - **Parity**: `None`

### 3. Test Connection
- Go to Operator Dashboard → Weighing Operations
- Click "Connect Bridge"
- Verify weight readings appear

## 🔒 Security Configuration

### Change Default Passwords
```bash
# Change admin password
sudo python3 -c "
from app import app, User, db
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('your-new-admin-password')
    db.session.commit()
"

# Create new operator users
# Use the web interface: Admin → Users → Register User
```

### Setup SSL Certificate (Optional but Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (replace your-domain.com)
sudo certbot --nginx -d your-domain.com
```

## 📊 System Management

### Service Commands
```bash
# Check service status
sudo systemctl status weighbridge

# Restart service
sudo systemctl restart weighbridge

# View logs
sudo journalctl -u weighbridge -f

# Stop service
sudo systemctl stop weighbridge

# Start service
sudo systemctl start weighbridge
```

### Database Management
```bash
# Backup database
sudo /opt/weighbridge/backup.sh

# Check database integrity
sqlite3 /opt/weighbridge/weighing_bridge.db "PRAGMA integrity_check;"

# View database location
ls -la /opt/weighbridge/weighing_bridge.db
```

## 🌐 Network Configuration

### Port Configuration
- **Application Port**: 8050 (internal)
- **Web Server Port**: 80 (HTTP), 443 (HTTPS)
- **Smart Weight Port**: Configured serial port

### Firewall Setup
```bash
# Allow web traffic
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow ssh
sudo ufw enable
```

## 📱 User Access

### Network Access
Users can access the system from any device on the network:
- **Desktop/Laptop**: Modern web browser
- **Tablet**: iOS Safari or Android Chrome
- **Mobile**: Responsive design works on all devices

### Recommended Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🔄 Maintenance

### Automatic Backups
- **Frequency**: Daily at 2:00 AM
- **Location**: `/opt/backups/weighbridge/`
- **Retention**: 30 days

### System Monitoring
- **Frequency**: Every 15 minutes
- **Checks**: Service status, disk space, database integrity
- **Auto-recovery**: Service restart on failure

### Manual Backup
```bash
# Create manual backup
sudo /opt/weighbridge/backup.sh

# Backup to external location
sudo cp /opt/backups/weighbridge/weighing_bridge_*.db /path/to/external/backup/
```

## ⚠️ Troubleshooting

### Service Won't Start
```bash
# Check logs for errors
sudo journalctl -u weighbridge --no-pager -n 50

# Common issues:
# 1. Port already in use → sudo lsof -i :8050
# 2. Permission issues → sudo chown -R www-data:www-data /opt/weighbridge
# 3. Database locked → sudo systemctl restart weighbridge
```

### Smart Weight Connection Issues
```bash
# Check serial port permissions
sudo groups www-data | grep dialout

# Test serial port
sudo cat /dev/ttyUSB0

# Check USB devices
lsusb | grep -i scale
```

### Can't Access Web Interface
```bash
# Check nginx status
sudo systemctl status nginx

# Check nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Check port 80 is open
sudo netstat -tlnp | grep :80
```

### Database Issues
```bash
# Check database file
ls -la /opt/weighbridge/weighing_bridge.db

# Repair database
sqlite3 /opt/weighbridge/weighing_bridge.db ".recover" | sqlite3 recovered.db

# Check disk space
df -h /opt/weighbridge
```

## 📞 Support

### Emergency Recovery
```bash
# Full system restart
sudo systemctl restart weighbridge nginx

# Reset to default configuration
sudo systemctl stop weighbridge
sudo cp /opt/weighbridge/app.py.backup /opt/weighbridge/app.py
sudo systemctl start weighbridge
```

### Log Locations
- **Application Logs**: `sudo journalctl -u weighbridge -f`
- **Web Server Logs**: `sudo tail -f /var/log/nginx/access.log`
- **Error Logs**: `sudo tail -f /var/log/nginx/error.log`

### Configuration Files
- **Main Config**: `/opt/weighbridge/production_config.py`
- **Nginx Config**: `/etc/nginx/sites-available/weighbridge`
- **Service Config**: `/etc/systemd/system/weighbridge.service`

## 🎯 Success Checklist

After deployment, verify:

- [ ] System accessible via web browser
- [ ] Admin login works
- [ ] Operator login works  
- [ ] Smart Weight machine connects
- [ ] Weight readings appear
- [ ] Can create weighing records
- [ ] Tickets generate correctly
- [ ] Excel export works
- [ ] Backup system running
- [ ] SSL certificate installed (if applicable)

Your Smart Weight Bridge Management System is now ready for production use! 🎉