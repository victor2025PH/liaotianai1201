#!/bin/bash
# Direct diagnostic script for API 404 issue - can be created directly on server

echo "=========================================="
echo "Diagnose API 404 Issue"
echo "=========================================="
echo ""

# 1. Check if backend is running
echo "1. Check backend status:"
echo "----------------------------------------"
if sudo lsof -i :8000 2>/dev/null | grep -q LISTEN; then
    echo "✅ Backend is running on port 8000"
    sudo lsof -i :8000 | grep LISTEN
else
    echo "❌ Backend is NOT running on port 8000"
    echo "Checking PM2 status..."
    pm2 list | grep -i backend || echo "Backend not in PM2"
fi

echo ""
echo "2. Test backend API endpoint directly (localhost:8000):"
echo "----------------------------------------"
echo "Testing GET /api/v1/sites..."
curl -v http://127.0.0.1:8000/api/v1/sites 2>&1 | head -40

echo ""
echo ""
echo "3. Check backend main.py for API router:"
echo "----------------------------------------"
if [ -f "/opt/web3-sites/admin-backend-minimal/app/main.py" ]; then
    echo "✅ Found main.py"
    echo "Checking API router configuration:"
    echo "--- include_router lines:"
    grep -n "include_router" /opt/web3-sites/admin-backend-minimal/app/main.py | head -5
    echo ""
    echo "--- /api/v1 prefix:"
    grep -B 3 -A 3 "/api/v1" /opt/web3-sites/admin-backend-minimal/app/main.py | head -10
else
    echo "❌ main.py not found"
fi

echo ""
echo "4. Check backend API directory structure:"
echo "----------------------------------------"
if [ -d "/opt/web3-sites/admin-backend-minimal/app/api" ]; then
    echo "API directory exists:"
    ls -la /opt/web3-sites/admin-backend-minimal/app/api/ | head -20
else
    echo "❌ API directory not found"
fi

echo ""
echo "5. Test backend root endpoint:"
echo "----------------------------------------"
curl -v http://127.0.0.1:8000/ 2>&1 | head -20

echo ""
echo "6. Test Nginx proxy (HTTP):"
echo "----------------------------------------"
curl -I http://aiadmin.usdt2026.cc/api/v1/sites 2>&1 | head -15

echo ""
echo "7. Test Nginx proxy (HTTPS):"
echo "----------------------------------------"
curl -k -I https://aiadmin.usdt2026.cc/api/v1/sites 2>&1 | head -15

echo ""
echo "8. Check Nginx configuration for /api/ location:"
echo "----------------------------------------"
sudo grep -A 10 "location /api/" /etc/nginx/sites-available/aiadmin.usdt2026.cc

echo ""
echo "=========================================="
echo "Diagnosis completed"
echo "=========================================="

