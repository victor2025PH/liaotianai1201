#!/bin/bash
# ============================================================
# Run All Deployment Preparation Tasks (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Execute security configuration, environment variable check, frontend verification, etc.
# 
# One-click execution: bash scripts/server/run-all-tasks.sh
# Step-by-step execution: See instructions below
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT/admin-backend"

echo "============================================================"
echo "🚀 Auto Execute All Deployment Preparation Tasks"
echo "============================================================"
echo ""

# Step 1: Check Security Configuration
echo "[1/3] 🔒 Checking security configuration..."
python scripts/check_security_config.py
CHECK_RESULT=$?

if [ $CHECK_RESULT -ne 0 ]; then
    echo ""
    echo "⚠️  Security issues found, setting up production security configuration..."
    echo ""
    python scripts/setup_production_security.py
    if [ $? -ne 0 ]; then
        echo "❌ Security configuration setup failed"
        exit 1
    fi
    echo ""
    echo "Waiting for configuration to take effect..."
    sleep 1
    echo ""
    echo "Re-checking security configuration..."
    python scripts/check_security_config.py
    if [ $? -ne 0 ]; then
        echo ""
        echo "⚠️  Note: Configuration saved to .env file, but service restart required"
        echo "⚠️  Or set system environment variables to take effect immediately"
    else
        echo "✅ Security configuration check passed!"
    fi
fi

echo ""

# Step 2: Check Environment Variable Documentation
echo "[2/3] 📋 Checking environment variable documentation..."
if [ ! -f ".env.example" ]; then
    echo "⚠️  .env.example does not exist"
    echo "Please refer to config/worker.env.example to create .env.example"
    echo "Or see: 環境變量設置指南.md"
else
    echo "✅ .env.example exists"
fi

echo ""

# Step 3: Frontend Function Verification
echo "[3/3] 🧪 Frontend function verification..."
echo "Note: This step requires both backend and frontend services to be running"
echo ""
python scripts/auto_frontend_verification.py

echo ""
echo "============================================================"
echo "📊 Task Execution Complete"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Check the above output to ensure all checks pass"
echo "  2. If security configuration has issues, run: python scripts/setup_production_security.py"
echo "  3. Complete frontend manual verification (see: 前端功能驗證清單.md)"
echo ""

# ============================================================
# Step-by-step execution instructions:
# ============================================================
# 
# Step 1: Check security configuration
#   python scripts/check_security_config.py
#   python scripts/setup_production_security.py
# 
# Step 2: Check environment variable documentation
#   Confirm .env.example exists
#   Reference: 環境變量設置指南.md
# 
# Step 3: Frontend function verification
#   Ensure services are running
#   python scripts/auto_frontend_verification.py
# ============================================================

