#!/bin/bash
# 完整修复 502 错误并持续验证

set -e

cd ~/liaotian

echo "========================================"
echo "完整修复 502 错误"
echo "========================================"
echo ""

# 函数定义
check_service() {
    local port=$1
    local name=$2
    if curl -s --max-time 3 "http://localhost:$port" > /dev/null 2>&1; then
        echo "✅ $name 正常 (端口 $port)"
        return 0
    else
        echo "❌ $name 异常 (端口 $port)"
        return 1
    fi
}

# 1. 启动后端
echo "[1/5] 启动后端服务..."
cd admin-backend
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pkill -f "uvicorn.*app.main:app" || true
    sleep 2
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_fix.log 2>&1 &
    echo "后端启动中..."
    sleep 5
    
    # 验证后端
    if curl -s --max-time 3 http://localhost:8000/health | grep -q "ok\|status"; then
        echo "✅ 后端服务已启动"
    else
        echo "⚠️  后端可能还在启动中"
    fi
else
    echo "❌ 虚拟环境不存在"
fi
cd ..

# 2. 启动前端
echo ""
echo "[2/5] 启动前端服务..."
cd saas-demo
pkill -f "next.*dev\|node.*3000" || true
sleep 2

# 确保在正确的目录
if [ ! -f "package.json" ]; then
    echo "❌ 无法找到 package.json"
    exit 1
fi

# 启动前端
nohup npm run dev > /tmp/frontend_fix.log 2>&1 &
echo "前端启动中..."
sleep 15

# 验证前端
if curl -s --max-time 3 http://localhost:3000 | head -1 | grep -q "html\|DOCTYPE"; then
    echo "✅ 前端服务已启动"
else
    echo "⚠️  前端可能还在启动中"
fi
cd ..

# 3. 检查并配置 Nginx
echo ""
echo "[3/5] 检查 Nginx 配置..."

# 检查配置是否存在
if [ ! -f "/etc/nginx/sites-enabled/default" ]; then
    echo "创建 Nginx 配置..."
    sudo tee /etc/nginx/sites-enabled/default > /dev/null <<'EOF'
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
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
}
EOF
fi

# 测试配置
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置正确"
else
    echo "❌ Nginx 配置错误"
    sudo nginx -t
fi

# 4. 重启 Nginx
echo ""
echo "[4/5] 重启 Nginx..."
sudo systemctl restart nginx
sleep 2

if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已重启"
else
    echo "❌ Nginx 启动失败"
    sudo systemctl status nginx --no-pager | head -10
fi

# 5. 最终验证
echo ""
echo "[5/5] 最终验证..."
sleep 3

check_service 8000 "后端服务"
check_service 3000 "前端服务"

echo ""
echo "========================================"
echo "修复完成"
echo "========================================"
echo ""
echo "服务状态:"
echo "  后端: http://localhost:8000/health"
echo "  前端: http://localhost:3000"
echo ""
echo "日志文件:"
echo "  后端: /tmp/backend_fix.log"
echo "  前端: /tmp/frontend_fix.log"
echo ""
echo "请稍等片刻后刷新浏览器测试"
