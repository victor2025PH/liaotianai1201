# 🖥️ 服務器部署快速指南

## 🚀 一鍵執行命令

### 首次部署（完整設置）

```bash
# 從項目根目錄執行
bash scripts/server/setup-server.sh
```

這會自動：
1. 安裝所有依賴（Python、Node.js、Gunicorn）
2. 設置數據庫
3. 配置安全設置
4. 驗證配置

### 啟動服務

#### 方式 1: 使用 Gunicorn（生產環境，推薦）

```bash
# 一鍵執行
bash scripts/server/start-all-services.sh
```

#### 方式 2: 快速啟動（開發環境，不需要 Gunicorn）

```bash
# 一鍵執行
bash scripts/server/quick-start.sh
```

### 驗證服務

```bash
# 一鍵執行
bash scripts/server/verify-services.sh
```

---

## 📋 分步執行命令

### 步驟 1: 安裝依賴

```bash
# 進入項目目錄
cd /path/to/telegram-ai-system

# 安裝依賴
bash scripts/server/install-dependencies.sh
```

### 步驟 2: 設置數據庫

```bash
cd admin-backend

# 激活虛擬環境（如果存在）
source venv/bin/activate

# 設置數據庫 URL
export DATABASE_URL="sqlite:///./admin.db"

# 初始化數據庫
python init_db_tables.py
```

### 步驟 3: 啟動服務

#### 使用 Uvicorn（不需要 Gunicorn）

```bash
cd admin-backend
source venv/bin/activate  # 如果存在
export DATABASE_URL="sqlite:///./admin.db"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 使用 Gunicorn（生產環境）

```bash
# 先安裝 Gunicorn
pip install gunicorn[gevent]

# 啟動服務
cd admin-backend
source venv/bin/activate
export DATABASE_URL="sqlite:///./admin.db"
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 步驟 4: 驗證服務

```bash
# 檢查健康狀態
curl http://localhost:8000/health

# 檢查 API 文檔
curl http://localhost:8000/docs
```

---

## ⚠️ 常見問題解決

### 問題 1: `gunicorn: command not found`

**解決方案 A: 安裝 Gunicorn**
```bash
cd admin-backend
source venv/bin/activate
pip install gunicorn[gevent]
```

**解決方案 B: 使用快速啟動（不需要 Gunicorn）**
```bash
bash scripts/server/quick-start.sh
```

### 問題 2: `scripts/server/start-all-services.sh: No such file or directory`

**解決方案：**
```bash
# 確保在項目根目錄
cd /path/to/telegram-ai-system

# 檢查文件是否存在
ls -la scripts/server/

# 如果不存在，從 GitHub 拉取最新代碼
git pull
```

### 問題 3: 權限問題

**解決方案：**
```bash
# 設置執行權限
chmod +x scripts/server/*.sh

# 然後執行
bash scripts/server/quick-start.sh
```

---

## 📁 服務器腳本位置

所有服務器腳本都在：`scripts/server/`

- `install-dependencies.sh` - 安裝依賴
- `setup-server.sh` - 完整設置
- `start-all-services.sh` - 啟動所有服務
- `quick-start.sh` - 快速啟動（推薦，不需要 Gunicorn）
- `verify-services.sh` - 驗證服務
- `auto-test-and-fix.sh` - 自動測試和修復

---

## ✅ 推薦流程

### 首次部署

```bash
# 1. 完整設置
bash scripts/server/setup-server.sh

# 2. 快速啟動（不需要 Gunicorn）
bash scripts/server/quick-start.sh
```

### 日常啟動

```bash
# 快速啟動
bash scripts/server/quick-start.sh
```

---

**最後更新：** 2025-01-17

