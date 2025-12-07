#!/bin/bash
# ============================================================
# View Service Logs (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: View detailed service logs to diagnose startup failures
# 
# One-click execution: bash scripts/server/view-service-logs.sh
# ============================================================

set -e

echo "============================================================"
echo "📋 View Service Logs"
echo "============================================================"
echo ""

echo "[1/3] Recent service logs (last 50 lines)..."
echo ""
sudo journalctl -u telegram-backend -n 50 --no-pager || true

echo ""
echo "[2/3] Error logs only..."
echo ""
sudo journalctl -u telegram-backend --no-pager | grep -i "error\|fail\|exception\|traceback" | tail -20 || true

echo ""
echo "[3/3] Testing manual start to see errors..."
echo ""
cd ~/telegram-ai-system/admin-backend

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Running: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo "Press Ctrl+C to stop after seeing the error"
    echo ""
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | head -50 || true
else
    echo "❌ Virtual environment not found"
fi

echo ""
echo "============================================================"
echo "✅ Log View Complete"
echo "============================================================"
echo ""
echo "To view logs in real-time:"
echo "  sudo journalctl -u telegram-backend -f"
echo ""

