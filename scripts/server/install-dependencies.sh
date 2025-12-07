#!/bin/bash
# ============================================================
# Install Dependencies (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Install required dependencies for backend and frontend
# 
# One-click execution: bash scripts/server/install-dependencies.sh
# Step-by-step execution: See instructions below
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "📦 Install Dependencies (Server Environment)"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Please do not run as root"
    exit 1
fi

# Step 1: Install Python dependencies
echo "[1/3] Installing Python dependencies..."
cd "$PROJECT_ROOT/admin-backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Gunicorn if not present
if ! command -v gunicorn &> /dev/null; then
    echo "Installing Gunicorn..."
    pip install gunicorn[gevent]
fi

echo "✅ Python dependencies installed"

# Step 2: Install Node.js dependencies (if needed)
echo ""
echo "[2/3] Installing Node.js dependencies..."
cd "$PROJECT_ROOT/saas-demo"

if [ -f "package.json" ]; then
    if command -v npm &> /dev/null; then
        npm install
        echo "✅ Node.js dependencies installed"
    else
        echo "⚠️  npm not found, skipping Node.js dependencies"
    fi
else
    echo "⚠️  package.json not found, skipping Node.js dependencies"
fi

# Step 3: Verify installations
echo ""
echo "[3/3] Verifying installations..."

cd "$PROJECT_ROOT/admin-backend"
source venv/bin/activate

echo "Checking Python packages..."
python -c "import fastapi, uvicorn, sqlalchemy; print('✅ Core Python packages OK')" || {
    echo "❌ Core Python packages missing"
    exit 1
}

if command -v gunicorn &> /dev/null; then
    echo "✅ Gunicorn installed: $(gunicorn --version)"
else
    echo "⚠️  Gunicorn not found in PATH (may be in venv)"
fi

echo ""
echo "============================================================"
echo "✅ Installation Complete"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment:"
echo "     cd admin-backend && source venv/bin/activate"
echo ""
echo "  2. Start services:"
echo "     bash scripts/server/start-all-services.sh"
echo ""

# ============================================================
# Step-by-step execution instructions:
# ============================================================
# 
# Step 1: Create virtual environment
#   cd admin-backend
#   python3 -m venv venv
#   source venv/bin/activate
# 
# Step 2: Install Python dependencies
#   pip install --upgrade pip
#   pip install -r requirements.txt
#   pip install gunicorn[gevent]
# 
# Step 3: Install Node.js dependencies (if needed)
#   cd saas-demo
#   npm install
# ============================================================

