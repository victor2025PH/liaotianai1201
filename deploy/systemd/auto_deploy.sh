#!/bin/bash

# 自动化部署脚本
# 用于检查和完成 systemd 服务部署

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量（请根据实际情况修改）
PROJECT_ROOT="/opt/smart-tg"
BACKEND_DIR="$PROJECT_ROOT/admin-backend"
FRONTEND_DIR="$PROJECT_ROOT/saas-demo"
BACKEND_SERVICE="smart-tg-backend"
FRONTEND_SERVICE="smart-tg-frontend"
SERVICE_USER="www-data"

echo "=========================================="
echo "Smart TG 自动化部署脚本"
echo "=========================================="
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}错误: 请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 步骤 1: 检查当前部署状态
echo -e "${BLUE}[步骤 1/8] 检查当前部署状态...${NC}"
echo ""

# 检查服务文件
echo "检查服务文件..."
if [ -f "/etc/systemd/system/$BACKEND_SERVICE.service" ]; then
    echo -e "${GREEN}✓ 后端服务文件存在${NC}"
else
    echo -e "${YELLOW}⚠ 后端服务文件不存在，将在后续步骤创建${NC}"
fi

if [ -f "/etc/systemd/system/$FRONTEND_SERVICE.service" ]; then
    echo -e "${GREEN}✓ 前端服务文件存在${NC}"
else
    echo -e "${YELLOW}⚠ 前端服务文件不存在，将在后续步骤创建${NC}"
fi

# 检查服务状态
echo ""
echo "检查服务状态..."
if systemctl is-active --quiet $BACKEND_SERVICE 2>/dev/null; then
    echo -e "${GREEN}✓ 后端服务正在运行${NC}"
    BACKEND_RUNNING=true
else
    echo -e "${YELLOW}⚠ 后端服务未运行${NC}"
    BACKEND_RUNNING=false
fi

if systemctl is-active --quiet $FRONTEND_SERVICE 2>/dev/null; then
    echo -e "${GREEN}✓ 前端服务正在运行${NC}"
    FRONTEND_RUNNING=true
else
    echo -e "${YELLOW}⚠ 前端服务未运行${NC}"
    FRONTEND_RUNNING=false
fi

# 检查端口
echo ""
echo "检查端口占用..."
if netstat -tlnp 2>/dev/null | grep -q ":8000"; then
    echo -e "${GREEN}✓ 端口 8000 已被占用${NC}"
else
    echo -e "${YELLOW}⚠ 端口 8000 未被占用${NC}"
fi

if netstat -tlnp 2>/dev/null | grep -q ":3000"; then
    echo -e "${GREEN}✓ 端口 3000 已被占用${NC}"
else
    echo -e "${YELLOW}⚠ 端口 3000 未被占用${NC}"
fi

# 步骤 2: 检查目录结构
echo ""
echo -e "${BLUE}[步骤 2/8] 检查目录结构...${NC}"
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${YELLOW}⚠ 项目根目录不存在，创建: $PROJECT_ROOT${NC}"
    mkdir -p $PROJECT_ROOT/{admin-backend,saas-demo,data,logs}
    chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_ROOT
fi

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}✗ 后端目录不存在: $BACKEND_DIR${NC}"
    echo "  请先上传后端代码到此目录"
    exit 1
else
    echo -e "${GREEN}✓ 后端目录存在${NC}"
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}✗ 前端目录不存在: $FRONTEND_DIR${NC}"
    echo "  请先上传前端代码到此目录"
    exit 1
else
    echo -e "${GREEN}✓ 前端目录存在${NC}"
fi

