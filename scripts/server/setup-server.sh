#!/bin/bash
# ============================================================
# Setup Server Environment (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Complete server setup including dependencies, database, and configuration
# 
# One-click execution: bash scripts/server/setup-server.sh
# Step-by-step execution: See instructions below
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "🖥️  Setup Server Environment"
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"

# Step 1: Install dependencies
echo "[1/4] Installing dependencies..."
bash scripts/server/install-dependencies.sh

# Step 2: Setup database
echo ""
echo "[2/4] Setting up database..."
cd admin-backend
source venv/bin/activate
export DATABASE_URL="sqlite:///./admin.db"

python init_db_tables.py || {
    echo "❌ Database setup failed"
    exit 1
}

echo "✅ Database setup complete"

# Step 3: Setup security configuration
echo ""
echo "[3/4] Setting up security configuration..."
python scripts/setup_production_security.py || {
    echo "⚠️  Security setup had issues, but continuing..."
}

# Step 4: Verify setup
echo ""
echo "[4/4] Verifying setup..."
python scripts/check_security_config.py

echo ""
echo "============================================================"
echo "✅ Server Setup Complete"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Start services:"
echo "     bash scripts/server/start-all-services.sh"
echo ""
echo "  2. Verify services:"
echo "     bash scripts/server/verify-services.sh"
echo ""

# ============================================================
# Step-by-step execution instructions:
# ============================================================
# 
# Step 1: Install dependencies
#   bash scripts/server/install-dependencies.sh
# 
# Step 2: Setup database
#   cd admin-backend
#   source venv/bin/activate
#   export DATABASE_URL="sqlite:///./admin.db"
#   python init_db_tables.py
# 
# Step 3: Setup security
#   python scripts/setup_production_security.py
# 
# Step 4: Verify
#   python scripts/check_security_config.py
# ============================================================

