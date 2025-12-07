#!/bin/bash
# ============================================================
# Quick Deploy Setup (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Quick setup for GitHub Actions deployment
# 
# One-click execution: bash scripts/server/quick-deploy-setup.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🚀 Quick Deploy Setup"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Step 1: Pull latest code to get deploy files
echo "[1/4] Pulling latest code..."
git pull origin main || {
    echo "⚠️  Git pull failed, trying to resolve..."
    git stash || true
    git pull origin main || {
        echo "❌ Cannot pull code. Please check Git repository."
        exit 1
    }
}

# Step 2: Check if deploy files exist
echo ""
echo "[2/4] Checking deploy files..."
if [ ! -f "deploy/systemd/setup-service.sh" ]; then
    echo "❌ Error: deploy/systemd/setup-service.sh not found"
    echo ""
    echo "Please ensure:"
    echo "  1. Files are pushed to GitHub"
    echo "  2. Run: git pull origin main"
    exit 1
fi

if [ ! -f "deploy/systemd/telegram-backend.service" ]; then
    echo "❌ Error: deploy/systemd/telegram-backend.service not found"
    exit 1
fi

echo "✅ Deploy files found"

# Step 3: Setup virtual environment if needed
echo ""
echo "[3/4] Checking virtual environment..."
if [ ! -d "admin-backend/venv" ]; then
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
fi

# Step 4: Install systemd service
echo ""
echo "[4/4] Installing systemd service..."
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Need sudo privileges to install service"
    echo "Running: sudo bash deploy/systemd/setup-service.sh"
    sudo bash deploy/systemd/setup-service.sh
else
    bash deploy/systemd/setup-service.sh
fi

echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Configure GitHub Secrets (SSH_HOST, SSH_USERNAME, SSH_PRIVATE_KEY)"
echo "  2. Push code to trigger deployment: git push origin main"
echo "  3. Check deployment: GitHub Actions → Deploy to Server"
echo ""

