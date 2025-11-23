#!/bin/bash
# 遠程工作節點自動部署腳本
# 用於在遠程服務器上部署群組AI工作節點

set -e

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變量（可通過環境變量覆蓋）
REMOTE_HOST="${REMOTE_HOST:-165.154.254.99}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_PASSWORD="${REMOTE_PASSWORD:-Along2025!!!}"
NODE_ID="${NODE_ID:-worker-01}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/group-ai}"
MAX_ACCOUNTS="${MAX_ACCOUNTS:-5}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  群組AI工作節點遠程部署腳本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}部署目標:${NC}"
echo -e "  主機: ${REMOTE_HOST}"
echo -e "  用戶: ${REMOTE_USER}"
echo -e "  節點ID: ${NODE_ID}"
echo -e "  部署目錄: ${DEPLOY_DIR}"
echo -e "  最大帳號數: ${MAX_ACCOUNTS}"
echo ""

# 檢查必要的工具
check_requirements() {
    echo -e "${GREEN}[1/10] 檢查本地環境...${NC}"
    
    if ! command -v sshpass &> /dev/null; then
        echo -e "${YELLOW}⚠ sshpass 未安裝，嘗試安裝...${NC}"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update && sudo apt-get install -y sshpass
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install hudochenkov/sshpass/sshpass || echo -e "${RED}✗ 請手動安裝 sshpass: brew install hudochenkov/sshpass/sshpass${NC}"
        fi
    fi
    
    if ! command -v ssh &> /dev/null; then
        echo -e "${RED}✗ SSH 未安裝${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 環境檢查完成${NC}"
}

# 測試SSH連接
test_ssh_connection() {
    echo -e "${GREEN}[2/10] 測試SSH連接...${NC}"
    
    if sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        "${REMOTE_USER}@${REMOTE_HOST}" "echo 'SSH連接成功'" 2>/dev/null; then
        echo -e "${GREEN}✓ SSH連接成功${NC}"
    else
        echo -e "${RED}✗ SSH連接失敗，請檢查：${NC}"
        echo -e "  - 服務器IP地址: ${REMOTE_HOST}"
        echo -e "  - 用戶名: ${REMOTE_USER}"
        echo -e "  - 密碼: ${REMOTE_PASSWORD}"
        echo -e "  - 防火牆是否開放22端口"
        exit 1
    fi
}

# 在遠程服務器上執行命令
remote_exec() {
    sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no \
        "${REMOTE_USER}@${REMOTE_HOST}" "$@"
}

# 上傳文件到遠程服務器
remote_upload() {
    local local_file=$1
    local remote_file=$2
    sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no \
        "${local_file}" "${REMOTE_USER}@${REMOTE_HOST}:${remote_file}"
}

# 部署腳本主體
deploy_remote() {
    echo -e "${GREEN}[3/10] 準備遠程部署環境...${NC}"
    
    # 創建部署腳本內容
    cat > /tmp/remote_deploy.sh << 'REMOTE_SCRIPT'
#!/bin/bash
set -e

DEPLOY_DIR="${1:-/opt/group-ai}"
NODE_ID="${2:-worker-01}"
MAX_ACCOUNTS="${3:-5}"

echo "=== 開始遠程部署 ==="
echo "部署目錄: ${DEPLOY_DIR}"
echo "節點ID: ${NODE_ID}"
echo "最大帳號數: ${MAX_ACCOUNTS}"

# 1. 更新系統
echo "[1/8] 更新系統..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

# 2. 安裝基礎工具
echo "[2/8] 安裝基礎工具..."
apt-get install -y -qq \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    ufw \
    build-essential \
    software-properties-common \
    python3-pip \
    python3-venv \
    python3-dev

# 3. 安裝Python 3.11
echo "[3/8] 安裝Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa > /dev/null 2>&1
apt-get update -qq
apt-get install -y -qq python3.11 python3.11-venv python3.11-dev

# 4. 配置系統限制
echo "[4/8] 配置系統限制..."
cat >> /etc/security/limits.conf << EOF
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOF

# 5. 配置時區
echo "[5/8] 配置時區..."
timedatectl set-timezone Asia/Shanghai

# 6. 配置防火牆
echo "[6/8] 配置防火牆..."
ufw --force enable
ufw allow 22/tcp
ufw allow 8000/tcp

# 7. 創建部署目錄結構
echo "[7/8] 創建目錄結構..."
mkdir -p ${DEPLOY_DIR}/{sessions,logs,configs,ai_models/group_scripts}
chmod -R 755 ${DEPLOY_DIR}

# 8. 創建Python虛擬環境
echo "[8/8] 創建Python虛擬環境..."
python3.11 -m venv ${DEPLOY_DIR}/venv
${DEPLOY_DIR}/venv/bin/pip install --upgrade pip setuptools wheel

echo "=== 基礎環境部署完成 ==="
REMOTE_SCRIPT

    # 上傳並執行部署腳本
    remote_upload /tmp/remote_deploy.sh /tmp/remote_deploy.sh
    remote_exec "chmod +x /tmp/remote_deploy.sh && /tmp/remote_deploy.sh ${DEPLOY_DIR} ${NODE_ID} ${MAX_ACCOUNTS}"
    
    echo -e "${GREEN}✓ 遠程環境準備完成${NC}"
}

