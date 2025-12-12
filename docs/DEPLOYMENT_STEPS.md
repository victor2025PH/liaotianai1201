# 完整部署步驟指南

## 📋 目錄

1. [從 GitHub 拉取代碼到服務器](#從-github-拉取代碼到服務器)
2. [安裝依賴](#安裝依賴)
3. [配置環境變量](#配置環境變量)
4. [啟動服務](#啟動服務)

---

## 從 GitHub 拉取代碼到服務器

### 方法 1: 使用 Git Clone（首次部署）

**執行位置：服務器（通過 SSH 登錄）**

```bash
# 步驟 1: 登錄到服務器
# 在本地終端執行（Windows PowerShell 或 CMD）
ssh ubuntu@你的服務器IP

# 步驟 2: 進入項目目錄（如果已存在）或創建新目錄
# 執行位置：服務器
cd /home/ubuntu
# 或者使用項目目錄
cd /opt/luckyred  # 根據你的實際項目路徑

# 步驟 3: 克隆倉庫（如果是新部署）
# 執行位置：服務器
# 作用：從 GitHub 下載完整的項目代碼
git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system

# 步驟 4: 進入項目目錄
# 執行位置：服務器
# 作用：切換到項目根目錄
cd telegram-ai-system

# 步驟 5: 切換到主分支
# 執行位置：服務器
# 作用：確保使用最新的 main 分支代碼
git checkout main
```

### 方法 2: 使用 Git Pull（更新現有代碼）

**執行位置：服務器（通過 SSH 登錄）**

```bash
# 步驟 1: 登錄到服務器
# 在本地終端執行
ssh ubuntu@你的服務器IP

# 步驟 2: 進入項目目錄
# 執行位置：服務器
# 作用：切換到項目根目錄
cd /home/ubuntu/telegram-ai-system
# 或
cd /opt/luckyred

# 步驟 3: 拉取最新代碼
# 執行位置：服務器
# 作用：從 GitHub 獲取最新的代碼更新
git pull origin main

# 如果遇到本地修改衝突，強制拉取（謹慎使用）
# git fetch origin main
# git reset --hard origin/main
```

### 方法 3: 通過 GitHub Actions 自動部署（推薦）

**執行位置：本地（推送代碼到 GitHub）**

```bash
# 步驟 1: 在本地項目目錄
# 執行位置：本地（Windows PowerShell）
cd D:\telegram-ai-system

# 步驟 2: 添加修改的文件
# 作用：將修改的文件添加到 Git 暫存區
git add .

# 步驟 3: 提交更改
# 作用：創建一個提交記錄，包含本次修改的說明
git commit -m "更新代碼：描述你的修改內容"

# 步驟 4: 推送到 GitHub
# 作用：將本地提交推送到遠程倉庫，觸發 GitHub Actions 自動部署
git push origin main
```

**注意：** GitHub Actions 會自動執行部署腳本，無需手動在服務器上操作。

---

## 安裝依賴

### 在服務器上安裝

**執行位置：服務器（通過 SSH 登錄）**

```bash
# 步驟 1: 登錄到服務器
# 在本地終端執行
ssh ubuntu@你的服務器IP

# 步驟 2: 進入項目目錄
# 執行位置：服務器
# 作用：切換到項目根目錄
cd /home/ubuntu/telegram-ai-system
# 或
cd /opt/luckyred

# 步驟 3: 執行安裝腳本
# 執行位置：服務器
# 作用：自動安裝所有 Python 和 Node.js 依賴
bash scripts/server/install-dependencies.sh
```

### 手動安裝（如果腳本失敗）

**執行位置：服務器**

```bash
# === Python 依賴 ===

# 步驟 1: 進入後端目錄
# 作用：切換到後端項目目錄
cd /home/ubuntu/telegram-ai-system/admin-backend

# 步驟 2: 創建虛擬環境
# 作用：創建一個獨立的 Python 環境，避免依賴衝突
python3 -m venv venv

# 步驟 3: 激活虛擬環境
# 作用：啟用虛擬環境，後續的 pip 安裝會安裝到這個環境中
source venv/bin/activate

# 步驟 4: 升級 pip
# 作用：確保使用最新版本的 pip 包管理器
pip install --upgrade pip

# 步驟 5: 安裝 Python 依賴
# 作用：根據 requirements.txt 安裝所有必需的 Python 包
pip install -r requirements.txt

# 步驟 6: 安裝根目錄的額外依賴（如果存在）
# 作用：安裝項目根目錄的額外依賴包
cd ..
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# === Node.js 依賴 ===

# 步驟 7: 進入前端目錄
# 作用：切換到前端項目目錄
cd saas-demo

# 步驟 8: 安裝 Node.js 依賴
# 作用：根據 package.json 安裝所有必需的 Node.js 包
npm install

# 步驟 9: 返回項目根目錄
cd ..
```

---

## 配置環境變量

### 自動配置

**執行位置：服務器**

```bash
# 步驟 1: 登錄到服務器
ssh ubuntu@你的服務器IP

# 步驟 2: 進入項目目錄
cd /home/ubuntu/telegram-ai-system

# 步驟 3: 執行配置腳本
# 作用：自動創建 .env 和 .env.local 文件模板
bash scripts/server/configure-env.sh
```

### 手動配置

**執行位置：服務器**

```bash
# === 後端配置 ===

# 步驟 1: 進入後端目錄
cd /home/ubuntu/telegram-ai-system/admin-backend

# 步驟 2: 創建 .env 文件
# 作用：創建環境變量配置文件
nano .env
# 或使用 vi
# vi .env

# 步驟 3: 填入以下內容（複製並修改）
cat > .env << 'EOF'
# 應用配置
APP_NAME=Smart TG Admin API
DATABASE_URL=sqlite:///./admin.db
REDIS_URL=redis://localhost:6379/0

# JWT 配置（使用下面的命令生成密鑰）
SECRET_KEY=你的安全密鑰
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 管理員默認賬號
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123

# OpenAI API 配置（必需）
OPENAI_API_KEY=你的OpenAI API密鑰
AI_PROVIDER=openai

# Telegram API 配置（可選）
TELEGRAM_API_ID=
TELEGRAM_API_HASH=

# 群組 AI 配置
GROUP_AI_AI_PROVIDER=openai
GROUP_AI_AI_API_KEY=你的OpenAI API密鑰
EOF

# 步驟 4: 生成 JWT Secret Key
# 作用：生成一個安全的隨機密鑰用於 JWT 加密
source venv/bin/activate
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# 複製輸出的密鑰，替換 .env 文件中的 SECRET_KEY

# === 前端配置 ===

# 步驟 5: 進入前端目錄
cd ../saas-demo

# 步驟 6: 創建 .env.local 文件
# 作用：創建前端環境變量配置文件
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_GROUP_AI_API_BASE_URL=http://localhost:8000/api/v1/group-ai
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/notifications/ws
NODE_ENV=development
EOF

# 如果是生產環境，修改為實際的服務器地址：
# NEXT_PUBLIC_API_BASE_URL=https://你的域名/api/v1
```

---

## 啟動服務

### 使用 Systemd 服務（生產環境推薦）

**執行位置：服務器**

```bash
# 步驟 1: 部署 Systemd 服務文件
# 作用：將服務配置文件複製到系統目錄
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/deploy-systemd.sh

# 步驟 2: 啟動後端服務
# 作用：啟動 FastAPI 後端服務
sudo systemctl start luckyred-api

# 步驟 3: 啟動前端服務
# 作用：啟動 Next.js 前端服務
sudo systemctl start liaotian-frontend

# 步驟 4: 啟動 Telegram Bot 服務（如果存在）
# 作用：啟動 Telegram 機器人服務
sudo systemctl start telegram-bot

# 步驟 5: 設置開機自啟
# 作用：確保服務在服務器重啟後自動啟動
sudo systemctl enable luckyred-api
sudo systemctl enable liaotian-frontend
sudo systemctl enable telegram-bot

# 步驟 6: 檢查服務狀態
# 作用：查看服務是否正常運行
sudo systemctl status luckyred-api
sudo systemctl status liaotian-frontend
```

### 手動啟動（開發/測試）

**執行位置：服務器**

```bash
# === 啟動後端 ===

# 步驟 1: 進入後端目錄
cd /home/ubuntu/telegram-ai-system/admin-backend

# 步驟 2: 激活虛擬環境
source venv/bin/activate

# 步驟 3: 啟動後端服務
# 作用：啟動 FastAPI 開發服務器（端口 8000）
uvicorn app.main:app --host 0.0.0.0 --port 8000
# 或使用生產模式
# gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# === 啟動前端（新終端）===

# 步驟 4: 打開新的 SSH 終端，進入前端目錄
cd /home/ubuntu/telegram-ai-system/saas-demo

# 步驟 5: 啟動前端服務
# 作用：啟動 Next.js 開發服務器（端口 3000）
npm run dev
# 或生產模式
# npm run build
# npm start
```

---

## 完整部署流程示例

### 首次部署（從零開始）

**執行位置：服務器**

```bash
# === 1. 拉取代碼 ===
cd /home/ubuntu
git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system
cd telegram-ai-system
git checkout main

# === 2. 安裝依賴 ===
bash scripts/server/install-dependencies.sh

# === 3. 配置環境變量 ===
bash scripts/server/configure-env.sh
# 然後編輯 .env 文件填入 API 密鑰
nano admin-backend/.env

# === 4. 部署服務 ===
sudo bash scripts/server/deploy-systemd.sh

# === 5. 啟動服務 ===
sudo systemctl start luckyred-api
sudo systemctl start liaotian-frontend
sudo systemctl enable luckyred-api
sudo systemctl enable liaotian-frontend

# === 6. 驗證服務 ===
curl http://localhost:8000/health
curl http://localhost:3000
```

### 更新代碼（已有部署）

**執行位置：服務器**

```bash
# === 1. 拉取最新代碼 ===
cd /home/ubuntu/telegram-ai-system
git pull origin main

# === 2. 更新依賴（如果需要）===
cd admin-backend
source venv/bin/activate
pip install -r requirements.txt

cd ../saas-demo
npm install

# === 3. 重啟服務 ===
sudo systemctl restart luckyred-api
sudo systemctl restart liaotian-frontend
```

---

## 命令執行位置說明

| 命令類型 | 執行位置 | 說明 |
|---------|---------|------|
| `git clone/pull` | 服務器 | 從 GitHub 拉取代碼 |
| `git add/commit/push` | 本地 | 推送代碼到 GitHub |
| `bash scripts/server/*.sh` | 服務器 | 執行服務器腳本 |
| `npm install` | 服務器 | 安裝 Node.js 依賴 |
| `pip install` | 服務器 | 安裝 Python 依賴 |
| `systemctl` | 服務器 | 管理系統服務 |
| `ssh` | 本地 | 連接到服務器 |

---

## 故障排查

### 問題 1: Git 拉取失敗

```bash
# 檢查網絡連接
ping github.com

# 檢查 Git 配置
git config --list

# 使用 HTTPS 而不是 SSH（如果 SSH 失敗）
git remote set-url origin https://github.com/victor2025PH/liaotianai1201.git
```

### 問題 2: 虛擬環境不存在

```bash
# 手動創建虛擬環境
cd admin-backend
python3 -m venv venv
source venv/bin/activate
```

### 問題 3: 權限問題

```bash
# 確保腳本有執行權限
chmod +x scripts/server/*.sh

# 確保目錄權限正確
sudo chown -R ubuntu:ubuntu /home/ubuntu/telegram-ai-system
```

---

## 下一步

完成部署後，請參考：
- [配置指南](./CONFIGURATION_GUIDE.md)
- [使用手冊](./USER_MANUAL.md)

