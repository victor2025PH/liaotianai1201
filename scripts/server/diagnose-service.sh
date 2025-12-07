#!/bin/bash
# ============================================================
# Diagnose Service Issues (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Diagnose and fix service startup issues
# 
# One-click execution: bash scripts/server/diagnose-service.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🔍 Diagnose Service Issues"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Step 1: Check service status
echo "[1/5] Checking service status..."
sudo systemctl status telegram-backend --no-pager || true

echo ""
echo "[2/5] Checking service logs (last 50 lines)..."
sudo journalctl -u telegram-backend -n 50 --no-pager || true

echo ""
echo "[3/5] Checking virtual environment..."
if [ ! -d "admin-backend/venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Creating virtual environment..."
    cd admin-backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
    # Test if uvicorn is available
    if [ -f "admin-backend/venv/bin/uvicorn" ]; then
        echo "✅ uvicorn found in venv"
    else
        echo "⚠️  uvicorn not found, installing..."
        cd admin-backend
        source venv/bin/activate
        pip install uvicorn
        cd ..
    fi
fi

echo ""
echo "[4/5] Checking service file..."
if [ -f "/etc/systemd/system/telegram-backend.service" ]; then
    echo "✅ Service file exists"
    echo ""
    echo "Current service file content:"
    cat /etc/systemd/system/telegram-backend.service
else
    echo "❌ Service file not found"
fi

echo ""
echo "[5/5] Testing manual start..."
cd admin-backend

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, creating default..."
    echo "DATABASE_URL=sqlite:///./admin.db" > .env
fi

# Try to start manually to see errors
echo "Testing manual start (will stop after 5 seconds)..."
source venv/bin/activate
timeout 5 python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 || {
    echo ""
    echo "❌ Manual start failed. Error details above."
    echo ""
    echo "Common issues:"
    echo "  1. Missing dependencies - run: pip install -r requirements.txt"
    echo "  2. Database connection error - check .env file"
    echo "  3. Port already in use - check: sudo lsof -i :8000"
    echo "  4. Permission issues - check file permissions"
}

cd ..

echo ""
echo "============================================================"
echo "✅ Diagnosis Complete!"
echo "============================================================"
echo ""
echo "Next steps based on errors above:"
echo "  1. Fix any issues found"
echo "  2. Restart service: sudo systemctl restart telegram-backend"
echo "  3. Check status: sudo systemctl status telegram-backend"
echo ""