# 上傳項目文件
upload_project_files() {
    echo -e "${GREEN}[4/10] 上傳項目文件...${NC}"
    
    # 獲取項目根目錄
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    
    # 創建臨時打包目錄
    TEMP_DIR=$(mktemp -d)
    echo "打包項目文件到: ${TEMP_DIR}"
    
    # 複製必要的文件
    mkdir -p "${TEMP_DIR}/group_ai_service"
    cp -r "${PROJECT_ROOT}/group_ai_service"/* "${TEMP_DIR}/group_ai_service/" 2>/dev/null || true
    
    mkdir -p "${TEMP_DIR}/admin-backend/app/api/group_ai"
    cp -r "${PROJECT_ROOT}/admin-backend/app/api/group_ai"/* "${TEMP_DIR}/admin-backend/app/api/group_ai/" 2>/dev/null || true
    
    # 複製配置文件
    if [ -f "${PROJECT_ROOT}/config.py" ]; then
        cp "${PROJECT_ROOT}/config.py" "${TEMP_DIR}/"
    fi
    
    # 複製requirements文件
    if [ -f "${PROJECT_ROOT}/admin-backend/requirements.txt" ]; then
        cp "${PROJECT_ROOT}/admin-backend/requirements.txt" "${TEMP_DIR}/requirements.txt"
    elif [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
        cp "${PROJECT_ROOT}/requirements.txt" "${TEMP_DIR}/requirements.txt"
    fi
    
    # 打包
    cd "${TEMP_DIR}"
    tar czf /tmp/group-ai-deploy.tar.gz .
    
    # 上傳到遠程服務器
    remote_upload /tmp/group-ai-deploy.tar.gz /tmp/group-ai-deploy.tar.gz
    
    # 在遠程服務器上解壓
    remote_exec "cd ${DEPLOY_DIR} && tar xzf /tmp/group-ai-deploy.tar.gz && rm /tmp/group-ai-deploy.tar.gz"
    
    # 清理
    rm -rf "${TEMP_DIR}" /tmp/group-ai-deploy.tar.gz
    
    echo -e "${GREEN}✓ 項目文件上傳完成${NC}"
}

# 安裝Python依賴
install_dependencies() {
    echo -e "${GREEN}[5/10] 安裝Python依賴...${NC}"
    
    # 創建requirements.txt（如果不存在）
    remote_exec "cat > ${DEPLOY_DIR}/requirements.txt << 'EOF'
# 核心依賴
pyrogram>=2.0.0
tgcrypto>=1.2.5
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# 數據庫
sqlalchemy>=2.0.0
alembic>=1.12.0
aiosqlite>=0.19.0

# Redis
redis>=5.0.0
hiredis>=2.2.0

# AI相關
openai>=1.0.0
tiktoken>=0.5.0

# 工具庫
python-dotenv>=1.0.0
pyyaml>=6.0
aiofiles>=23.2.0
httpx>=0.25.0

# 監控
prometheus-client>=0.19.0
EOF"
    
    # 安裝依賴
    remote_exec "${DEPLOY_DIR}/venv/bin/pip install -r ${DEPLOY_DIR}/requirements.txt"
    
    echo -e "${GREEN}✓ Python依賴安裝完成${NC}"
}

# 創建配置文件
create_config_files() {
    echo -e "${GREEN}[6/10] 創建配置文件...${NC}"
    
    # 創建.env文件
    remote_exec "cat > ${DEPLOY_DIR}/.env << EOF
# 應用配置
APP_NAME=Group AI Worker Node
APP_ENV=production
DEBUG=false
NODE_ID=${NODE_ID}
NODE_ROLE=worker

# 主節點配置（如果有的話）
MASTER_NODE_URL=http://localhost:8000
MASTER_NODE_API_KEY=

# 數據庫配置（使用SQLite作為測試）
DATABASE_URL=sqlite:///${DEPLOY_DIR}/data/group_ai.db

# Redis配置（可選）
REDIS_URL=

# Telegram API配置（需要用戶提供）
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# OpenAI配置（需要用戶提供）
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Session文件配置
SESSION_FILES_DIRECTORY=${DEPLOY_DIR}/sessions
SESSION_FILES_BACKUP_DIRECTORY=${DEPLOY_DIR}/sessions_backup

# 帳號配置
MAX_ACCOUNTS_PER_NODE=${MAX_ACCOUNTS}
ACCOUNT_HEALTH_CHECK_INTERVAL=60
ACCOUNT_RECONNECT_DELAY=5
ACCOUNT_MAX_RECONNECT_ATTEMPTS=3

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=${DEPLOY_DIR}/logs/worker.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10

# 監控配置
METRICS_ENABLED=true
METRICS_PORT=9091
HEARTBEAT_INTERVAL=30
EOF"
    
    # 創建config.py（如果不存在）
    remote_exec "if [ ! -f ${DEPLOY_DIR}/config.py ]; then
        cat > ${DEPLOY_DIR}/config.py << 'PYEOF'
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API配置
API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '')

# OpenAI配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
PYEOF
    fi"
    
    # 創建數據目錄
    remote_exec "mkdir -p ${DEPLOY_DIR}/data"
    
    echo -e "${GREEN}✓ 配置文件創建完成${NC}"
    echo -e "${YELLOW}⚠ 請記得編輯 ${DEPLOY_DIR}/.env 文件，填入正確的API密鑰${NC}"
}

# 創建systemd服務
create_systemd_service() {
    echo -e "${GREEN}[7/10] 創建systemd服務...${NC}"
    
    remote_exec "cat > /tmp/group-ai-worker.service << EOF
[Unit]
Description=Group AI Worker Node Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${DEPLOY_DIR}
Environment=\"PATH=${DEPLOY_DIR}/venv/bin\"
ExecStart=${DEPLOY_DIR}/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    sudo mv /tmp/group-ai-worker.service /etc/systemd/system/
    sudo systemctl daemon-reload"
    
    echo -e "${GREEN}✓ systemd服務創建完成${NC}"
}

# 創建啟動腳本
create_startup_scripts() {
    echo -e "${GREEN}[8/10] 創建啟動腳本...${NC}"
    
    remote_exec "cat > ${DEPLOY_DIR}/start.sh << 'EOF'
#!/bin/bash
cd ${DEPLOY_DIR}
source venv/bin/activate
export PYTHONPATH=\${DEPLOY_DIR}:\${PYTHONPATH}
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF
    chmod +x ${DEPLOY_DIR}/start.sh"
    
    remote_exec "cat > ${DEPLOY_DIR}/stop.sh << 'EOF'
#!/bin/bash
pkill -f 'uvicorn app.main:app' || true
EOF
    chmod +x ${DEPLOY_DIR}/stop.sh"
    
    echo -e "${GREEN}✓ 啟動腳本創建完成${NC}"
}

# 健康檢查
health_check() {
    echo -e "${GREEN}[9/10] 執行健康檢查...${NC}"
    
    # 檢查Python環境
    if remote_exec "${DEPLOY_DIR}/venv/bin/python --version" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Python環境正常${NC}"
    else
        echo -e "${RED}✗ Python環境異常${NC}"
    fi
    
    # 檢查目錄結構
    if remote_exec "test -d ${DEPLOY_DIR}/sessions && test -d ${DEPLOY_DIR}/logs" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 目錄結構正常${NC}"
    else
        echo -e "${RED}✗ 目錄結構異常${NC}"
    fi
    
    echo -e "${GREEN}✓ 健康檢查完成${NC}"
}

# 顯示部署信息
show_deployment_info() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}  部署完成！${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${GREEN}部署信息:${NC}"
    echo -e "  服務器: ${REMOTE_HOST}"
    echo -e "  部署目錄: ${DEPLOY_DIR}"
    echo -e "  節點ID: ${NODE_ID}"
    echo ""
    echo -e "${YELLOW}下一步操作:${NC}"
    echo -e "  1. 編輯配置文件:"
    echo -e "     ssh ${REMOTE_USER}@${REMOTE_HOST}"
    echo -e "     vi ${DEPLOY_DIR}/.env"
    echo ""
    echo -e "  2. 上傳Session文件到:"
    echo -e "     ${DEPLOY_DIR}/sessions/"
    echo ""
    echo -e "  3. 啟動服務:"
    echo -e "     ssh ${REMOTE_USER}@${REMOTE_HOST} '${DEPLOY_DIR}/start.sh'"
    echo ""
    echo -e "  或使用systemd:"
    echo -e "     ssh ${REMOTE_USER}@${REMOTE_HOST} 'sudo systemctl start group-ai-worker'"
    echo ""
    echo -e "  4. 查看日誌:"
    echo -e "     ssh ${REMOTE_USER}@${REMOTE_HOST} 'tail -f ${DEPLOY_DIR}/logs/worker.log'"
    echo ""
}

# 主函數
main() {
    check_requirements
    test_ssh_connection
    deploy_remote
    upload_project_files
    install_dependencies
    create_config_files
    create_systemd_service
    create_startup_scripts
    health_check
    show_deployment_info
}

# 執行主函數
main

