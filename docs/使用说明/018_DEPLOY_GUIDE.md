# 部署指南

本文檔提供完整的部署指南，包括本地開發環境啟動、數據庫初始化、環境變量配置、生產環境部署和健康檢查。

> **文檔版本**: v1.0  
> **最後更新**: 2024-12-19  
> **適用於**: 聊天AI08-繼續開發項目

---

## 目錄

1. [本地開發啟動](#本地開發啟動)
2. [數據庫初始化與遷移](#數據庫初始化與遷移)
3. [環境變量說明](#環境變量說明)
4. [生產環境部署流程](#生產環境部署流程)
5. [健康檢查與驗證步驟](#健康檢查與驗證步驟)

---

## 本地開發啟動

### 前置要求

- **Python**: 3.11+
- **Node.js**: 18+ (LTS)
- **Poetry**: Python 依賴管理工具
- **npm/yarn**: Node.js 包管理器
- **Git**: 版本控制

### 1. 後端（admin-backend）啟動

#### 1.1 安裝依賴

```bash
# 進入後端目錄
cd admin-backend

# 安裝 Poetry（如果未安裝）
pip install poetry

# 安裝項目依賴
poetry install
```

#### 1.2 配置環境變量

創建 `.env` 文件（在 `admin-backend/` 目錄或項目根目錄）：

```bash
# 數據庫配置
DATABASE_URL=sqlite:///./admin.db
# 或使用 PostgreSQL（生產環境）
# DATABASE_URL=postgresql://user:password@localhost:5432/admin_db

# Redis 配置（可選）
REDIS_URL=redis://localhost:6379/0

# JWT 配置（必須修改）
JWT_SECRET=your-secret-key-change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 管理員初始化配置
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123

# 外部服務 URL（可選）
SESSION_SERVICE_URL=http://localhost:8001
REDPACKET_SERVICE_URL=http://localhost:8002
MONITORING_SERVICE_URL=http://localhost:8003
```

#### 1.3 啟動服務

```bash
# 使用 Poetry 運行
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Python 直接運行
poetry run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**預期輸出**：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**驗證**：
- 訪問 `http://localhost:8000/docs` 查看 Swagger API 文檔
- 訪問 `http://localhost:8000/health` 應該返回 `{"status": "ok"}`

---

### 2. 前端（saas-demo）啟動

#### 2.1 安裝依賴

```bash
# 進入前端目錄
cd saas-demo

# 安裝依賴
npm install
# 或使用 yarn
yarn install
```

#### 2.2 配置環境變量

創建 `.env.local` 文件（在 `saas-demo/` 目錄）：

```bash
# API 基礎地址
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

> **注意**：Next.js 中只有以 `NEXT_PUBLIC_` 開頭的環境變量才會暴露給瀏覽器。修改環境變量後需要重啟開發服務器。

#### 2.3 啟動開發服務器

```bash
npm run dev
# 或使用 yarn
yarn dev
```

**預期輸出**：
```
  ▲ Next.js 16.0.2
  - Local:        http://localhost:3000
  - ready started server on 0.0.0.0:3000
```

**驗證**：
- 訪問 `http://localhost:3000` 應該看到 Dashboard 頁面
- 如果後端未運行，會自動切換到 Mock 數據並顯示提示

---

### 3. 前端（admin-frontend）啟動

#### 3.1 安裝依賴

```bash
# 進入前端目錄
cd admin-frontend

# 安裝依賴
npm install
# 或使用 yarn
yarn install
```

#### 3.2 配置環境變量

創建 `.env.local` 文件（在 `admin-frontend/` 目錄）：

```bash
# API 基礎地址
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

> **注意**：Vite 中只有以 `VITE_` 開頭的環境變量才會暴露給瀏覽器。修改環境變量後需要重啟開發服務器。

#### 3.3 啟動開發服務器

```bash
npm run dev
# 或使用 yarn
yarn dev
```

**預期輸出**：
```
  VITE v5.4.10  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**驗證**：
- 訪問 `http://localhost:5173` 應該看到 Dashboard 頁面

---

### 4. 主程序（main.py）啟動

#### 4.1 安裝依賴

```bash
# 在項目根目錄
pip install -r requirements.txt
```

#### 4.2 配置環境變量

創建 `.env` 文件（在項目根目錄）：

```bash
# Telegram API 配置（必填）
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_SESSION_NAME=your_session_name
TELEGRAM_SESSION_FILE=./sessions/your_session.session

# OpenAI API 配置（必填）
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_VISION_MODEL=gpt-4o-mini

# 語音功能配置（可選）
ENABLE_VOICE_RESPONSES=1
MIN_VOICE_DURATION_SEC=1
MAX_VOICE_DURATION_SEC=120
MAX_VOICE_FILE_MB=8

# 騰訊雲配置（可選，用於 TTS）
TENCENT_SECRET_ID=your_tencent_secret_id
TENCENT_SECRET_KEY=your_tencent_secret_key
```

#### 4.3 啟動主程序

```bash
python main.py
```

**預期輸出**：
```
[INFO] 初始化數據庫...
[INFO] 初始化 Excel...
[INFO] 啟動 Pyrogram 客戶端...
[INFO] 註冊消息處理器...
[INFO] 啟動後台任務...
[INFO] 進入 idle 狀態...
```

---

## 數據庫初始化與遷移

### admin-backend 數據庫

#### 自動初始化（推薦）

後端服務啟動時會自動初始化數據庫：

1. 自動創建表結構（`Base.metadata.create_all()`）
2. 創建默認管理員用戶（如果不存在）
3. 創建默認角色和權限

**首次啟動後**：
- 數據庫文件：`admin-backend/admin.db`（SQLite）
- 默認管理員：`admin@example.com` / `changeme123`
- **重要**：首次登錄後應立即修改密碼

#### 手動初始化

如果需要手動初始化：

```bash
cd admin-backend

# 使用 Poetry 運行初始化腳本
poetry run python -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"

# 或使用 Python 直接運行
python -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"
```

#### 使用 PostgreSQL（生產環境）

1. **創建數據庫**：
   ```bash
   createdb admin_db
   # 或使用 psql
   psql -U postgres -c "CREATE DATABASE admin_db;"
   ```

2. **配置環境變量**：
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/admin_db
   ```

3. **啟動服務**（會自動創建表）：
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

#### 數據庫遷移（使用 Alembic）

**初始化 Alembic**（如果尚未初始化）：

```bash
cd admin-backend
poetry run alembic init alembic
```

**配置 `alembic.ini` 和 `alembic/env.py`**：
- 設置 `sqlalchemy.url` 從環境變量讀取
- 設置 `target_metadata = Base.metadata`

**創建遷移**：
```bash
poetry run alembic revision --autogenerate -m "描述"
```

**應用遷移**：
```bash
poetry run alembic upgrade head
```

**回滾遷移**：
```bash
poetry run alembic downgrade -1  # 回滾一個版本
poetry run alembic downgrade base  # 回滾到初始狀態
```

---

### 主程序數據庫（chat_history.db）

#### 自動初始化

主程序啟動時會自動初始化：

1. 創建 `data/` 目錄（如果不存在）
2. 創建 `chat_history.db` 數據庫
3. 創建必要的表結構

#### 手動遷移

如果需要執行數據庫遷移：

```bash
# 在項目根目錄
python -m scripts.run_migrations
```

**遷移流程**：
1. 自動備份數據庫到 `backup/db_bak/`
2. 檢查已應用的遷移
3. 執行未應用的遷移
4. 更新遷移記錄

---

## 環境變量說明

### 快速配置

複製環境變量示例文件：

```bash
# 後端環境變量
cp docs/env.example admin-backend/.env

# 主程序環境變量
cp docs/env.example .env
```

### 環境變量分類

詳細的環境變量說明請參考：`docs/CONFIG_ENV_MATRIX.md`

#### 必填環境變量

**後端（admin-backend）**：
- `JWT_SECRET`：**必須修改**，用於簽名 JWT Token（至少 32 字符）

**主程序（main.py）**：
- `TELEGRAM_API_ID`：Telegram API ID
- `TELEGRAM_API_HASH`：Telegram API Hash
- `TELEGRAM_SESSION_NAME`：會話名稱
- `OPENAI_API_KEY`：OpenAI API Key

#### 可選環境變量

**後端**：
- `DATABASE_URL`：數據庫連接（默認：SQLite）
- `REDIS_URL`：Redis 連接（可選）
- `ADMIN_DEFAULT_EMAIL`：默認管理員郵箱
- `ADMIN_DEFAULT_PASSWORD`：默認管理員密碼

**前端（saas-demo）**：
- `NEXT_PUBLIC_API_BASE_URL`：API 基礎地址（默認：`http://localhost:8000/api/v1`）

**前端（admin-frontend）**：
- `VITE_API_BASE_URL`：API 基礎地址（默認：`http://localhost:8000/api/v1`）

**主程序**：
- `OPENAI_MODEL`：OpenAI 模型（默認：`gpt-4`）
- `ENABLE_VOICE_RESPONSES`：是否啟用語音回復（默認：`1`）
- `TENCENT_SECRET_ID`、`TENCENT_SECRET_KEY`：騰訊雲配置（可選）

---

## 生產環境部署流程

### 方式 1：Docker Compose（推薦）

#### 1.1 準備環境

```bash
# 確保已安裝 Docker 和 Docker Compose
docker --version
docker compose version
```

#### 1.2 配置環境變量

在項目根目錄創建 `.env` 文件：

```bash
# 後端配置
DATABASE_URL=postgresql://user:password@postgres:5432/admin_db
REDIS_URL=redis://redis:6379/0
JWT_SECRET=your-production-secret-key-change-me
ADMIN_DEFAULT_EMAIL=admin@yourdomain.com
ADMIN_DEFAULT_PASSWORD=your-strong-password

# 外部服務 URL
SESSION_SERVICE_URL=http://session-service:8001
REDPACKET_SERVICE_URL=http://redpacket-service:8002
MONITORING_SERVICE_URL=http://monitoring-service:8003

# Telegram 配置
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_SESSION_NAME=your_session_name

# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key
```

#### 1.3 構建 Docker 鏡像

```bash
# 構建所有服務
docker compose -f deploy/docker-compose.yaml build

# 或單獨構建
docker build -t admin-backend:latest -f admin-backend/Dockerfile admin-backend
docker build -t admin-frontend:latest -f admin-frontend/Dockerfile admin-frontend
docker build -t session-service:latest -f deploy/session-service.Dockerfile .
```

#### 1.4 啟動服務

```bash
# 啟動所有服務
docker compose -f deploy/docker-compose.yaml up -d

# 查看日誌
docker compose -f deploy/docker-compose.yaml logs -f

# 查看特定服務日誌
docker compose -f deploy/docker-compose.yaml logs -f admin-backend
```

#### 1.5 停止服務

```bash
# 停止所有服務
docker compose -f deploy/docker-compose.yaml down

# 停止並刪除數據卷
docker compose -f deploy/docker-compose.yaml down -v
```

#### 1.6 更新服務

```bash
# 拉取最新代碼
git pull

# 重新構建並啟動
docker compose -f deploy/docker-compose.yaml up -d --build
```

---

### 方式 2：PM2（Node.js 進程管理）

#### 2.1 安裝 PM2

```bash
npm install -g pm2
```

#### 2.2 配置 PM2 生態系統文件

創建 `ecosystem.config.js`（在項目根目錄）：

```javascript
module.exports = {
  apps: [
    {
      name: 'admin-backend',
      script: 'poetry',
      args: 'run uvicorn app.main:app --host 0.0.0.0 --port 8000',
      cwd: './admin-backend',
      interpreter: 'none',
      env: {
        DATABASE_URL: 'postgresql://user:password@localhost:5432/admin_db',
        REDIS_URL: 'redis://localhost:6379/0',
        JWT_SECRET: 'your-production-secret-key',
      },
      instances: 2,
      exec_mode: 'cluster',
      error_file: './logs/admin-backend-error.log',
      out_file: './logs/admin-backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
    },
    {
      name: 'saas-demo',
      script: 'npm',
      args: 'run start',
      cwd: './saas-demo',
      env: {
        NODE_ENV: 'production',
        NEXT_PUBLIC_API_BASE_URL: 'http://localhost:8000/api/v1',
      },
      instances: 2,
      exec_mode: 'cluster',
      error_file: './logs/saas-demo-error.log',
      out_file: './logs/saas-demo-out.log',
      autorestart: true,
    },
    {
      name: 'main-bot',
      script: 'python',
      args: 'main.py',
      cwd: './',
      env: {
        TELEGRAM_API_ID: '123456',
        TELEGRAM_API_HASH: 'your_telegram_api_hash',
        OPENAI_API_KEY: 'your_openai_api_key',
      },
      error_file: './logs/main-bot-error.log',
      out_file: './logs/main-bot-out.log',
      autorestart: true,
      max_restarts: 10,
    },
  ],
};
```

#### 2.3 啟動服務

```bash
# 啟動所有服務
pm2 start ecosystem.config.js

# 查看狀態
pm2 status

# 查看日誌
pm2 logs

# 查看特定服務日誌
pm2 logs admin-backend
```

#### 2.4 管理服務

```bash
# 停止服務
pm2 stop admin-backend

# 重啟服務
pm2 restart admin-backend

# 刪除服務
pm2 delete admin-backend

# 保存當前配置
pm2 save

# 設置開機自啟
pm2 startup
```

---

### 方式 3：systemd（Linux 系統服務）

#### 3.1 創建 systemd 服務文件

創建 `/etc/systemd/system/admin-backend.service`：

```ini
[Unit]
Description=Admin Backend API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/chat-ai08/admin-backend
Environment="PATH=/opt/chat-ai08/admin-backend/.venv/bin"
ExecStart=/opt/chat-ai08/admin-backend/.venv/bin/poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
EnvironmentFile=/opt/chat-ai08/.env

[Install]
WantedBy=multi-user.target
```

#### 3.2 啟動服務

```bash
# 重新加載 systemd 配置
sudo systemctl daemon-reload

# 啟動服務
sudo systemctl start admin-backend

# 設置開機自啟
sudo systemctl enable admin-backend

# 查看狀態
sudo systemctl status admin-backend

# 查看日誌
sudo journalctl -u admin-backend -f
```

---

## 健康檢查與驗證步驟

### 1. 後端健康檢查

#### 1.1 基礎健康檢查

```bash
# 檢查健康端點
curl http://localhost:8000/health

# 預期響應：
# {"status":"ok"}
```

#### 1.2 API 端點檢查

```bash
# Dashboard API
curl http://localhost:8000/api/v1/dashboard

# Metrics API
curl http://localhost:8000/api/v1/metrics

# Sessions API
curl "http://localhost:8000/api/v1/sessions?page=1&page_size=10"

# Logs API
curl "http://localhost:8000/api/v1/logs?page=1&page_size=10"

# System Monitor API
curl http://localhost:8000/api/v1/system/monitor

# Alert Settings API
curl http://localhost:8000/api/v1/settings/alerts
```

**預期結果**：
- 所有端點返回 200 狀態碼
- 返回有效的 JSON 數據
- 沒有 500 錯誤

---

### 2. 前端健康檢查

#### 2.1 saas-demo（Next.js）

**訪問頁面**：
- `http://localhost:3000/` - Dashboard
- `http://localhost:3000/sessions` - 會話列表
- `http://localhost:3000/logs` - 日誌中心
- `http://localhost:3000/monitoring` - 系統監控
- `http://localhost:3000/settings/alerts` - 告警設置

**檢查點**：
- [ ] 頁面正常渲染，無白屏
- [ ] 統計卡片顯示數據（或 Skeleton 加載狀態）
- [ ] 圖表正常顯示（或顯示「暫無數據」）
- [ ] 表格正常顯示（或顯示空狀態）
- [ ] 如果後端不可用，顯示 Mock 數據提示

#### 2.2 admin-frontend（Vite + React）

**訪問頁面**：
- `http://localhost:5173/` - Dashboard
- `http://localhost:5173/accounts` - 賬戶管理
- `http://localhost:5173/activities` - 活動記錄

**檢查點**：
- [ ] 頁面正常渲染，無白屏
- [ ] 側邊欄導航正常
- [ ] API 請求返回 200 狀態碼
- [ ] 數據正常顯示

---

### 3. 一鍵檢查腳本

#### Bash 腳本（Linux/macOS）

創建 `scripts/health_check.sh`：

```bash
#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== 後端健康檢查 ==="

# 檢查後端健康端點
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✓ 後端健康檢查通過${NC}"
else
    echo -e "${RED}✗ 後端健康檢查失敗${NC}"
    exit 1
fi

# 檢查 Dashboard API
if curl -s http://localhost:8000/api/v1/dashboard | grep -q "stats"; then
    echo -e "${GREEN}✓ Dashboard API 正常${NC}"
else
    echo -e "${YELLOW}⚠ Dashboard API 可能異常${NC}"
fi

# 檢查前端
if curl -s http://localhost:3000 | grep -q "<!DOCTYPE html"; then
    echo -e "${GREEN}✓ saas-demo 前端正常運行${NC}"
else
    echo -e "${RED}✗ saas-demo 前端未運行或異常${NC}"
fi

echo ""
echo "=== 檢查完成 ==="
```

**使用方式**：
```bash
chmod +x scripts/health_check.sh
./scripts/health_check.sh
```

#### PowerShell 腳本（Windows）

創建 `scripts/health_check.ps1`：

```powershell
Write-Host "=== 後端健康檢查 ===" -ForegroundColor Cyan

$healthCheck = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
if ($healthCheck.StatusCode -eq 200 -and $healthCheck.Content -like '*"status":"ok"*') {
    Write-Host "✓ 後端健康檢查通過" -ForegroundColor Green
} else {
    Write-Host "✗ 後端健康檢查失敗" -ForegroundColor Red
    exit 1
}

$dashboard = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/dashboard" -UseBasicParsing
if ($dashboard.StatusCode -eq 200) {
    Write-Host "✓ Dashboard API 正常" -ForegroundColor Green
} else {
    Write-Host "⚠ Dashboard API 異常" -ForegroundColor Yellow
}

Write-Host "`n=== 檢查完成 ===" -ForegroundColor Cyan
```

**使用方式**：
```powershell
powershell -ExecutionPolicy Bypass -File scripts/health_check.ps1
```

---

### 4. 完整驗證清單

#### 部署前檢查

- [ ] 所有環境變量已正確配置
- [ ] 數據庫已初始化
- [ ] 依賴已安裝
- [ ] 端口未被佔用
- [ ] 防火牆規則已配置（生產環境）

#### 部署後檢查

- [ ] 後端健康檢查通過（`/health`）
- [ ] 所有 API 端點正常響應
- [ ] 前端頁面正常加載
- [ ] 數據庫連接正常
- [ ] Redis 連接正常（如果使用）
- [ ] 外部服務連接正常（如果使用）
- [ ] 日誌文件正常生成
- [ ] 錯誤處理正常（Mock Fallback 機制）

#### 生產環境額外檢查

- [ ] HTTPS 已配置（如果使用）
- [ ] CORS 配置正確
- [ ] 認證機制已啟用
- [ ] 日誌輪轉已配置
- [ ] 監控告警已配置
- [ ] 備份機制已配置
- [ ] 回滾方案已準備

---

## 故障排查

### 問題 1：後端無法啟動

**排查步驟**：
1. 檢查端口是否被佔用：`lsof -i :8000`（Linux/macOS）或 `netstat -ano | findstr :8000`（Windows）
2. 檢查環境變量是否正確：`echo $DATABASE_URL`
3. 檢查依賴是否安裝：`poetry install`
4. 查看日誌：`poetry run uvicorn app.main:app --reload` 的終端輸出

### 問題 2：前端無法連接到後端

**排查步驟**：
1. 確認後端服務正在運行
2. 檢查 `NEXT_PUBLIC_API_BASE_URL` 或 `VITE_API_BASE_URL` 是否正確
3. 檢查瀏覽器控制台的 Network 面板
4. 檢查 CORS 配置（`admin-backend/app/main.py`）

### 問題 3：數據庫連接失敗

**排查步驟**：
1. 檢查 `DATABASE_URL` 是否正確
2. 檢查數據庫服務是否運行（PostgreSQL）
3. 檢查數據庫文件權限（SQLite）
4. 查看後端日誌中的數據庫錯誤信息

### 問題 4：Docker 容器無法啟動

**排查步驟**：
1. 查看容器日誌：`docker compose logs <service-name>`
2. 檢查環境變量文件（`.env`）是否存在
3. 檢查 Docker 鏡像是否構建成功：`docker images`
4. 檢查端口衝突：`docker ps`

---

## 總結

本部署指南涵蓋了：

1. ✅ **本地開發啟動**：後端、前端、主程序的完整啟動流程
2. ✅ **數據庫初始化與遷移**：自動和手動初始化方法
3. ✅ **環境變量說明**：必填和可選環境變量的配置
4. ✅ **生產環境部署**：Docker Compose、PM2、systemd 三種部署方式
5. ✅ **健康檢查與驗證**：完整的檢查步驟和驗證清單

**下一步**：
- 根據實際環境調整配置
- 設置監控和告警（參考 `docs/MONITORING_AND_ALERTING_CHECKLIST.md`）
- 配置 CI/CD 流程（參考 `.github/workflows/ci.yml`）

---

**最後更新**: 2024-12-19  
**文檔維護**: 請根據實際部署環境及時更新本文檔

