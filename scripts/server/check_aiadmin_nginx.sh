#!/bin/bash
# Check all Nginx configurations for aiadmin.usdt2026.cc

echo "=========================================="
echo "Check Nginx configurations for aiadmin.usdt2026.cc"
echo "=========================================="
echo ""

# 1. Check HTTP configuration
echo "1. HTTP configuration (port 80):"
echo "----------------------------------------"
if [ -f "/etc/nginx/sites-available/aiadmin.usdt2026.cc" ]; then
    echo "File exists: /etc/nginx/sites-available/aiadmin.usdt2026.cc"
    echo ""
    echo "proxy_pass directives:"
    grep proxy_pass /etc/nginx/sites-available/aiadmin.usdt2026.cc || echo "No proxy_pass found"
    echo ""
    echo "Full configuration:"
    cat /etc/nginx/sites-available/aiadmin.usdt2026.cc
else
    echo "File not found: /etc/nginx/sites-available/aiadmin.usdt2026.cc"
fi

echo ""
echo "2. Check if enabled:"
echo "----------------------------------------"
if [ -L "/etc/nginx/sites-enabled/aiadmin.usdt2026.cc" ]; then
    echo "✅ Symlink exists"
    ls -la /etc/nginx/sites-enabled/aiadmin.usdt2026.cc
else
    echo "❌ Symlink not found"
fi

echo ""
echo "3. Check HTTPS configuration (port 443):"
echo "----------------------------------------"
if [ -f "/etc/nginx/sites-available/aiadmin.usdt2026.cc-ssl" ]; then
    echo "Found SSL config file"
    cat /etc/nginx/sites-available/aiadmin.usdt2026.cc-ssl
elif grep -q "listen 443" /etc/nginx/sites-available/aiadmin.usdt2026.cc 2>/dev/null; then
    echo "HTTPS configuration found in main config file:"
    grep -A 50 "listen 443" /etc/nginx/sites-available/aiadmin.usdt2026.cc
else
    echo "No HTTPS configuration found"
fi

echo ""
echo "4. Check default configuration:"
echo "----------------------------------------"
if [ -f "/etc/nginx/sites-available/default" ]; then
    if grep -q "aiadmin.usdt2026.cc" /etc/nginx/sites-available/default; then
        echo "⚠️  aiadmin.usdt2026.cc found in default config:"
        grep -A 20 "aiadmin.usdt2026.cc" /etc/nginx/sites-available/default
    else
        echo "Not found in default config"
    fi
fi

echo ""
echo "5. Check all enabled sites:"
echo "----------------------------------------"
ls -la /etc/nginx/sites-enabled/ | grep -E "aiadmin|default"

echo ""
echo "6. Check which server block handles the domain:"
echo "----------------------------------------"
sudo nginx -T 2>/dev/null | grep -A 30 "server_name aiadmin.usdt2026.cc" || echo "No matching server block found in nginx -T"

