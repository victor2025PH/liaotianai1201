#!/bin/bash
# ============================================================
# Fix Service Issues (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Fix common service startup issues
# 
# One-click execution: bash scripts/server/fix-service.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🔧 Fix Service Issues"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Step 1: Stop service
echo "[1/6] Stopping service..."
sudo systemctl stop telegram-backend 2>/dev/null || true

# Step 2: Check and fix virtual environment
echo ""
echo "[2/6] Checking virtual environment..."
cd admin-backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

cd ..

# Step 3: Check and create .env file
echo ""
echo "[3/6] Checking .env file..."
if [ ! -f "admin-backend/.env" ]; then
    echo "Creating .env file..."
    cat > admin-backend/.env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=change_me_in_production
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file exists"
fi

# Step 4: Fix permissions
echo ""
echo "[4/6] Fixing permissions..."
sudo chown -R ubuntu:ubuntu "$PROJECT_ROOT/admin-backend" 2>/dev/null || true
chmod +x admin-backend/venv/bin/* 2>/dev/null || true

# Step 5: Update service file
echo ""
echo "[5/6] Updating service file..."

# Get absolute paths
PROJECT_ABS_PATH=$(pwd)
USER=$(logname || echo "ubuntu")
GROUP=$(id -gn "$USER")

# Create updated service file
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

# Use virtual environment
ExecStart=$PROJECT_ABS_PATH/admin-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-backend

# Security
NoNewPrivileges=true
PrivateTmp=true

# Resource limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file updated"

# Step 6: Reload and start
echo ""
echo "[6/6] Reloading systemd and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-backend
sudo systemctl start telegram-backend

# Wait a moment
sleep 3

# Check status
echo ""
echo "Checking service status..."
sudo systemctl status telegram-backend --no-pager -l || true

echo ""
echo "============================================================"
echo "✅ Fix Complete!"
echo "============================================================"
echo ""
echo "If service still fails, check logs:"
echo "  sudo journalctl -u telegram-backend -f"
echo ""

