#!/bin/bash
# Fix and deploy frontend completely

set -e

echo "=========================================="
echo "Fix and Deploy Frontend"
echo "=========================================="

cd ~/liaotian || {
    echo "❌ Cannot enter project directory"
    exit 1
}

# 1. Pull latest code
echo ""
echo "=== 1. Pull Latest Code ==="
git pull origin main || git pull origin master
echo "✅ Code updated"

# 2. Enter frontend directory
echo ""
echo "=== 2. Enter Frontend Directory ==="
cd ~/liaotian/saas-demo || {
    echo "❌ Cannot enter frontend directory"
    exit 1
}

# 3. Install dependencies
echo ""
echo "=== 3. Install Dependencies ==="
npm install
echo "✅ Dependencies installed"

# 4. Clean cache
echo ""
echo "=== 4. Clean Build Cache ==="
rm -rf .next
rm -rf node_modules/.cache
echo "✅ Cache cleaned"

# 5. Build frontend
echo ""
echo "=== 5. Build Frontend ==="
if npm run build; then
    echo "✅ Frontend build successful"
else
    echo "❌ Frontend build failed"
    echo "Check error messages above..."
    exit 1
fi

# 6. Clean old processes
echo ""
echo "=== 6. Clean Old Processes ==="
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
sleep 3

# Check and clean port 3000
if command -v ss > /dev/null; then
    PID=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+' | head -1 || true)
    if [ -n "$PID" ]; then
        echo "Terminating process on port 3000: $PID"
        kill $PID 2>/dev/null || true
        sleep 2
    fi
fi

# 7. Start frontend service
echo ""
echo "=== 7. Start Frontend Service ==="
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend service started, PID: $FRONTEND_PID"

# 8. Wait and verify
echo ""
echo "=== 8. Verify Service ==="
sleep 10

if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "✅ Frontend process is running (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend process exited"
    echo "Check logs:"
    tail -50 /tmp/frontend.log
    exit 1
fi

# Check port
if command -v ss > /dev/null; then
    if ss -tlnp | grep :3000 > /dev/null; then
        echo "✅ Port 3000 is listening"
        ss -tlnp | grep :3000
    else
        echo "⚠️  Port 3000 is not listening"
        echo "Check logs:"
        tail -30 /tmp/frontend.log
    fi
fi

# Check HTTP response
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ Frontend service responding (HTTP $HTTP_CODE)"
else
    echo "⚠️  Frontend service not responding (HTTP $HTTP_CODE)"
    echo "Check logs: tail -f /tmp/frontend.log"
fi

# 9. Check backend service
echo ""
echo "=== 9. Check Backend Service ==="
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend service is running"
    curl -s http://localhost:8000/health
else
    echo "⚠️  Backend service not responding"
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Service Status:"
echo "  Backend: http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "View Logs:"
echo "  Frontend: tail -f /tmp/frontend.log"
echo "  Backend: tail -f /tmp/backend.log"
echo ""
echo "Check Service Status:"
echo "  ps aux | grep -E 'node|uvicorn' | grep -v grep"
echo "  ss -tlnp | grep -E ':3000|:8000'"
