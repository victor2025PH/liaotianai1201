# 快速部署命令清單

請按照以下順序執行命令。**每次SSH連接時，當提示輸入密碼時，輸入: `Along2025!!!`**

## 步驟1: 清理SSH主機密鑰（已完成）

```powershell
ssh-keygen -R 165.154.254.99
```

## 步驟2: 測試SSH連接

```powershell
ssh -o StrictHostKeyChecking=accept-new root@165.154.254.99 "echo '連接成功'"
```

**提示**: 輸入密碼 `Along2025!!!`

## 步驟3: 執行基礎環境部署

複製以下命令並執行（會提示輸入密碼）：

```powershell
ssh root@165.154.254.99 "bash -s" << 'REMOTE_SCRIPT'
set -e
DEPLOY_DIR="/opt/group-ai"
echo "=== 開始遠程部署 ==="
echo "[1/8] 更新系統..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get upgrade -y -qq
echo "[2/8] 安裝基礎工具..."
apt-get install -y -qq curl wget git vim htop net-tools ufw build-essential software-properties-common python3-pip python3-venv python3-dev
echo "[3/8] 安裝Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa > /dev/null 2>&1
apt-get update -qq && apt-get install -y -qq python3.11 python3.11-venv python3.11-dev
echo "[4/8] 配置系統限制..."
cat >> /etc/security/limits.conf << 'LIMITS'
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
LIMITS
echo "[5/8] 配置時區..."
timedatectl set-timezone Asia/Shanghai
echo "[6/8] 配置防火牆..."
ufw --force enable && ufw allow 22/tcp && ufw allow 8000/tcp
echo "[7/8] 創建目錄結構..."
mkdir -p $DEPLOY_DIR/{sessions,logs,configs,ai_models/group_scripts,data} && chmod -R 755 $DEPLOY_DIR
echo "[8/8] 創建Python虛擬環境..."
python3.11 -m venv $DEPLOY_DIR/venv
$DEPLOY_DIR/venv/bin/pip install --upgrade pip setuptools wheel
echo "=== 基礎環境部署完成 ==="
REMOTE_SCRIPT
```

## 步驟4: 上傳項目文件

```powershell
# 進入項目目錄
cd "E:\002-工作文件\重要程序\聊天AI群聊程序"

# 打包項目文件
tar czf group-ai-deploy.tar.gz group_ai_service/ admin-backend/app/api/group_ai/ config.py 2>$null

# 上傳到服務器（需要輸入密碼）
scp group-ai-deploy.tar.gz root@165.154.254.99:/tmp/

# 在服務器上解壓
ssh root@165.154.254.99 "cd /opt/group-ai && tar xzf /tmp/group-ai-deploy.tar.gz && rm /tmp/group-ai-deploy.tar.gz"
```

## 步驟5: 安裝Python依賴

```powershell
ssh root@165.154.254.99 "bash -s" << 'REMOTE_SCRIPT'
cd /opt/group-ai
source venv/bin/activate

# 創建requirements.txt
cat > requirements.txt << 'EOF'
pyrogram>=2.0.0
tgcrypto>=1.2.5
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
sqlalchemy>=2.0.0
alembic>=1.12.0
aiosqlite>=0.19.0
redis>=5.0.0
hiredis>=2.2.0
openai>=1.0.0
tiktoken>=0.5.0
python-dotenv>=1.0.0
pyyaml>=6.0
aiofiles>=23.2.0
httpx>=0.25.0
prometheus-client>=0.19.0
EOF

# 安裝依賴
pip install -r requirements.txt
echo "=== Python依賴安裝完成 ==="
REMOTE_SCRIPT
```

## 步驟6: 創建配置文件

```powershell
ssh root@165.154.254.99 "cat > /opt/group-ai/.env << 'EOF'
# 應用配置
APP_NAME=Group AI Worker Node
APP_ENV=production
DEBUG=false
NODE_ID=worker-01
NODE_ROLE=worker

# 數據庫配置
DATABASE_URL=sqlite:////opt/group-ai/data/group_ai.db

# Telegram API配置（需要修改）
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# OpenAI配置（需要修改）
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Session文件配置
SESSION_FILES_DIRECTORY=/opt/group-ai/sessions
SESSION_FILES_BACKUP_DIRECTORY=/opt/group-ai/sessions_backup

# 帳號配置
MAX_ACCOUNTS_PER_NODE=5
ACCOUNT_HEALTH_CHECK_INTERVAL=60
ACCOUNT_RECONNECT_DELAY=5
ACCOUNT_MAX_RECONNECT_ATTEMPTS=3

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=/opt/group-ai/logs/worker.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10

# 監控配置
METRICS_ENABLED=true
METRICS_PORT=9091
HEARTBEAT_INTERVAL=30
EOF"
```

