#!/bin/bash
# ============================================================
# Start All Services (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: One-click start backend and frontend services
# 
# One-click execution: bash scripts/server/start-all-services.sh
# Step-by-step execution: See instructions below
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "============================================================"
echo "🚀 Start All Services (Server Environment)"
echo "============================================================"
echo ""

# Step 1: Start Backend Service
echo "[1/2] Starting backend service..."
cd admin-backend
export DATABASE_URL="sqlite:///./admin.db"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if gunicorn is available
if command -v gunicorn &> /dev/null || python -m gunicorn --version &> /dev/null; then
    # Use Gunicorn for production
    echo "Using Gunicorn (production mode)..."
    screen -dmS backend-service bash -c "cd $PROJECT_ROOT/admin-backend && source venv/bin/activate 2>/dev/null || true && export DATABASE_URL='sqlite:///./admin.db' && gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
else
    # Fallback to uvicorn
    echo "Using Uvicorn (development mode)..."
    screen -dmS backend-service bash -c "cd $PROJECT_ROOT/admin-backend && source venv/bin/activate 2>/dev/null || true && export DATABASE_URL='sqlite:///./admin.db' && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
fi
echo "✅ Backend service starting (port 8000)"

sleep 3

# Step 2: Start Frontend Service
echo ""
echo "[2/2] Starting frontend service..."
cd ../saas-demo

# Use screen to run in background
screen -dmS frontend-service bash -c "npm run build && npm start"
echo "✅ Frontend service starting (port 3000)"

echo ""
echo "============================================================"
echo "📊 Services Started"
echo "============================================================"
echo ""
echo "Service URLs:"
echo "  Backend API: http://localhost:8000"
echo "  Frontend UI: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Wait for services to start (about 10-30 seconds), then:"
echo "  1. Access frontend UI for verification"
echo "  2. Run: bash scripts/server/verify-services.sh"
echo ""
echo "View running services:"
echo "  screen -ls"
echo "  screen -r backend-service"
echo "  screen -r frontend-service"
echo ""

# ============================================================
# Step-by-step execution instructions:
# ============================================================
# 
# Step 1: Start backend service
#   cd admin-backend
#   export DATABASE_URL="sqlite:///./admin.db"
#   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
#   # Or for production:
#   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
# 
# Step 2: Start frontend service (another terminal)
#   cd saas-demo
#   npm run build
#   npm start
# 
# Step 3: Verify services
#   curl http://localhost:8000/health
#   curl http://localhost:3000
# ============================================================

