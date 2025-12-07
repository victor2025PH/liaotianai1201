#!/bin/bash
# ============================================================
# Manual Fix Service (Server Environment - Linux)
# ============================================================
# 
# This script can be created directly on the server if needed
# ============================================================

set -e

cd ~/telegram-ai-system

echo "============================================================"
echo "🔧 Manual Fix Service"
echo "============================================================"
echo ""

# Step 1: Stop service
echo "[1/5] Stopping service..."
sudo systemctl stop telegram-backend 2>/dev/null || true

# Step 2: Check virtual environment
echo ""
echo "[2/5] Checking virtual environment..."
cd admin-backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

cd ..

# Step 3: Check .env file
echo ""
echo "[3/5] Checking .env file..."
if [ ! -f "admin-backend/.env" ]; then
    echo "Creating .env file..."
    cat > admin-backend/.env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=change_me_in_production
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
EOF
    echo "✅ .env file created"
fi

# Step 4: Fix permissions
echo ""
echo "[4/5] Fixing permissions..."
sudo chown -R ubuntu:ubuntu admin-backend 2>/dev/null || true
chmod +x admin-backend/venv/bin/* 2>/dev/null || true

# Step 5: Update service file
echo ""
echo "[5/5] Updating service file..."

PROJECT_ABS_PATH=$(pwd)
USER=$(logname || echo "ubuntu")
GROUP=$(id -gn "$USER")

sudo tee /etc/systemd/system/telegram-backend.service > /dev/null << EOF
[Unit]
Description=Telegram AI System Backend Service
After=network.target

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$PROJECT_ABS_PATH/admin-backend
Environment="PATH=$PROJECT_ABS_PATH/admin-backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

ExecStart=$PROJECT_ABS_PATH/admin-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-backend

NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file updated"

# Reload and start
echo ""
echo "Reloading systemd and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-backend
sudo systemctl start telegram-backend

sleep 3

echo ""
echo "Checking service status..."
sudo systemctl status telegram-backend --no-pager -l || true

echo ""
echo "============================================================"
echo "✅ Fix Complete!"
echo "============================================================"
echo ""
echo "Check logs if still failing:"
echo "  sudo journalctl -u telegram-backend -f"
echo ""

