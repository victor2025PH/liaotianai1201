# 🖥️ 服務器腳本說明

## 📋 腳本列表

### 設置和安裝

1. **`install-dependencies.sh`** - 安裝所有依賴
   - 一鍵執行：`bash scripts/server/install-dependencies.sh`
   - 功能：安裝 Python 和 Node.js 依賴，包括 Gunicorn

2. **`setup-server.sh`** - 完整服務器設置
   - 一鍵執行：`bash scripts/server/setup-server.sh`
   - 功能：安裝依賴、設置數據庫、配置安全設置

### 啟動服務

3. **`start-all-services.sh`** - 啟動所有服務
   - 一鍵執行：`bash scripts/server/start-all-services.sh`
   - 功能：啟動後端和前端服務（使用 screen）

4. **`quick-start.sh`** - 快速啟動（不需要 Gunicorn）
   - 一鍵執行：`bash scripts/server/quick-start.sh`
   - 功能：使用 Uvicorn 快速啟動後端服務

### 測試和驗證

5. **`auto-test-and-fix.sh`** - 自動測試和修復
   - 一鍵執行：`bash scripts/server/auto-test-and-fix.sh`

6. **`verify-services.sh`** - 驗證服務狀態
   - 一鍵執行：`bash scripts/server/verify-services.sh`

7. **`run-all-tasks.sh`** - 執行所有任務
   - 一鍵執行：`bash scripts/server/run-all-tasks.sh`

## 🚀 快速開始

### 首次設置

```bash
# 一鍵設置
bash scripts/server/setup-server.sh
```

### 啟動服務

```bash
# 方式 1: 使用 Gunicorn（生產環境）
bash scripts/server/start-all-services.sh

# 方式 2: 快速啟動（開發環境，不需要 Gunicorn）
bash scripts/server/quick-start.sh
```

### 驗證服務

```bash
bash scripts/server/verify-services.sh
```

## 📝 常見問題

### 問題 1: Gunicorn 未找到

**解決方案：**
```bash
# 安裝 Gunicorn
cd admin-backend
source venv/bin/activate
pip install gunicorn[gevent]

# 或使用快速啟動（不需要 Gunicorn）
bash scripts/server/quick-start.sh
```

### 問題 2: 腳本文件不存在

**解決方案：**
```bash
# 從項目根目錄執行
cd /path/to/telegram-ai-system
bash scripts/server/quick-start.sh
```

### 問題 3: 權限問題

**解決方案：**
```bash
# 設置執行權限
chmod +x scripts/server/*.sh
```

---

**最後更新：** 2025-01-17

