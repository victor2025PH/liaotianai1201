#!/bin/bash
# Fix Nginx configuration for aiadmin.usdt2026.cc

echo "=========================================="
echo "Fix Nginx configuration for aiadmin.usdt2026.cc"
echo "=========================================="
echo ""

NGINX_CONFIG="/etc/nginx/sites-available/aiadmin.usdt2026.cc"

# 1. Check current configuration
echo "1. Check current Nginx configuration..."
if [ -f "$NGINX_CONFIG" ]; then
    echo "Current configuration:"
    cat "$NGINX_CONFIG"
else
    echo "ERROR: Nginx configuration file not found: $NGINX_CONFIG"
    exit 1
fi

echo ""
echo "2. Create correct Nginx configuration..."

# Backup current config
cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"

# Write correct configuration
sudo tee "$NGINX_CONFIG" > /dev/null << 'EOF'
server {
    listen 80;
    server_name aiadmin.usdt2026.cc;

    client_max_body_size 50M;

    # --- 1. Next.js 静态资源（标准路径 _next/static）---
    location /_next/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade "";
        proxy_set_header Connection "";
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # --- 2. 后端 API 接口 (8000端口) ---
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # --- 3. 前端主页面 (3007端口，管理后台前端) ---
    location / {
        proxy_pass http://127.0.0.1:3007;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

echo "✅ Configuration file updated"

# 3. Test Nginx configuration
echo ""
echo "3. Test Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration test failed"
    echo "Restoring backup..."
    cp "$NGINX_CONFIG.backup."* "$NGINX_CONFIG" 2>/dev/null || true
    exit 1
fi

# 4. Reload Nginx
echo ""
echo "4. Reload Nginx..."
sudo systemctl reload nginx

if [ $? -eq 0 ]; then
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx reload failed"
    exit 1
fi

# 5. Verify configuration
echo ""
echo "5. Verify configuration..."
echo "Checking what's listening on ports:"
sudo lsof -i :3007 | grep LISTEN || echo "  Port 3007: Not found (may be normal)"
sudo lsof -i :8000 | grep LISTEN || echo "  Port 8000: Not found (may be normal)"

echo ""
echo "Testing HTTP responses:"
echo "  Frontend (3007):"
curl -s -o /dev/null -w "    HTTP %{http_code}\n" http://127.0.0.1:3007
echo "  Backend API (8000):"
curl -s -o /dev/null -w "    HTTP %{http_code}\n" http://127.0.0.1:8000/api/v1/sites

echo ""
echo "=========================================="
echo "Fix completed"
echo "=========================================="
echo ""
echo "Please test: http://aiadmin.usdt2026.cc"
echo "It should now show the admin frontend, not aizkw content"

