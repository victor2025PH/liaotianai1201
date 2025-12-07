#!/bin/bash
# ============================================================
# Verify Services (Server Environment - Linux)
# ============================================================
# 
# Running Environment: Server Linux Environment
# Function: Verify backend and frontend services are running
# 
# One-click execution: bash scripts/server/verify-services.sh
# Step-by-step execution: See instructions below
# ============================================================

set -e

echo "============================================================"
echo "🔍 Verify Services Status"
echo "============================================================"
echo ""

# Check Backend Service
echo "Checking backend service..."
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend service is running (http://localhost:8000)"
    BACKEND_STATUS=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "ok")
    echo "   Status: $BACKEND_STATUS"
else
    echo "❌ Backend service is not running"
    echo "   Please start: bash scripts/server/start-all-services.sh"
fi

echo ""

# Check Frontend Service
echo "Checking frontend service..."
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ Frontend service is running (http://localhost:3000)"
else
    echo "⚠️ Frontend service is not running (optional)"
    echo "   Please start: cd saas-demo && npm run build && npm start"
fi

echo ""
echo "============================================================"
echo "📊 Verification Complete"
echo "============================================================"
echo ""

# ============================================================
# Step-by-step execution instructions:
# ============================================================
# 
# Step 1: Check backend health
#   curl http://localhost:8000/health
# 
# Step 2: Check frontend
#   curl http://localhost:3000
# 
# Step 3: Check API documentation
#   curl http://localhost:8000/docs
# ============================================================

