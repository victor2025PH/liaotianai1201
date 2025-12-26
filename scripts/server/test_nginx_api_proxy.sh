#!/bin/bash
# Test Nginx API proxy configuration

echo "=========================================="
echo "Test Nginx API proxy"
echo "=========================================="
echo ""

echo "1. Test direct backend API (localhost:8000):"
echo "----------------------------------------"
curl -I http://127.0.0.1:8000/api/v1/sites 2>&1 | head -10

echo ""
echo "2. Test Nginx proxy for API (via HTTP):"
echo "----------------------------------------"
curl -I http://aiadmin.usdt2026.cc/api/v1/sites 2>&1 | head -10

echo ""
echo "3. Test Nginx proxy for API (via HTTPS):"
echo "----------------------------------------"
curl -k -I https://aiadmin.usdt2026.cc/api/v1/sites 2>&1 | head -10

echo ""
echo "4. Check Nginx access logs for API requests:"
echo "----------------------------------------"
sudo tail -20 /var/log/nginx/access.log | grep "api/v1/sites" || echo "No API requests found in logs"

echo ""
echo "5. Check Nginx error logs:"
echo "----------------------------------------"
sudo tail -20 /var/log/nginx/error.log | tail -10

echo ""
echo "=========================================="
echo "Test completed"
echo "=========================================="

