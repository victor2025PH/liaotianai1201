#!/bin/bash

# 部署状态检查脚本
# 用于检查 systemd 服务的部署状态

echo "=========================================="
echo "Smart TG 部署状态检查"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查后端服务
echo "1. 检查后端服务 (smart-tg-backend)..."
if systemctl is-active --quiet smart-tg-backend; then
    echo -e "${GREEN}✓ 后端服务正在运行${NC}"
    systemctl status smart-tg-backend --no-pager -l | head -n 5
else
    echo -e "${RED}✗ 后端服务未运行${NC}"
    if systemctl is-enabled --quiet smart-tg-backend; then
        echo "  服务已启用但未运行，尝试查看日志:"
        echo "  sudo journalctl -u smart-tg-backend -n 20"
    else
        echo "  服务未启用，需要执行:"
        echo "  sudo systemctl enable smart-tg-backend"
        echo "  sudo systemctl start smart-tg-backend"
    fi
fi

echo ""

# 检查前端服务
echo "2. 检查前端服务 (smart-tg-frontend)..."
if systemctl is-active --quiet smart-tg-frontend; then
    echo -e "${GREEN}✓ 前端服务正在运行${NC}"
    systemctl status smart-tg-frontend --no-pager -l | head -n 5
else
    echo -e "${RED}✗ 前端服务未运行${NC}"
    if systemctl is-enabled --quiet smart-tg-frontend; then
        echo "  服务已启用但未运行，尝试查看日志:"
        echo "  sudo journalctl -u smart-tg-frontend -n 20"
    else
        echo "  服务未启用，需要执行:"
        echo "  sudo systemctl enable smart-tg-frontend"
        echo "  sudo systemctl start smart-tg-frontend"
    fi
fi

echo ""

# 检查端口
echo "3. 检查端口占用..."
if netstat -tlnp 2>/dev/null | grep -q ":8000"; then
    echo -e "${GREEN}✓ 端口 8000 已被占用（后端）${NC}"
    netstat -tlnp 2>/dev/null | grep ":8000" | head -n 1
else
    echo -e "${YELLOW}⚠ 端口 8000 未被占用${NC}"
fi

if netstat -tlnp 2>/dev/null | grep -q ":3000"; then
    echo -e "${GREEN}✓ 端口 3000 已被占用（前端）${NC}"
    netstat -tlnp 2>/dev/null | grep ":3000" | head -n 1
else
    echo -e "${YELLOW}⚠ 端口 3000 未被占用${NC}"
fi

echo ""

# 检查健康端点
echo "4. 检查健康端点..."
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端健康检查通过${NC}"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
else
    echo -e "${RED}✗ 后端健康检查失败${NC}"
    echo "  无法连接到 http://localhost:8000/health"
fi

echo ""

# 检查前端
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务可访问${NC}"
else
    echo -e "${RED}✗ 前端服务不可访问${NC}"
    echo "  无法连接到 http://localhost:3000"
fi

echo ""

# 检查目录和文件
echo "5. 检查关键目录和文件..."
BACKEND_DIR="/opt/smart-tg/admin-backend"
FRONTEND_DIR="/opt/smart-tg/saas-demo"

if [ -d "$BACKEND_DIR" ]; then
    echo -e "${GREEN}✓ 后端目录存在: $BACKEND_DIR${NC}"
    if [ -f "$BACKEND_DIR/.env" ]; then
        echo -e "${GREEN}  ✓ .env 文件存在${NC}"
    else
        echo -e "${YELLOW}  ⚠ .env 文件不存在${NC}"
    fi
    if [ -d "$BACKEND_DIR/.venv" ]; then
        echo -e "${GREEN}  ✓ 虚拟环境存在${NC}"
    else
        echo -e "${YELLOW}  ⚠ 虚拟环境不存在${NC}"
    fi
else
    echo -e "${RED}✗ 后端目录不存在: $BACKEND_DIR${NC}"
fi

if [ -d "$FRONTEND_DIR" ]; then
    echo -e "${GREEN}✓ 前端目录存在: $FRONTEND_DIR${NC}"
    if [ -f "$FRONTEND_DIR/.env.local" ]; then
        echo -e "${GREEN}  ✓ .env.local 文件存在${NC}"
    else
        echo -e "${YELLOW}  ⚠ .env.local 文件不存在${NC}"
    fi
    if [ -d "$FRONTEND_DIR/.next" ]; then
        echo -e "${GREEN}  ✓ Next.js 构建目录存在${NC}"
    else
        echo -e "${YELLOW}  ⚠ Next.js 构建目录不存在（需要运行 npm run build）${NC}"
    fi
else
    echo -e "${RED}✗ 前端目录不存在: $FRONTEND_DIR${NC}"
fi

echo ""

# 总结
echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""
echo "如果服务未运行，请执行:"
echo "  sudo systemctl start smart-tg-backend"
echo "  sudo systemctl start smart-tg-frontend"
echo ""
echo "查看日志:"
echo "  sudo journalctl -u smart-tg-backend -f"
echo "  sudo journalctl -u smart-tg-frontend -f"
echo ""

