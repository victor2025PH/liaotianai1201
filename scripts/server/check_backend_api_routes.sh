#!/bin/bash
# Check backend API routes configuration

echo "=========================================="
echo "Check backend API routes"
echo "=========================================="
echo ""

# 1. Check if backend is running
echo "1. Check if backend is running on port 8000:"
echo "----------------------------------------"
if sudo lsof -i :8000 2>/dev/null | grep -q LISTEN; then
    echo "✅ Backend is running on port 8000"
    sudo lsof -i :8000 | grep LISTEN
else
    echo "❌ Backend is NOT running on port 8000"
    exit 1
fi

echo ""
echo "2. Test backend API endpoint directly:"
echo "----------------------------------------"
echo "Testing GET /api/v1/sites..."
curl -v http://127.0.0.1:8000/api/v1/sites 2>&1 | head -30

echo ""
echo ""
echo "3. Check backend main.py for API router configuration:"
echo "----------------------------------------"
if [ -f "/opt/web3-sites/admin-backend-minimal/app/main.py" ]; then
    echo "Found main.py, checking API router configuration:"
    grep -A 5 "include_router" /opt/web3-sites/admin-backend-minimal/app/main.py || echo "No include_router found"
    grep -A 5 "app.include_router" /opt/web3-sites/admin-backend-minimal/app/main.py || echo "No app.include_router found"
    grep -B 5 -A 10 "/api/v1" /opt/web3-sites/admin-backend-minimal/app/main.py || echo "No /api/v1 found"
else
    echo "❌ main.py not found at /opt/web3-sites/admin-backend-minimal/app/main.py"
fi

echo ""
echo "4. Check backend API routes directory:"
echo "----------------------------------------"
if [ -d "/opt/web3-sites/admin-backend-minimal/app/api" ]; then
    echo "API directory structure:"
    find /opt/web3-sites/admin-backend-minimal/app/api -name "*.py" -type f | head -20
else
    echo "❌ API directory not found"
fi

echo ""
echo "5. Test backend root endpoint:"
echo "----------------------------------------"
curl -v http://127.0.0.1:8000/ 2>&1 | head -20

echo ""
echo "6. Test backend /docs endpoint (FastAPI docs):"
echo "----------------------------------------"
curl -s http://127.0.0.1:8000/docs 2>&1 | head -10 | grep -i "<title>" || echo "Docs endpoint might not be available"

echo ""
echo "=========================================="
echo "Check completed"
echo "=========================================="