# 步骤 3: 检查后端环境
echo ""
echo -e "${BLUE}[步骤 3/8] 检查后端环境...${NC}"
cd $BACKEND_DIR

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠ 虚拟环境不存在，正在创建...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        pip install gunicorn
    else
        echo -e "${RED}✗ requirements.txt 不存在${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ 虚拟环境存在${NC}"
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env 文件不存在，请创建并配置${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "  已从 .env.example 创建 .env，请编辑配置"
    fi
else
    echo -e "${GREEN}✓ .env 文件存在${NC}"
fi

# 步骤 4: 检查前端环境
echo ""
echo -e "${BLUE}[步骤 4/8] 检查前端环境...${NC}"
cd $FRONTEND_DIR

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠ node_modules 不存在，正在安装依赖...${NC}"
    npm install
else
    echo -e "${GREEN}✓ node_modules 存在${NC}"
fi

# 检查 .env.local
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}⚠ .env.local 文件不存在，请创建并配置${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env.local
        echo "  已从 .env.example 创建 .env.local，请编辑配置"
    fi
else
    echo -e "${GREEN}✓ .env.local 文件存在${NC}"
fi

# 检查构建
if [ ! -d ".next" ]; then
    echo -e "${YELLOW}⚠ Next.js 构建目录不存在，正在构建...${NC}"
    npm run build
else
    echo -e "${GREEN}✓ Next.js 构建目录存在${NC}"
fi

# 步骤 5: 创建 systemd 服务文件
echo ""
echo -e "${BLUE}[步骤 5/8] 创建 systemd 服务文件...${NC}"

# 获取当前脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 复制服务文件
if [ -f "$SCRIPT_DIR/smart-tg-backend.service" ]; then
    cp $SCRIPT_DIR/smart-tg-backend.service /etc/systemd/system/$BACKEND_SERVICE.service
    
    # 替换路径占位符
    sed -i "s|/opt/smart-tg|$PROJECT_ROOT|g" /etc/systemd/system/$BACKEND_SERVICE.service
    
    echo -e "${GREEN}✓ 后端服务文件已创建${NC}"
else
    echo -e "${RED}✗ 找不到后端服务文件模板${NC}"
    exit 1
fi

if [ -f "$SCRIPT_DIR/smart-tg-frontend.service" ]; then
    cp $SCRIPT_DIR/smart-tg-frontend.service /etc/systemd/system/$FRONTEND_SERVICE.service
    
    # 替换路径占位符
    sed -i "s|/opt/smart-tg|$PROJECT_ROOT|g" /etc/systemd/system/$FRONTEND_SERVICE.service
    
    echo -e "${GREEN}✓ 前端服务文件已创建${NC}"
else
    echo -e "${RED}✗ 找不到前端服务文件模板${NC}"
    exit 1
fi

# 步骤 6: 设置权限
echo ""
echo -e "${BLUE}[步骤 6/8] 设置权限...${NC}"
chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_ROOT
chmod -R 755 $PROJECT_ROOT
chmod 600 $BACKEND_DIR/.env 2>/dev/null || true
chmod 600 $FRONTEND_DIR/.env.local 2>/dev/null || true
echo -e "${GREEN}✓ 权限已设置${NC}"

# 步骤 7: 初始化数据库（如果需要）
echo ""
echo -e "${BLUE}[步骤 7/8] 初始化数据库...${NC}"
cd $BACKEND_DIR
source .venv/bin/activate

if [ -f "init_db_tables.py" ]; then
    echo "运行数据库初始化..."
    python init_db_tables.py || echo -e "${YELLOW}⚠ 数据库初始化可能已存在${NC}"
fi

if [ -f "alembic.ini" ]; then
    echo "运行数据库迁移..."
    alembic upgrade head || echo -e "${YELLOW}⚠ 数据库迁移可能已完成${NC}"
fi

# 步骤 8: 启动服务
echo ""
echo -e "${BLUE}[步骤 8/8] 启动服务...${NC}"

# 重新加载 systemd
systemctl daemon-reload
echo -e "${GREEN}✓ systemd 配置已重新加载${NC}"

# 启动后端服务
if [ "$BACKEND_RUNNING" = false ]; then
    systemctl enable $BACKEND_SERVICE
    systemctl start $BACKEND_SERVICE
    sleep 3
    if systemctl is-active --quiet $BACKEND_SERVICE; then
        echo -e "${GREEN}✓ 后端服务已启动${NC}"
    else
        echo -e "${RED}✗ 后端服务启动失败${NC}"
        echo "查看日志: journalctl -u $BACKEND_SERVICE -n 50"
        exit 1
    fi
else
    echo -e "${GREEN}✓ 后端服务已在运行${NC}"
fi

# 启动前端服务
if [ "$FRONTEND_RUNNING" = false ]; then
    systemctl enable $FRONTEND_SERVICE
    systemctl start $FRONTEND_SERVICE
    sleep 3
    if systemctl is-active --quiet $FRONTEND_SERVICE; then
        echo -e "${GREEN}✓ 前端服务已启动${NC}"
    else
        echo -e "${RED}✗ 前端服务启动失败${NC}"
        echo "查看日志: journalctl -u $FRONTEND_SERVICE -n 50"
        exit 1
    fi
else
    echo -e "${GREEN}✓ 前端服务已在运行${NC}"
fi

# 最终检查
echo ""
echo "=========================================="
echo "部署完成！进行最终检查..."
echo "=========================================="
echo ""

# 检查健康端点
echo "检查后端健康端点..."
sleep 2
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ 后端健康检查通过${NC}"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
else
    echo -e "${YELLOW}⚠ 后端健康检查失败，服务可能还在启动中${NC}"
fi

echo ""
echo "检查前端服务..."
if curl -s -f http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✓ 前端服务可访问${NC}"
else
    echo -e "${YELLOW}⚠ 前端服务不可访问，服务可能还在启动中${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "服务状态:"
systemctl status $BACKEND_SERVICE --no-pager -l | head -n 3
systemctl status $FRONTEND_SERVICE --no-pager -l | head -n 3
echo ""
echo "查看日志:"
echo "  sudo journalctl -u $BACKEND_SERVICE -f"
echo "  sudo journalctl -u $FRONTEND_SERVICE -f"
echo ""
echo "服务管理:"
echo "  启动: sudo systemctl start $BACKEND_SERVICE"
echo "  停止: sudo systemctl stop $BACKEND_SERVICE"
echo "  重启: sudo systemctl restart $BACKEND_SERVICE"
echo ""

