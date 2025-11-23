# 快速開始指南

> **更新日期**: 2024-12-19

---

## 系統概述

Telegram 群組多 AI 賬號智能管理系統，支持：
- 1-100 個 AI 賬號管理
- 劇本驅動的智能對話
- 紅包檢測和參與
- 實時監控和調控

---

## 前置要求

### 環境要求
- Python 3.9+
- Node.js 18+
- PostgreSQL (可選，開發環境可用 SQLite)
- Telegram API 憑證 (API_ID, API_HASH)

### 依賴安裝

**後端**:
```bash
cd admin-backend
pip install -r requirements.txt
```

**前端**:
```bash
cd saas-demo
npm install
```

---

## 快速啟動

### 1. 配置環境變量

創建 `.env` 文件（後端）:
```env
# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# OpenAI API (可選，用於 AI 生成)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-3.5-turbo

# 數據庫
DATABASE_URL=sqlite:///./group_ai.db
```

創建 `.env.local` 文件（前端）:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 2. 初始化數據庫

```bash
cd admin-backend
alembic upgrade head
```

### 3. 啟動後端服務

```bash
cd admin-backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

後端 API 將在 `http://localhost:8000` 運行。

### 4. 啟動前端服務

```bash
cd saas-demo
npm run dev
```

前端將在 `http://localhost:3000` 運行。

---

## 使用流程

### 1. 準備 Session 文件

將 Telegram session 文件放在 `sessions/` 目錄下：
```
sessions/
  ├── account1.session
  ├── account2.session
  └── ...
```

### 2. 創建劇本

通過前端界面或 API 創建對話劇本：

**前端**: 訪問 `http://localhost:3000/group-ai/scripts`，點擊「創建劇本」

**API**:
```bash
curl -X POST http://localhost:8000/api/v1/group-ai/scripts/ \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "daily_chat",
    "name": "日常聊天",
    "version": "1.0",
    "yaml_content": "..."
  }'
```

### 3. 添加賬號

**前端**: 訪問 `http://localhost:3000/group-ai/accounts`，點擊「添加賬號」

**API**:
```bash
curl -X POST http://localhost:8000/api/v1/group-ai/accounts/ \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "account_001",
    "session_file": "sessions/account1.session",
    "script_id": "daily_chat",
    "group_ids": [-1001234567890]
  }'
```

### 4. 啟動賬號

**前端**: 在賬號列表中點擊「啟動」按鈕

**API**:
```bash
curl -X POST http://localhost:8000/api/v1/group-ai/accounts/account_001/start
```

### 5. 監控運行狀態

訪問 `http://localhost:3000/group-ai/monitor` 查看：
- 系統指標
- 賬號指標
- 告警列表

### 6. 調整參數

訪問 `http://localhost:3000/group-ai/accounts/account_001/params` 調整：
- 回復頻率
- 紅包參與概率
- 其他行為參數

---

## 測試

### 單元測試

```bash
# 測試賬號管理器
py scripts/test_account_manager_quick.py

# 測試劇本引擎
py scripts/test_script_engine.py

# 測試對話管理器
py scripts/test_dialogue_manager.py

# 測試紅包處理器
py scripts/test_redpacket_handler.py

# 測試監控服務
py scripts/test_monitor_service.py
```

### 集成測試

```bash
py scripts/integration_test.py
```

### API 測試

```bash
# 測試賬號 API
py scripts/test_api_accounts.py

# 測試劇本 API
py scripts/test_scripts_api.py
```

---

## 常見問題

### 1. Session 文件無效

確保：
- Session 文件路徑正確
- Session 文件未過期
- 有正確的 API_ID 和 API_HASH

### 2. 賬號無法啟動

檢查：
- Session 文件是否存在
- 賬號配置是否正確
- 日誌中的錯誤信息

### 3. 劇本無法加載

確保：
- YAML 格式正確
- 劇本 ID 唯一
- 場景配置完整

### 4. 前端無法連接後端

檢查：
- 後端服務是否運行
- API URL 配置是否正確
- CORS 設置是否正確

---

## 下一步

1. **完善 Telegram API 集成**
   - 實現實際的搶紅包操作
   - 處理 FloodWait 錯誤

2. **性能優化**
   - 上下文緩存
   - 批量處理
   - 數據庫優化

3. **功能增強**
   - 新成員檢測
   - 話題追蹤
   - 更多策略

---

## 獲取幫助

- 查看文檔: `docs/` 目錄
- 查看代碼註釋
- 檢查日誌文件

---

**狀態**: ✅ 系統可運行，核心功能完整

