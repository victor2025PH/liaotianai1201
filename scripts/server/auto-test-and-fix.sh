#!/bin/bash
# ============================================================
# Auto Test and Fix (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Automatically test all functions, detect errors and auto-fix
# 
# One-click execution: bash scripts/server/auto-test-and-fix.sh
# Step-by-step execution: See instructions below
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT/admin-backend"

echo "============================================================"
echo "🚀 Auto Test and Fix System"
echo "============================================================"
echo ""

# Step 1: Fix Configuration
echo "[Step 1/5] Fixing configuration..."
python scripts/check_security_config.py >/dev/null 2>&1 || {
    echo "Setting security configuration..."
    python scripts/setup_production_security.py
}

# Step 2: Initialize Database
echo ""
echo "[Step 2/5] Initializing database..."
export DATABASE_URL="sqlite:///./admin.db"
python init_db_tables.py || {
    echo "❌ Database initialization failed"
    exit 1
}

# Step 3: Start Backend Service
echo ""
echo "[Step 3/5] Starting backend service..."
export DATABASE_URL="sqlite:///./admin.db"
screen -dmS backend-service bash -c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 || gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"

echo "Waiting for service to start..."
sleep 15

# Step 4: Verify Service
echo ""
echo "[Step 4/5] Verifying service..."
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend service is running"
else
    echo "⚠️ Backend service may still be starting"
fi

# Step 5: Run Automated Tests
echo ""
echo "[Step 5/5] Running automated tests..."
python scripts/auto_test_and_fix.py

echo ""
echo "============================================================"
echo "📊 Testing Complete"
echo "============================================================"
echo ""
echo "Service URLs:"
echo "  Backend: http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "View detailed report: admin-backend/最終測試報告.md"
echo ""

# ============================================================
# Step-by-step execution instructions:
# ============================================================
# 
# Step 1: Fix configuration
#   python scripts/check_security_config.py
#   python scripts/setup_production_security.py
# 
# Step 2: Initialize database
#   export DATABASE_URL="sqlite:///./admin.db"
#   python init_db_tables.py
# 
# Step 3: Start service
#   export DATABASE_URL="sqlite:///./admin.db"
#   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
#   # Or for production:
#   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
# 
# Step 4: Verify service
#   curl http://localhost:8000/health
# 
# Step 5: Run tests
#   python scripts/auto_test_and_fix.py
# ============================================================

