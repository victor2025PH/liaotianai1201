#!/bin/bash
# ============================================================
# Complete Auto Test and Fix (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Fully automated test all functions, monitor logs, auto-fix errors
# 
# One-click execution: bash scripts/server/complete-auto-test.sh
# Step-by-step execution: See instructions below
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT/admin-backend"

echo "============================================================"
echo "🤖 Complete Auto Test and Fix System"
echo "============================================================"
echo ""

echo "Running complete auto test and fix..."
python scripts/auto_test_and_fix.py

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ All tests passed! System running perfectly!"
    echo "============================================================"
else
    echo ""
    echo "============================================================"
    echo "⚠️  Issues found, please check the above output"
    echo "============================================================"
fi

echo ""
echo "Service URLs:"
echo "  Backend: http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""

# ============================================================
# Step-by-step execution instructions:
# ============================================================
# 
# Step 1: Run auto test
#   cd admin-backend
#   python scripts/auto_test_and_fix.py
# 
# Step 2: Check test results
#   View output and log files
# 
# Step 3: Verify services
#   Access http://localhost:8000/docs
#   Access http://localhost:3000
# ============================================================

