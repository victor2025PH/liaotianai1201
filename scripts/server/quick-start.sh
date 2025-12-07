#!/bin/bash
# ============================================================
# Quick Start (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Quick start with uvicorn (no gunicorn required)
# 
# One-click execution: bash scripts/server/quick-start.sh
# Step-by-step execution: See instructions below
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT/admin-backend"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set database URL
export DATABASE_URL="sqlite:///./admin.db"

echo "============================================================"
echo "🚀 Quick Start Backend Service"
echo "============================================================"
echo ""
echo "Starting with Uvicorn (development mode)..."
echo "Service will be available at: http://0.0.0.0:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start with uvicorn (no gunicorn required)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# ============================================================
# Step-by-step execution instructions:
# ============================================================
# 
# Step 1: Activate virtual environment (if exists)
#   cd admin-backend
#   source venv/bin/activate
# 
# Step 2: Set database URL
#   export DATABASE_URL="sqlite:///./admin.db"
# 
# Step 3: Start service
#   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# ============================================================

