#!/bin/bash
# 自动化部署脚本 - 部署到远程服务器
# 使用方法: ./deploy_to_server.sh <server_ip> <username> <password> [server_name]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 参数
SERVER_IP="${1:-165.154.255.48}"
USERNAME="${2:-ubuntu}"
PASSWORD="${3:-8iDcGrYb52Fxpzee}"
SERVER_NAME="${4:-server}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}自动化部署到远程服务器${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "服务器: ${CYAN}${SERVER_NAME}${NC} (${SERVER_IP})"
echo -e "用户名: ${CYAN}${USERNAME}${NC}"
echo ""

# 检查 sshpass 是否安装
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}警告: sshpass 未安装，将使用交互式密码输入${NC}"
    SSH_CMD="ssh"
    SCP_CMD="scp"
else
    export SSHPASS="${PASSWORD}"
    SSH_CMD="sshpass -e ssh -o StrictHostKeyChecking=no"
    SCP_CMD="sshpass -e scp -o StrictHostKeyChecking=no"
fi

# 测试连接
echo -e "${CYAN}[1/8] 测试服务器连接...${NC}"
if $SSH_CMD "${USERNAME}@${SERVER_IP}" "echo '连接成功'" 2>/dev/null; then
    echo -e "${GREEN}✓ 服务器连接成功${NC}"
else
    echo -e "${RED}✗ 服务器连接失败${NC}"
    exit 1
fi

# 检查系统环境
echo -e "${CYAN}[2/8] 检查系统环境...${NC}"
$SSH_CMD "${USERNAME}@${SERVER_IP}" << 'EOF'
    echo "=== 系统信息 ==="
    uname -a
    echo ""
    echo "=== Python ==="
    python3 --version || echo "Python3 未安装"
    echo ""
    echo "=== Node.js ==="
    node --version || echo "Node.js 未安装"
    echo ""
    echo "=== Docker ==="
    docker --version || echo "Docker 未安装"
    echo ""
    echo "=== 磁盘空间 ==="
    df -h / | tail -1
EOF

# 创建部署目录
echo -e "${CYAN}[3/8] 创建部署目录...${NC}"
$SSH_CMD "${USERNAME}@${SERVER_IP}" << EOF
    mkdir -p ~/telegram-ai-system
    mkdir -p ~/telegram-ai-system/backups
    mkdir -p ~/telegram-ai-system/sessions
    echo "部署目录已创建"
EOF

# 打包项目文件
echo -e "${CYAN}[4/8] 打包项目文件...${NC}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEMP_DIR=$(mktemp -d)
TAR_FILE="${TEMP_DIR}/telegram-ai-system.tar.gz"

cd "$PROJECT_ROOT"
tar --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='.env.local' \
    --exclude='backups' \
    --exclude='sessions' \
    --exclude='*.log' \
    -czf "$TAR_FILE" .

echo -e "${GREEN}✓ 项目文件已打包${NC}"

# 上传项目文件
echo -e "${CYAN}[5/8] 上传项目文件...${NC}"
$SCP_CMD "$TAR_FILE" "${USERNAME}@${SERVER_IP}:~/telegram-ai-system/"

# 解压并部署
echo -e "${CYAN}[6/8] 解压并部署...${NC}"
$SSH_CMD "${USERNAME}@${SERVER_IP}" << EOF
    cd ~/telegram-ai-system
    tar -xzf telegram-ai-system.tar.gz
    rm telegram-ai-system.tar.gz
    echo "项目文件已解压"
EOF

# 安装依赖和配置
echo -e "${CYAN}[7/8] 安装依赖和配置...${NC}"
$SSH_CMD "${USERNAME}@${SERVER_IP}" << 'ENVEOF'
    cd ~/telegram-ai-system
    
    # 安装 Python 依赖（如果使用 Poetry）
    if command -v poetry &> /dev/null; then
        echo "使用 Poetry 安装依赖..."
        cd admin-backend
        poetry install --no-dev
        cd ..
    elif [ -f "admin-backend/requirements.txt" ]; then
        echo "使用 pip 安装依赖..."
        pip3 install -r admin-backend/requirements.txt
    else
        echo "未找到依赖文件，跳过安装"
    fi
    
    # 创建 .env 文件（如果不存在）
    if [ ! -f "admin-backend/.env" ]; then
        echo "创建 .env 文件..."
        cat > admin-backend/.env << 'EOF'
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
    fi
    
    # 初始化数据库
    if [ -f "admin-backend/alembic.ini" ]; then
        echo "运行数据库迁移..."
        cd admin-backend
        if command -v poetry &> /dev/null; then
            poetry run alembic upgrade head || echo "迁移失败，将使用自动创建表"
        else
            alembic upgrade head || echo "迁移失败，将使用自动创建表"
        fi
        cd ..
    fi
    
    echo "依赖安装和配置完成"
ENVEOF

# 启动服务
echo -e "${CYAN}[8/8] 启动服务...${NC}"
$SSH_CMD "${USERNAME}@${SERVER_IP}" << 'EOF'
    cd ~/telegram-ai-system
    
    # 检查服务是否已运行
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo "后端服务已在运行，跳过启动"
    else
        echo "启动后端服务..."
        cd admin-backend
        nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
        echo $! > ../backend.pid
        cd ..
        echo "后端服务已启动 (PID: $(cat backend.pid))"
    fi
    
    # 等待服务启动
    sleep 5
    
    # 健康检查
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✓ 后端服务健康检查通过"
    else
        echo "✗ 后端服务健康检查失败"
    fi
EOF

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "服务器地址: ${CYAN}http://${SERVER_IP}:8000${NC}"
echo -e "API 文档: ${CYAN}http://${SERVER_IP}:8000/docs${NC}"
echo -e "健康检查: ${CYAN}http://${SERVER_IP}:8000/health${NC}"
echo ""
echo -e "查看日志: ${YELLOW}ssh ${USERNAME}@${SERVER_IP} 'tail -f ~/telegram-ai-system/logs/backend.log'${NC}"
echo -e "停止服务: ${YELLOW}ssh ${USERNAME}@${SERVER_IP} 'kill \$(cat ~/telegram-ai-system/backend.pid)'${NC}"

