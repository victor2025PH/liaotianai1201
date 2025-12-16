#!/bin/bash
# ============================================================
# 快速修复服务配置脚本
# ============================================================
# 
# 功能：
# 1. 修复 luckyred-api 服务配置（EnvironmentFile 可选）
# 2. 修复 liaotian-frontend 服务配置（检查路径）
# 3. 重启服务
#
# 使用方法：sudo bash scripts/server/fix_services_quick.sh
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

echo "============================================================"
echo "快速修复服务配置"
echo "============================================================"
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 此脚本需要 root 权限，请使用 sudo 运行"
    exit 1
fi

# ============================================================
# [1/4] 修复后端服务配置
# ============================================================
echo "[1/4] 修复后端服务配置"
echo "------------------------------------------------------------"

BACKEND_SERVICE="/etc/systemd/system/luckyred-api.service"

if [ ! -f "$BACKEND_SERVICE" ]; then
    echo "❌ 服务文件不存在: $BACKEND_SERVICE"
    echo "□ 从模板创建服务文件..."
    mkdir -p "$(dirname "$BACKEND_SERVICE")"
    cp "$PROJECT_DIR/deploy/systemd/luckyred-api.service" "$BACKEND_SERVICE" 2>/dev/null || {
        echo "❌ 无法复制模板文件，手动创建..."
        cat > "$BACKEND_SERVICE" << 'EOF'
[Unit]
Description=LuckyRed API Service (FastAPI)
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/telegram-ai-system/admin-backend
Environment="PATH=/home/ubuntu/telegram-ai-system/admin-backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH=/home/ubuntu/telegram-ai-system/admin-backend"
EnvironmentFile=-/home/ubuntu/telegram-ai-system/admin-backend/.env

ExecStart=/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=luckyred-api

NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
    }
fi

# 修复 EnvironmentFile（添加 - 前缀，使文件不存在时不报错）
sed -i 's|EnvironmentFile=/home/ubuntu/telegram-ai-system/admin-backend/.env|EnvironmentFile=-/home/ubuntu/telegram-ai-system/admin-backend/.env|' "$BACKEND_SERVICE"

# 检查虚拟环境是否存在
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "⚠️  虚拟环境不存在，创建中..."
    cd "$BACKEND_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt --quiet || echo "⚠️  部分依赖安装失败"
    deactivate
fi

# 检查 uvicorn 是否存在
if [ ! -f "$BACKEND_DIR/venv/bin/uvicorn" ]; then
    echo "⚠️  uvicorn 未安装，安装中..."
    cd "$BACKEND_DIR"
    source venv/bin/activate
    pip install uvicorn --quiet
    deactivate
fi

echo "✅ 后端服务配置已修复"
echo ""

# ============================================================
# [2/4] 修复前端服务配置
# ============================================================
echo "[2/4] 修复前端服务配置"
echo "------------------------------------------------------------"

FRONTEND_SERVICE="/etc/systemd/system/liaotian-frontend.service"

if [ ! -f "$FRONTEND_SERVICE" ]; then
    echo "❌ 服务文件不存在: $FRONTEND_SERVICE"
    echo "□ 从模板创建服务文件..."
    cp "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" "$FRONTEND_SERVICE" 2>/dev/null || {
        echo "❌ 无法复制模板文件，手动创建..."
        cat > "$FRONTEND_SERVICE" << 'EOF'
[Unit]
Description=Liaotian Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/telegram-ai-system/saas-demo
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NODE_OPTIONS=--max-old-space-size=1024
ExecStart=/usr/bin/node .next/standalone/saas-demo/server.js
Restart=always
RestartSec=5
LimitNOFILE=65535

StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOF
    }
fi

# 检查 server.js 是否存在
if [ ! -f "$FRONTEND_DIR/.next/standalone/saas-demo/server.js" ]; then
    echo "⚠️  server.js 不存在，检查构建..."
    
    # 检查是否有其他位置的 server.js
    SERVER_JS=$(find "$FRONTEND_DIR/.next" -name "server.js" -type f 2>/dev/null | head -1)
    
    if [ -n "$SERVER_JS" ]; then
        echo "□ 找到 server.js: $SERVER_JS"
        # 计算相对路径
        REL_PATH=$(realpath --relative-to="$FRONTEND_DIR" "$SERVER_JS")
        sed -i "s|ExecStart=.*|ExecStart=/usr/bin/node $REL_PATH|" "$FRONTEND_SERVICE"
        echo "✅ 已更新服务配置使用: $REL_PATH"
    else
        echo "❌ 未找到 server.js，需要重新构建前端"
        echo "□ 开始构建前端..."
        cd "$FRONTEND_DIR"
        npm install --prefer-offline --no-audit --no-fund || echo "⚠️  npm install 失败"
        export NODE_ENV=production
        export NODE_OPTIONS="--max-old-space-size=4096"
        npm run build || {
            echo "❌ 前端构建失败"
            echo "请检查构建日志"
            exit 1
        }
        
        # 再次检查
        if [ -f "$FRONTEND_DIR/.next/standalone/saas-demo/server.js" ]; then
            echo "✅ server.js 已生成"
        else
            SERVER_JS=$(find "$FRONTEND_DIR/.next" -name "server.js" -type f 2>/dev/null | head -1)
            if [ -n "$SERVER_JS" ]; then
                REL_PATH=$(realpath --relative-to="$FRONTEND_DIR" "$SERVER_JS")
                sed -i "s|ExecStart=.*|ExecStart=/usr/bin/node $REL_PATH|" "$FRONTEND_SERVICE"
            fi
        fi
    fi
else
    echo "✅ server.js 存在"
fi

echo "✅ 前端服务配置已修复"
echo ""

# ============================================================
# [3/4] 重新加载 systemd 配置
# ============================================================
echo "[3/4] 重新加载 systemd 配置"
echo "------------------------------------------------------------"
systemctl daemon-reload
echo "✅ systemd 配置已重新加载"
echo ""

# ============================================================
# [4/4] 重启服务
# ============================================================
echo "[4/4] 重启服务"
echo "------------------------------------------------------------"

echo "□ 停止服务..."
systemctl stop luckyred-api 2>/dev/null || true
systemctl stop liaotian-frontend 2>/dev/null || true
sleep 2

echo "□ 启动后端服务..."
systemctl start luckyred-api
sleep 3

if systemctl is-active --quiet luckyred-api; then
    echo "✅ 后端服务已启动"
else
    echo "❌ 后端服务启动失败"
    echo "查看日志: sudo journalctl -u luckyred-api -n 30 --no-pager"
fi

echo "□ 启动前端服务..."
systemctl start liaotian-frontend
sleep 3

if systemctl is-active --quiet liaotian-frontend; then
    echo "✅ 前端服务已启动"
else
    echo "❌ 前端服务启动失败"
    echo "查看日志: sudo journalctl -u liaotian-frontend -n 30 --no-pager"
fi

echo ""

# ============================================================
# 最终验证
# ============================================================
echo "============================================================"
echo "服务状态"
echo "============================================================"

systemctl status luckyred-api --no-pager | head -10
echo ""
systemctl status liaotian-frontend --no-pager | head -10
echo ""

echo "============================================================"
echo "✅ 修复完成"
echo "============================================================"
echo ""
echo "如果服务仍然失败，请查看详细日志："
echo "  sudo journalctl -u luckyred-api -n 50 --no-pager"
echo "  sudo journalctl -u liaotian-frontend -n 50 --no-pager"
echo ""

