#!/bin/bash
# ============================================================
# Test Startup (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Test application startup manually to see errors
# 
# One-click execution: bash scripts/server/test-startup.sh
# ============================================================

set -e

cd ~/telegram-ai-system/admin-backend

echo "============================================================"
echo "🧪 Test Application Startup"
echo "============================================================"
echo ""

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

source venv/bin/activate

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, creating default..."
    cat > .env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=change_me_in_production
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
EOF
fi

echo "[1/3] Checking Python environment..."
python --version
which python

echo ""
echo "[2/3] Checking uvicorn..."
which uvicorn
uvicorn --version

echo ""
echo "[3/3] Testing startup..."
echo "This will show any errors. Press Ctrl+C to stop."
echo ""

# Try to start and capture errors
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | head -100 || {
    echo ""
    echo "============================================================"
    echo "❌ Startup failed. Error details above."
    echo "============================================================"
    echo ""
    echo "Common issues:"
    echo "  1. Missing dependencies: pip install -r requirements.txt"
    echo "  2. Database connection error: check .env file"
    echo "  3. Import errors: check Python path"
    echo "  4. Port already in use: sudo lsof -i :8000"
    exit 1
}

