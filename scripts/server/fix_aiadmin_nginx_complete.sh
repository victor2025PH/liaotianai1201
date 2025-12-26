#!/bin/bash
# Complete fix for aiadmin.usdt2026.cc Nginx configuration

NGINX_CONFIG="/etc/nginx/sites-available/aiadmin.usdt2026.cc"

echo "=========================================="
echo "Fix aiadmin.usdt2026.cc Nginx configuration"
echo "=========================================="
echo ""

# 1. Backup current config
echo "1. Backup current configuration..."
sudo cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"

# 2. Create complete configuration (with location / block)
echo "2. Create complete configuration..."
sudo tee "$NGINX_CONFIG" > /dev/null << 'EOF'
server {
    listen 80;
    server_name aiadmin.usdt2026.cc;

    client_max_body_size 50M;

    # Next.js 静态资源
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
        access_log off;
    }

    # 后端 API 接口 (8000端口)
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

    # 前端主页面 (3007端口，管理后台前端) - 这个块之前缺失了！
    location / {
        proxy_pass http://127.0.0.1:3007;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

# 3. Ensure symlink exists
echo "3. Ensure symlink exists..."
sudo ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/aiadmin.usdt2026.cc

# 4. Test configuration
echo "4. Test Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi

# 5. Reload Nginx
echo "5. Reload Nginx..."
sudo systemctl reload nginx

if [ $? -eq 0 ]; then
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx reload failed"
    exit 1
fi

# 6. Verify
echo ""
echo "6. Verify configuration..."
echo "Location blocks in config:"
sudo grep -E "^    location" "$NGINX_CONFIG" || echo "No location blocks found"

echo ""
echo "Testing HTTP responses:"
echo "  Frontend (3007):"
curl -s -o /dev/null -w "    HTTP %{http_code}\n" http://127.0.0.1:3007
echo "  Domain (HTTP):"
curl -s -o /dev/null -w "    HTTP %{http_code}\n" http://aiadmin.usdt2026.cc

echo ""
echo "=========================================="
echo "Fix completed"
echo "=========================================="
echo ""
echo "Note: If you're accessing via HTTPS, you need to add HTTPS configuration separately."

