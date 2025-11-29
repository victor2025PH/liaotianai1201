#!/bin/bash
# 最终完整修复 502 - 覆盖所有步骤

set -e

cd ~/liaotian/saas-demo

echo "========================================"
echo "最终完整修复 502"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

LOG_FILE="/tmp/502_final_fix_$(date +%s).log"
{
    echo "开始修复: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
} > "$LOG_FILE"

# 步骤 1: 修复 package.json 端口
echo "[1/8] 修复端口配置..."
if grep -q '"dev": "next dev -p 3001"' package.json; then
    sed -i 's/"dev": "next dev -p 3001"/"dev": "next dev -p 3000"/g' package.json
    echo "✅ 端口已修复为 3000"
    echo "端口已修复" >> "$LOG_FILE"
fi
echo ""

# 步骤 2: 停止所有相关进程
echo "[2/8] 停止旧进程..."
pkill -f "next.*dev|node.*3000|node.*3001" || true
sleep 3

# 清理端口
sudo lsof -i :3000 2>/dev/null | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
sleep 2
echo "✅ 完成"
echo ""

# 步骤 3: 检查并安装依赖
echo "[3/8] 检查依赖..."
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/next" ]; then
    echo "安装依赖..."
    npm install >> "$LOG_FILE" 2>&1
    echo "✅ 依赖安装完成"
else
    echo "✅ 依赖已存在"
fi
echo ""

# 步骤 4: 尝试构建
echo "[4/8] 检查构建..."
if [ ! -d ".next" ]; then
    echo "开始构建..."
    npm run build >> "$LOG_FILE" 2>&1 || echo "构建失败但继续"
fi
echo "✅ 完成"
echo ""

# 步骤 5: 启动前端服务
echo "[5/8] 启动前端服务..."
npm run dev >> /tmp/frontend_final.log 2>&1 &
DEV_PID=$!
echo "PID: $DEV_PID"
echo "等待启动（60秒）..."
sleep 60

# 验证
if ps -p $DEV_PID > /dev/null 2>&1; then
    echo "✅ 进程运行中"
else
    echo "❌ 进程退出"
    tail -30 /tmp/frontend_final.log
    exit 1
fi

if curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 服务可访问"
else
    echo "⚠️  服务可能还在启动中"
fi
echo ""

# 步骤 6: 检查并修复 Nginx 配置
echo "[6/8] 检查 Nginx 配置..."
NGINX_FILE="/etc/nginx/sites-enabled/default"

# 备份
sudo cp "$NGINX_FILE" "${NGINX_FILE}.backup.$(date +%s)" 2>/dev/null || true

# 读取当前配置
CONFIG_CONTENT=$(sudo cat "$NGINX_FILE" 2>/dev/null)

# 检查是否需要修复
NEED_FIX=false

# 检查 proxy_pass 是否指向 3000
if ! echo "$CONFIG_CONTENT" | grep -q "proxy_pass.*127.0.0.1:3000"; then
    echo "⚠️  需要修复 proxy_pass 配置"
    NEED_FIX=true
fi

# 如果配置需要修复
if [ "$NEED_FIX" = true ]; then
    echo "修复 Nginx 配置..."
    
    # 创建新配置（基于现有结构）
    sudo tee "$NGINX_FILE" > /dev/null <<'EOF'
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }

    # 前端 - 所有路径都代理到 Next.js
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
    }

    # API workers
    location = /api/workers/ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location ~ ^/api/workers/(.+)$ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers/$1;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }
}
EOF
    echo "✅ 配置已更新"
fi

# 测试配置
echo ""
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ 配置语法正确"
    sudo systemctl reload nginx
    echo "✅ Nginx 已重载"
else
    echo "❌ 配置错误:"
    sudo nginx -t
    exit 1
fi
echo ""

# 步骤 7: 最终验证
echo "[7/8] 最终验证..."
sleep 5

echo "测试本地 3000:"
LOCAL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
echo "HTTP $LOCAL_STATUS"

echo "测试 Nginx 代理:"
PROXY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/group-ai/accounts)
echo "HTTP $PROXY_STATUS"

echo "测试域名访问:"
DOMAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://aikz.usdt2026.cc/group-ai/accounts)
echo "HTTP $DOMAIN_STATUS"
echo ""

# 步骤 8: 结果总结
echo "[8/8] 结果总结..."
echo "========================================"
if [ "$DOMAIN_STATUS" = "200" ] || [ "$DOMAIN_STATUS" = "301" ] || [ "$DOMAIN_STATUS" = "302" ] || [ "$DOMAIN_STATUS" = "304" ]; then
    echo "✅ 修复成功！"
    echo "域名访问: HTTP $DOMAIN_STATUS"
else
    echo "⚠️  状态码: $DOMAIN_STATUS"
    echo "继续检查..."
fi
echo "========================================"
echo ""
echo "前端进程 PID: $DEV_PID"
echo "日志文件: $LOG_FILE"
echo "前端日志: /tmp/frontend_final.log"
