#!/bin/bash
set -e

# Deployment script for Kids project on VPS
# Run this script as root or with sudo on the VPS

PROJECT_DIR="/var/www/kids"
DOMAIN="kids-genius.run.place"
REPO_URL="https://github.com/sokil747/kids.git"

echo "=== Kids Project Deployment ==="
echo ""

# Step 1: Install system dependencies
echo "[1/8] Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-venv python3-pip python3-dev nginx certbot python3-certbot-nginx git

# Step 2: Create project directory and clone repo
echo "[2/8] Setting up project directory..."
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/logs
cd $PROJECT_DIR
git clone $REPO_URL .

# Step 3: Set up Python virtual environment
echo "[3/8] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Step 4: Set up .env file
echo "[4/8] Configuring environment variables..."
cp .env $PROJECT_DIR/.env

# Step 5: Collect static files and run migrations
echo "[5/8] Running migrations and collecting static files..."
source venv/bin/activate
python manage.py migrate --run-syncdb
python manage.py collectstatic --noinput
deactivate

# Step 6: Set up Nginx configuration
echo "[6/8] Configuring Nginx..."
cp deploy/kids.nginx /etc/nginx/sites-available/$DOMAIN
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Step 7: Set up SSL with Certbot
echo "[7/8] Setting up SSL certificate..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN --redirect || echo "SSL setup skipped (run manually: certbot --nginx -d $DOMAIN)"

# Step 8: Set up systemd service
echo "[8/8] Configuring systemd service..."
cp deploy/kids.service /etc/systemd/system/kids.service
systemctl daemon-reload
systemctl enable kids
systemctl restart kids

# Set proper permissions
chown -R www-data:www-data $PROJECT_DIR
chmod 755 $PROJECT_DIR
chmod 644 $PROJECT_DIR/db.sqlite3 2>/dev/null || true

echo ""
echo "=== Deployment Complete! ==="
echo "Your site should be available at https://$DOMAIN"
echo ""
echo "Don't forget to:"
echo "1. Create a superuser: cd $PROJECT_DIR && source venv/bin/activate && python manage.py createsuperuser"
echo "2. Configure BotSettings in the admin panel at https://$DOMAIN/admin"
echo ""
echo "Useful commands:"
echo "  Check service status:  systemctl status kids"
echo "  View logs:            tail -f $PROJECT_DIR/logs/uwsgi.log"
echo "  Restart service:      systemctl restart kids"
