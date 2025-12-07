#!/bin/bash
# Fix standalone mode startup script

set -e

echo "========================================="
echo "Fix Standalone Mode Startup"
echo "========================================="
echo ""

cd ~/liaotian/saas-demo || exit 1

# Check if .next/standalone exists
if [ -d ".next/standalone" ]; then
    echo "✅ Standalone build found"
    echo "   Using: node .next/standalone/server.js"
    
    # Stop old processes
    echo ""
    echo "=== Stopping old processes ==="
    pkill -f "next-server" 2>/dev/null || true
    pkill -f "node.*next" 2>/dev/null || true
    pkill -f "standalone/server" 2>/dev/null || true
    sleep 3
    
    # Start with standalone server
    echo ""
    echo "=== Starting with standalone server ==="
    cd .next/standalone
    PORT=3000 nohup node server.js > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "✅ Frontend started with standalone mode, PID: $FRONTEND_PID"
    
    # Wait and verify
    sleep 10
    
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "✅ Process is running"
        ss -tlnp | grep :3000 || echo "⚠️  Port 3000 not listening yet"
    else
        echo "❌ Process exited, check logs:"
        tail -50 /tmp/frontend.log
    fi
    
else
    echo "⚠️  Standalone build not found"
    echo "   Using: next start (standard mode)"
    
    # Stop old processes
    echo ""
    echo "=== Stopping old processes ==="
    pkill -f "next-server" 2>/dev/null || true
    pkill -f "node.*next" 2>/dev/null || true
    sleep 3
    
    # Start with next start
    echo ""
    echo "=== Starting with next start ==="
    nohup npm start > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "✅ Frontend started, PID: $FRONTEND_PID"
    
    sleep 10
    
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "✅ Process is running"
        ss -tlnp | grep :3000 || echo "⚠️  Port 3000 not listening yet"
    else
        echo "❌ Process exited, check logs:"
        tail -50 /tmp/frontend.log
    fi
fi

echo ""
echo "========================================="
echo "✅ Done!"
echo "========================================="
echo "Log file: /tmp/frontend.log"
echo "To view logs: tail -f /tmp/frontend.log"
