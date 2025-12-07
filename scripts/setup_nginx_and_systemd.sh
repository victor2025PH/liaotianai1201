#!/bin/bash
# Setup Nginx and Systemd Services for Liaotian AI System
# 配置 Nginx 反向代理和 Systemd 开机自启动

set -e

echo "========================================="
echo "Liaotian AI System - Nginx & Systemd Setup"
echo "聊天 AI 系统 - Nginx 和 Systemd 配置"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}错误: 请使用 sudo 运行此脚本${NC}"
    echo "Usage: sudo bash scripts/setup_nginx_and_systemd.sh"
    exit 1
fi

# 项目路径
PROJECT_DIR="/home/ubuntu/liaotian"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
SYSTEMD_DIR="/etc/systemd/system"

echo "=== 步骤 1: 安装 Nginx ==="
if ! command -v nginx &> /dev/null; then
    echo "安装 Nginx..."
    apt-get update
    apt-get install -y nginx
    echo -e "${GREEN}✅ Nginx 安装完成${NC}"
else
    echo -e "${GREEN}✅ Nginx 已安装${NC}"
fi

echo ""
echo "=== 步骤 2: 配置 Nginx ==="

# 复制 Nginx 配置文件
if [ -f "$PROJECT_DIR/deploy/nginx/liaotian.conf" ]; then
    cp "$PROJECT_DIR/deploy/nginx/liaotian.conf" "$NGINX_CONF_DIR/liaotian"
    echo -e "${GREEN}✅ Nginx 配置文件已复制${NC}"
else
    echo -e "${YELLOW}⚠️  配置文件不存在，创建默认配置...${NC}"
    
    cat > "$NGINX_CONF_DIR/liaotian" << 'EOF'
# Liaotian AI System - Nginx Configuration
upstream frontend {
    server localhost:3000;
    keepalive 64;
}

upstream backend {
    server localhost:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name 165.154.233.55;
    client_max_body_size 50M;

    # 前端
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }

    # 后端 API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }

    location /docs {
        proxy_pass http://backend/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    access_log /var/log/nginx/liaotian-access.log;
    error_log /var/log/nginx/liaotian-error.log;
}
EOF
    echo -e "${GREEN}✅ 默认 Nginx 配置已创建${NC}"
fi

# 创建符号链接（如果不存在）
if [ ! -L "$NGINX_ENABLED_DIR/liaotian" ]; then
    ln -s "$NGINX_CONF_DIR/liaotian" "$NGINX_ENABLED_DIR/liaotian"
    echo -e "${GREEN}✅ Nginx 配置已启用${NC}"
else
    echo -e "${GREEN}✅ Nginx 配置已存在${NC}"
fi

# 测试 Nginx 配置
echo "测试 Nginx 配置..."
if nginx -t; then
    echo -e "${GREEN}✅ Nginx 配置测试通过${NC}"
else
    echo -e "${RED}❌ Nginx 配置测试失败${NC}"
    exit 1
fi

# 重载 Nginx
systemctl reload nginx
echo -e "${GREEN}✅ Nginx 已重载${NC}"

echo ""
echo "=== 步骤 3: 配置 Systemd 服务 ==="

# 复制前端服务文件
if [ -f "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" ]; then
    cp "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" "$SYSTEMD_DIR/liaotian-frontend.service"
    echo -e "${GREEN}✅ 前端服务文件已复制${NC}"
else
    echo -e "${YELLOW}⚠️  前端服务文件不存在，创建默认配置...${NC}"
    
    cat > "$SYSTEMD_DIR/liaotian-frontend.service" << EOF
[Unit]
Description=Liaotian Frontend Service (Next.js)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$PROJECT_DIR/saas-demo
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo -e "${GREEN}✅ 默认前端服务文件已创建${NC}"
fi

# 复制后端服务文件
if [ -f "$PROJECT_DIR/deploy/systemd/liaotian-backend.service" ]; then
    cp "$PROJECT_DIR/deploy/systemd/liaotian-backend.service" "$SYSTEMD_DIR/liaotian-backend.service"
    echo -e "${GREEN}✅ 后端服务文件已复制${NC}"
else
    echo -e "${YELLOW}⚠️  后端服务文件不存在，创建默认配置...${NC}"
    
    cat > "$SYSTEMD_DIR/liaotian-backend.service" << EOF
[Unit]
Description=Liaotian Backend API Service (FastAPI)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$PROJECT_DIR/admin-backend
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo -e "${GREEN}✅ 默认后端服务文件已创建${NC}"
fi

# 重新加载 systemd
systemctl daemon-reload
echo -e "${GREEN}✅ Systemd 配置已重载${NC}"

echo ""
echo "=== 步骤 4: 启用并启动服务 ==="

# 停止可能正在运行的服务
echo "停止旧服务..."
systemctl stop liaotian-frontend 2>/dev/null || true
systemctl stop liaotian-backend 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 3

# 启用服务（开机自启动）
systemctl enable liaotian-backend
systemctl enable liaotian-frontend
echo -e "${GREEN}✅ 服务已设置为开机自启动${NC}"

# 启动服务
echo "启动后端服务..."
systemctl start liaotian-backend
sleep 5

echo "启动前端服务..."
systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== 步骤 5: 验证服务状态 ==="

# 检查后端
if systemctl is-active --quiet liaotian-backend; then
    echo -e "${GREEN}✅ 后端服务运行中${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败${NC}"
    echo "查看日志: sudo journalctl -u liaotian-backend -n 50"
fi

# 检查前端
if systemctl is-active --quiet liaotian-frontend; then
    echo -e "${GREEN}✅ 前端服务运行中${NC}"
else
    echo -e "${RED}❌ 前端服务启动失败${NC}"
    echo "查看日志: sudo journalctl -u liaotian-frontend -n 50"
fi

# 检查端口
echo ""
echo "检查端口状态..."
if ss -tlnp | grep :8000 > /dev/null; then
    echo -e "${GREEN}✅ 端口 8000 监听中${NC}"
else
    echo -e "${YELLOW}⚠️  端口 8000 未监听${NC}"
fi

if ss -tlnp | grep :3000 > /dev/null; then
    echo -e "${GREEN}✅ 端口 3000 监听中${NC}"
else
    echo -e "${YELLOW}⚠️  端口 3000 未监听${NC}"
fi

# 检查 Nginx
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx 运行中${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx 未运行${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}✅ 配置完成！${NC}"
echo "========================================="
echo ""
echo "服务管理命令："
echo "  查看状态: sudo systemctl status liaotian-frontend"
echo "            sudo systemctl status liaotian-backend"
echo "  查看日志: sudo journalctl -u liaotian-frontend -f"
echo "            sudo journalctl -u liaotian-backend -f"
echo "  重启服务: sudo systemctl restart liaotian-frontend"
echo "            sudo systemctl restart liaotian-backend"
echo ""
echo "Nginx 管理命令："
echo "  测试配置: sudo nginx -t"
echo "  重载配置: sudo systemctl reload nginx"
echo "  查看日志: sudo tail -f /var/log/nginx/liaotian-access.log"
echo ""
echo "访问地址："
echo "  前端: http://165.154.233.55/"
echo "  后端 API: http://165.154.233.55/api"
echo "  API 文档: http://165.154.233.55/docs"