## 步驟7: 創建config.py

```powershell
ssh root@165.154.254.99 "cat > /opt/group-ai/config.py << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API配置
API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '')

# OpenAI配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
EOF"
```

## 步驟8: 配置API密鑰

**重要**: 請編輯配置文件並填入正確的API密鑰

```powershell
# 連接到服務器
ssh root@165.154.254.99

# 在服務器上執行（需要修改以下值）:
vi /opt/group-ai/.env
```

需要修改：
- `TELEGRAM_API_ID`: 從 https://my.telegram.org 獲取
- `TELEGRAM_API_HASH`: 從 https://my.telegram.org 獲取  
- `OPENAI_API_KEY`: 您的OpenAI API Key（如果使用）

## 步驟9: 上傳Session文件

```powershell
# 上傳Session文件到服務器
scp *.session root@165.154.254.99:/opt/group-ai/sessions/
```

## 步驟10: 創建啟動腳本和systemd服務

```powershell
ssh root@165.154.254.99 "bash -s" << 'REMOTE_SCRIPT'
# 創建啟動腳本
cat > /opt/group-ai/start.sh << 'EOF'
#!/bin/bash
cd /opt/group-ai
source venv/bin/activate
export PYTHONPATH=/opt/group-ai:\$PYTHONPATH

if [ -d "admin-backend" ]; then
    cd admin-backend
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    python -m group_ai_service.main --host 0.0.0.0 --port 8000
fi
EOF
chmod +x /opt/group-ai/start.sh

# 創建systemd服務
cat > /etc/systemd/system/group-ai-worker.service << 'EOF'
[Unit]
Description=Group AI Worker Node Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/group-ai
Environment="PATH=/opt/group-ai/venv/bin"
Environment="PYTHONPATH=/opt/group-ai"
ExecStart=/opt/group-ai/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 啟動服務
systemctl daemon-reload
systemctl enable group-ai-worker
systemctl start group-ai-worker
systemctl status group-ai-worker
REMOTE_SCRIPT
```

## 步驟11: 驗證部署

```powershell
# 檢查服務狀態
ssh root@165.154.254.99 "systemctl status group-ai-worker"

# 檢查端口
ssh root@165.154.254.99 "netstat -tlnp | grep 8000"

# 測試API（如果服務已啟動）
curl http://165.154.254.99:8000/health

# 查看日誌
ssh root@165.154.254.99 "tail -f /opt/group-ai/logs/worker.log"
```

## 一鍵執行所有步驟（需要多次輸入密碼）

如果您想一次性執行所有步驟，可以複製以下完整腳本：

```powershell
# 設置變量
$RemoteHost = "165.154.254.99"
$RemoteUser = "root"
$RemotePassword = "Along2025!!!"

# 清理SSH主機密鑰
ssh-keygen -R $RemoteHost

# 測試連接
Write-Host "測試SSH連接（輸入密碼: $RemotePassword）..." -ForegroundColor Yellow
ssh -o StrictHostKeyChecking=accept-new "${RemoteUser}@${RemoteHost}" "echo '連接成功'"

# 執行基礎環境部署
Write-Host "`n執行基礎環境部署（輸入密碼: $RemotePassword）..." -ForegroundColor Yellow
ssh "${RemoteUser}@${RemoteHost}" "bash -s" << 'REMOTE_SCRIPT'
# ... (這裡插入步驟3的腳本內容)
REMOTE_SCRIPT

# 繼續執行其他步驟...
```

## 注意事項

1. **每次SSH連接都需要輸入密碼**: `Along2025!!!`
2. **步驟3（基礎環境部署）可能需要10-15分鐘**，請耐心等待
3. **步驟5（安裝Python依賴）可能需要5-10分鐘**，請耐心等待
4. **如果某個步驟失敗**，請查看錯誤信息，可能需要手動執行
5. **建議配置SSH密鑰**，部署完成後可以避免每次輸入密碼

## 需要幫助？

如果遇到問題，請查看：
- [分步部署指南](./step_by_step_deploy.md)
- [遠程服務器快速部署指南](../docs/部署方案/遠程服務器快速部署指南.md)

