#!/bin/bash

# Smart Weight Bridge Management System Deployment Script
# This script automates the deployment process for production use

echo "🚀 Smart Weight Bridge Management System Deployment"
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Get installation directory
INSTALL_DIR="/opt/weighbridge"
echo "📁 Installation directory: $INSTALL_DIR"

# Create installation directory
echo "📂 Creating installation directory..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Copy application files
echo "📋 Copying application files..."
cp -r /workspace/* $INSTALL_DIR/

# Set proper permissions
echo "🔒 Setting permissions..."
chown -R www-data:www-data $INSTALL_DIR
chmod 755 $INSTALL_DIR
chmod +x $INSTALL_DIR/*.py
chmod +x $INSTALL_DIR/*.sh

# Install system dependencies
echo "📦 Installing system dependencies..."
apt update
apt install -y python3.11 python3.11-pip python3.11-venv sqlite3 nginx supervisor

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
sudo -u www-data python3.11 -m venv $INSTALL_DIR/venv
sudo -u www-data $INSTALL_DIR/venv/bin/pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
sudo -u www-data $INSTALL_DIR/venv/bin/pip install -r $INSTALL_DIR/requirements.txt

# Create production config
echo "⚙️ Creating production configuration..."
cat > $INSTALL_DIR/production_config.py << 'EOF'
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secure-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///weighing_bridge.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    
    # Smart Weight Machine Settings
    SMART_WEIGHT_PORT = os.environ.get('SMART_WEIGHT_PORT', '/dev/ttyUSB0')
    SMART_WEIGHT_BAUDRATE = int(os.environ.get('SMART_WEIGHT_BAUDRATE', '9600'))
    
    # Security Settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', '3600'))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
EOF

# Update app.py to use production config
echo "🔧 Updating application for production..."
sed -i "s/app = Flask(__name__)/app = Flask(__name__, static_folder='static', template_folder='templates')/" $INSTALL_DIR/app.py
sed -i '/app\.config\[.SECRET_KEY.\]/d' $INSTALL_DIR/app.py
sed -i '/app\.config\[.SQLALCHEMY_DATABASE_URI.\]/d' $INSTALL_DIR/app.py
sed -i '/app\.config\[.SQLALCHEMY_TRACK_MODIFICATIONS.\]/d' $INSTALL_DIR/app.py

# Add production config import
sed -i "2i from production_config import ProductionConfig" $INSTALL_DIR/app.py
sed -i "3i app.config.from_object(ProductionConfig)" $INSTALL_DIR/app.py

# Create production startup script
echo "🚀 Creating startup script..."
cat > $INSTALL_DIR/start_production.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from production_config import ProductionConfig
from app import app, init_db

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run production server
    app.run(
        host='0.0.0.0',
        port=8050,
        debug=False,
        threaded=True
    )
EOF

chmod +x $INSTALL_DIR/start_production.py

# Initialize database
echo "🗄️ Initializing database..."
sudo -u www-data $INSTALL_DIR/venv/bin/python -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
from app import init_db
init_db()
"

# Create systemd service
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/weighbridge.service << EOF
[Unit]
Description=Smart Weight Bridge Management System
After=network.target
Wants=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
Environment=PYTHONPATH=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/start_production.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=weighbridge

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

# Create nginx configuration
echo "🌐 Creating nginx configuration..."
cat > /etc/nginx/sites-available/weighbridge << 'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    location / {
        proxy_pass http://127.0.0.1:8050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Static files
    location /static {
        alias $INSTALL_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_proxied expired no-cache no-store private must-revalidate auth;
        gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;
    }
    
    # Security - hide nginx version
    server_tokens off;
}
EOF

# Enable nginx site
echo "🔗 Enabling nginx site..."
ln -sf /etc/nginx/sites-available/weighbridge /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

# Configure serial port for Smart Weight
echo "🔌 Configuring serial port access..."
usermod -a -G dialout www-data

# Create backup script
echo "💾 Creating backup script..."
cat > $INSTALL_DIR/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/backups/weighbridge"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "📦 Backing up database..."
cp /opt/weighbridge/weighing_bridge.db $BACKUP_DIR/weighing_bridge_$DATE.db

# Backup configuration
echo "📋 Backing up configuration..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /opt/weighbridge/production_config.py /opt/weighbridge/app.py

# Clean old backups
echo "🧹 Cleaning old backups..."
find $BACKUP_DIR -name "*.db" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Backup completed: $BACKUP_DIR"
EOF

chmod +x $INSTALL_DIR/backup.sh

# Create monitoring script
echo "📊 Creating monitoring script..."
cat > $INSTALL_DIR/monitor.sh << 'EOF'
#!/bin/bash

# Check if service is running
if ! systemctl is-active --quiet weighbridge; then
    echo "❌ Weighbridge service is not running!"
    systemctl restart weighbridge
    echo "🔄 Service restarted"
fi

# Check disk space
USAGE=$(df /opt/weighbridge | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $USAGE -gt 80 ]; then
    echo "⚠️  Disk usage is above 80%: $USAGE%"
fi

# Check database integrity
sqlite3 /opt/weighbridge/weighing_bridge.db "PRAGMA integrity_check;" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Database integrity check failed!"
fi

echo "✅ Monitoring check completed"
EOF

chmod +x $INSTALL_DIR/monitor.sh

# Setup cron jobs
echo "⏰ Setting up scheduled tasks..."
(crontab -l 2>/dev/null; echo "0 2 * * * $INSTALL_DIR/backup.sh") | crontab -
(crontab -l 2>/dev/null; echo "*/15 * * * * $INSTALL_DIR/monitor.sh") | crontab -

# Enable and start services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable weighbridge
systemctl start weighbridge
systemctl enable nginx
systemctl restart nginx

# Wait for service to start
sleep 5

# Check service status
echo "🔍 Checking service status..."
if systemctl is-active --quiet weighbridge; then
    echo "✅ Weighbridge service is running"
else
    echo "❌ Weighbridge service failed to start"
    journalctl -u weighbridge --no-pager -n 20
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx service is running"
else
    echo "❌ Nginx service failed to start"
    systemctl status nginx --no-pager
    exit 1
fi

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "🎉 Deployment completed successfully!"
echo "=================================="
echo "📱 Access the system at:"
echo "   http://$SERVER_IP"
echo ""
echo "🔐 Default login credentials:"
echo "   Administrator: admin / admin123"
echo "   Operator: operator1 / operator123"
echo ""
echo "🔧 Important next steps:"
echo "   1. Change default passwords"
echo "   2. Configure Smart Weight machine settings"
echo "   3. Set up SSL certificate (optional)"
echo "   4. Configure backup location"
echo ""
echo "📚 Configuration files:"
echo "   Application: $INSTALL_DIR/production_config.py"
echo "   Logs: journalctl -u weighbridge -f"
echo "   Backups: $INSTALL_DIR/backup.sh"
echo ""
echo "🔍 Service commands:"
echo "   Restart: sudo systemctl restart weighbridge"
echo "   Status: sudo systemctl status weighbridge"
echo "   Logs: sudo journalctl -u weighbridge -f"
echo ""
echo "⚙️  Smart Weight machine setup:"
echo "   1. Connect Smart Weight machine to serial port"
echo "   2. Configure port settings in the system"
echo "   3. Test connection from Operator Dashboard"