# Deployment Guide - Smart Weight Bridge Management System

## Production Deployment Instructions

### Prerequisites
- Linux server (Ubuntu 20.04+ or CentOS 8+ recommended)
- Python 3.11+
- Smart Weight weighing bridge machine
- Network access for user connectivity
- SSL certificate (for production)

### Step 1: Server Setup

1. **Update System Packages**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Python and Dependencies**
   ```bash
   sudo apt install python3.11 python3.11-pip python3.11-venv sqlite3 nginx -y
   ```

3. **Create Application Directory**
   ```bash
   sudo mkdir -p /opt/weighbridge
   sudo chown $USER:$USER /opt/weighbridge
   cd /opt/weighbridge
   ```

### Step 2: Application Setup

1. **Create Virtual Environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY='your-secure-secret-key-here'
   ```

4. **Create Production Configuration**
   ```bash
   # Create config.py
   cat > config.py << EOF
   import os
   
   class ProductionConfig:
       SECRET_KEY = os.environ.get('SECRET_KEY') or 'secure-default-key'
       SQLALCHEMY_DATABASE_URI = 'sqlite:///weighing_bridge.db'
       SQLALCHEMY_TRACK_MODIFICATIONS = False
       DEBUG = False
   EOF
   ```

### Step 3: Database Setup

1. **Initialize Database**
   ```bash
   python -c "from app import init_db; init_db()"
   ```

2. **Set Proper Permissions**
   ```bash
   chmod 644 weighing_bridge.db
   chown www-data:www-data weighing_bridge.db
   ```

### Step 4: System Service Setup

1. **Create Systemd Service File**
   ```bash
   sudo cat > /etc/systemd/system/weighbridge.service << EOF
   [Unit]
   Description=Smart Weight Bridge Management System
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/weighbridge
   Environment=PATH=/opt/weighbridge/venv/bin
   ExecStart=/opt/weighbridge/venv/bin/python app.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   EOF
   ```

2. **Enable and Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable weighbridge
   sudo systemctl start weighbridge
   ```

3. **Check Service Status**
   ```bash
   sudo systemctl status weighbridge
   ```

### Step 5: Nginx Reverse Proxy

1. **Create Nginx Configuration**
   ```bash
   sudo cat > /etc/nginx/sites-available/weighbridge << EOF
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8050;
           proxy_set_header Host \$host;
           proxy_set_header X-Real-IP \$remote_addr;
           proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto \$scheme;
       }
       
       # Static file handling
       location /static {
           alias /opt/weighbridge/static;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
   }
   EOF
   ```

2. **Enable Site**
   ```bash
   sudo ln -s /etc/nginx/sites-available/weighbridge /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Step 6: SSL Certificate (Optional but Recommended)

1. **Install Certbot**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   ```

2. **Obtain SSL Certificate**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. **Set Auto-Renewal**
   ```bash
   sudo crontab -e
   # Add: 0 12 * * * /usr/bin/certbot renew --quiet
   ```

### Step 7: Smart Weight Machine Setup

1. **Configure Serial Port**
   ```bash
   # Add user to dialout group for serial access
   sudo usermod -a -G dialout www-data
   ```

2. **Configure Port Settings**
   - Access the system at `http://your-domain.com`
   - Login as administrator
   - Navigate to settings and configure:
     - Smart Weight port (usually /dev/ttyUSB0 or /dev/ttyS0)
     - Baud rate (usually 9600)
     - Communication parameters

### Step 8: Backup Configuration

1. **Create Backup Script**
   ```bash
   sudo cat > /opt/weighbridge/backup.sh << EOF
   #!/bin/bash
   BACKUP_DIR="/opt/backups/weighbridge"
   DATE=\$(date +%Y%m%d_%H%M%S)
   mkdir -p \$BACKUP_DIR
   
   # Backup database
   cp /opt/weighbridge/weighing_bridge.db \$BACKUP_DIR/weighing_bridge_\$DATE.db
   
   # Backup configuration
   tar -czf \$BACKUP_DIR/config_\$DATE.tar.gz /opt/weighbridge/config.py /opt/weighbridge/.env
   
   # Keep last 30 days
   find \$BACKUP_DIR -name "*.db" -mtime +30 -delete
   find \$BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
   EOF
   
   sudo chmod +x /opt/weighbridge/backup.sh
   ```

2. **Schedule Automatic Backups**
   ```bash
   sudo crontab -e
   # Add: 0 2 * * * /opt/weighbridge/backup.sh
   ```

### Step 9: Monitoring and Logging

1. **Configure Log Rotation**
   ```bash
   sudo cat > /etc/logrotate.d/weighbridge << EOF
   /opt/weighbridge/logs/*.log {
       daily
       missingok
       rotate 30
       compress
       delaycompress
       notifempty
       create 644 www-data www-data
   }
   EOF
   ```

2. **Monitor System Resources**
   ```bash
   # Create monitoring script
   sudo cat > /opt/weighbridge/monitor.sh << EOF
   #!/bin/bash
   # Check if service is running
   if ! systemctl is-active --quiet weighbridge; then
       echo "Weighbridge service is not running!" | mail -s "Service Alert" admin@your-domain.com
   fi
   
   # Check disk space
   USAGE=\$(df /opt/weighbridge | tail -1 | awk '{print \$5}' | sed 's/%//')
   if [ \$USAGE -gt 80 ]; then
       echo "Disk usage is above 80%" | mail -s "Disk Alert" admin@your-domain.com
   fi
   EOF
   
   sudo chmod +x /opt/weighbridge/monitor.sh
   ```

### Step 10: Security Hardening

1. **Firewall Configuration**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 'Nginx Full'
   sudo ufw enable
   ```

2. **Fail2Ban Setup**
   ```bash
   sudo apt install fail2ban -y
   sudo systemctl enable fail2ban
   ```

3. **Regular Updates**
   ```bash
   # Set up automatic security updates
   sudo apt install unattended-upgrades -y
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```

## Maintenance

### Regular Tasks
1. **Weekly**: Check logs and system performance
2. **Monthly**: Update system packages
3. **Quarterly**: Review backup integrity
4. **Annually**: Full system audit and security review

### Troubleshooting Common Issues

1. **Service Not Starting**
   ```bash
   sudo journalctl -u weighbridge -f
   ```

2. **Database Issues**
   ```bash
   # Check database integrity
   sqlite3 /opt/weighbridge/weighing_bridge.db "PRAGMA integrity_check;"
   ```

3. **Smart Weight Connection Issues**
   ```bash
   # Check serial port permissions
   sudo groups www-data | grep dialout
   # Test serial connection
   sudo cat /dev/ttyUSB0
   ```

## Performance Optimization

1. **Database Optimization**
   ```bash
   sqlite3 /opt/weighbridge/weighing_bridge.db "VACUUM;"
   sqlite3 /opt/weighbridge/weighing_bridge.db "ANALYZE;"
   ```

2. **Application Performance**
   - Monitor response times
   - Optimize database queries
   - Implement caching where needed

This deployment guide provides a production-ready setup for the Smart Weight Bridge Management System with proper security, monitoring, and maintenance procedures.