# 逐步測試指南

> **更新日期**: 2024-12-19

---

## 📋 測試前準備

### 1. 檢查環境變量配置

確保項目根目錄有 `.env` 文件，包含以下必要配置：

```env
# Telegram API（必需）
TELEGRAM_API_ID=你的API_ID
TELEGRAM_API_HASH=你的API_HASH

# OpenAI API（用於 AI 生成，必需）
OPENAI_API_KEY=你的OpenAI_Key

# 數據庫（可選，默認使用 SQLite）
DATABASE_URL=sqlite:///./admin.db
```

### 2. 檢查 Session 文件

確保 `sessions/` 目錄下有至少一個有效的 `.session` 文件：

```bash
# 檢查 sessions 目錄
ls sessions/
```

如果沒有，請參考 `docs/GENERATE_SESSION_FILES.md` 生成 session 文件。

---

## 🚀 第一步：啟動後端服務

### 1.1 檢查後端依賴

```bash
cd admin-backend
pip list | grep -E "fastapi|uvicorn|sqlalchemy"
```

如果缺少依賴，安裝：

```bash
# 使用 pip
pip install -r ../requirements.txt

# 或使用 poetry（如果已安裝）
poetry install
```

### 1.2 初始化數據庫

```bash
cd admin-backend
alembic upgrade head
```

### 1.3 啟動後端服務

**方式一：直接啟動（開發模式）**

```bash
cd admin-backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**方式二：使用啟動腳本**

```bash
python scripts/start_system.py
```

### 1.4 驗證後端運行

打開瀏覽器訪問：
- 健康檢查：http://localhost:8000/health
- API 文檔：http://localhost:8000/docs

應該看到：
- `/health` 返回 `{"status": "ok"}`
- `/docs` 顯示 Swagger API 文檔

---

## 🎨 第二步：啟動前端服務

### 2.1 檢查前端依賴

```bash
cd saas-demo
npm list --depth=0
```

如果缺少依賴，安裝：

```bash
cd saas-demo
npm install
```

### 2.2 配置前端 API 地址

檢查 `saas-demo/.env.local` 文件（如果不存在則創建）：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 2.3 啟動前端服務

```bash
cd saas-demo
npm run dev
```

### 2.4 驗證前端運行

打開瀏覽器訪問：http://localhost:3000

應該看到登錄頁面或主界面。

---

## ✅ 第三步：基礎功能測試

### 3.1 測試後端 API（使用 curl 或 Postman）

#### 測試健康檢查

```bash
curl http://localhost:8000/health
```

**預期結果**：
```json
{"status": "ok"}
```

#### 測試賬號列表 API

```bash
curl http://localhost:8000/api/v1/group-ai/accounts/
```

**預期結果**：
```json
[]
```
（初始為空列表）

#### 測試劇本列表 API

```bash
curl http://localhost:8000/api/v1/group-ai/scripts/
```

**預期結果**：
```json
[]
```
（初始為空列表）

#### 測試監控 API

```bash
curl http://localhost:8000/api/v1/group-ai/monitor/system
```

**預期結果**：
```json
{
  "total_accounts": 0,
  "active_accounts": 0,
  "total_messages": 0,
  "total_replies": 0,
  ...
}
```

---

### 3.2 測試前端界面

#### 測試賬號管理頁面

1. 訪問：http://localhost:3000/group-ai/accounts
2. 應該看到：
   - 賬號列表（初始為空）
   - 「添加賬號」按鈕
   - 頁面無錯誤

#### 測試劇本管理頁面

1. 訪問：http://localhost:3000/group-ai/scripts
2. 應該看到：
   - 劇本列表（初始為空）
   - 「創建劇本」按鈕
   - 頁面無錯誤

#### 測試監控頁面

1. 訪問：http://localhost:3000/group-ai/monitor
2. 應該看到：
   - 系統指標卡片
   - 賬號指標列表
   - 告警列表
   - 數據自動刷新（30秒間隔）

---

## 🧪 第四步：功能測試

### 4.1 創建測試劇本

**方式一：通過前端**

1. 訪問：http://localhost:3000/group-ai/scripts
2. 點擊「創建劇本」
3. 填寫：
   - 劇本 ID: `test_script`
   - 名稱: `測試劇本`
   - 版本: `1.0`
   - YAML 內容：
   ```yaml
   scenes:
     - name: greeting
       triggers:
         - keywords: ["你好", "hello"]
       responses:
         - type: text
           content: "你好！很高興認識你。"
   ```
4. 點擊「保存」

**方式二：通過 API**

```bash
curl -X POST http://localhost:8000/api/v1/group-ai/scripts/ \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test_script",
    "name": "測試劇本",
    "version": "1.0",
    "yaml_content": "scenes:\n  - name: greeting\n    triggers:\n      - keywords: [\"你好\", \"hello\"]\n    responses:\n      - type: text\n        content: \"你好！很高興認識你。\""
  }'
```

**驗證**：
- 刷新劇本列表，應該看到新創建的劇本
- 點擊「測試」按鈕，應該能成功解析 YAML

---

### 4.2 添加測試賬號

**前提**：確保 `sessions/` 目錄下有有效的 `.session` 文件

**方式一：通過前端**

1. 訪問：http://localhost:3000/group-ai/accounts
2. 點擊「添加賬號」
3. 填寫：
   - 賬號 ID: `test_account_001`
   - Session 文件: `sessions/你的session文件名.session`
   - 劇本 ID: `test_script`
   - 群組 ID（可選）: `-1001234567890`
4. 點擊「保存」

**方式二：通過 API**

```bash
curl -X POST http://localhost:8000/api/v1/group-ai/accounts/ \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "test_account_001",
    "session_file": "sessions/你的session文件名.session",
    "script_id": "test_script",
    "group_ids": [-1001234567890]
  }'
```

**驗證**：
- 刷新賬號列表，應該看到新添加的賬號
- 賬號狀態應該為 `OFFLINE`

---

### 4.3 啟動賬號

**方式一：通過前端**

1. 在賬號列表中，找到 `test_account_001`
2. 點擊「啟動」按鈕
3. 等待幾秒鐘

**方式二：通過 API**

```bash
curl -X POST http://localhost:8000/api/v1/group-ai/accounts/test_account_001/start
```

**驗證**：
- 賬號狀態應該變為 `ONLINE` 或 `CONNECTING`
- 檢查後端日誌，應該看到連接信息
- 如果 session 文件有效，應該成功連接到 Telegram

---

### 4.4 測試賬號參數調整

1. 訪問：http://localhost:3000/group-ai/accounts/test_account_001/params
2. 調整參數：
   - 回復頻率：`0.5`（50%）
   - 紅包參與概率：`0.3`（30%）
3. 點擊「保存」

**驗證**：
- 參數應該成功保存
- 通過 API 查詢應該看到更新後的參數

```bash
curl http://localhost:8000/api/v1/group-ai/accounts/test_account_001
```

---

### 4.5 測試監控功能

1. 訪問：http://localhost:3000/group-ai/monitor
2. 觀察：
   - 系統指標應該顯示當前賬號數量
   - 如果有活動，應該看到消息和回復統計
   - 告警列表應該顯示相關告警（如果有）

**驗證 API**：

```bash
# 系統指標
curl http://localhost:8000/api/v1/group-ai/monitor/system

# 賬號指標
curl http://localhost:8000/api/v1/group-ai/monitor/accounts

# 告警列表
curl http://localhost:8000/api/v1/group-ai/monitor/alerts
```

---

## 🔍 第五步：高級測試

### 5.1 測試劇本執行

1. 確保賬號已啟動並在線
2. 在 Telegram 群組中發送觸發關鍵詞（如「你好」）
3. 觀察：
   - 賬號應該自動回復
   - 監控頁面應該顯示消息和回復統計增加

### 5.2 測試紅包檢測

1. 在 Telegram 群組中發送包含紅包關鍵詞的消息（如「發紅包」）
2. 觀察：
   - 日誌中應該看到紅包檢測信息
   - 如果參與概率設置，可能會嘗試參與

### 5.3 測試停止賬號

**方式一：通過前端**

1. 在賬號列表中，點擊「停止」按鈕

**方式二：通過 API**

```bash
curl -X POST http://localhost:8000/api/v1/group-ai/accounts/test_account_001/stop
```

**驗證**：
- 賬號狀態應該變為 `OFFLINE`
- 後端應該停止監聽該賬號的消息

---

## 🐛 常見問題排查

### 問題 1：後端無法啟動

**症狀**：`uvicorn` 報錯或端口被佔用

**解決方案**：
```bash
# 檢查端口是否被佔用
netstat -ano | findstr :8000

# 如果被佔用，殺死進程或更改端口
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 問題 2：前端無法連接後端

**症狀**：前端顯示網絡錯誤或 404

**解決方案**：
1. 確認後端正在運行
2. 檢查 `saas-demo/.env.local` 中的 `NEXT_PUBLIC_API_URL`
3. 檢查後端 CORS 設置

### 問題 3：Session 文件無效

**症狀**：賬號無法啟動，日誌顯示認證錯誤

**解決方案**：
1. 確認 session 文件路徑正確
2. 重新生成 session 文件（參考 `docs/GENERATE_SESSION_FILES.md`）
3. 確認 `API_ID` 和 `API_HASH` 正確

### 問題 4：數據庫錯誤

**症狀**：API 返回數據庫相關錯誤

**解決方案**：
```bash
cd admin-backend
# 重新運行遷移
alembic upgrade head
# 或重置數據庫
alembic downgrade base
alembic upgrade head
```

### 問題 5：劇本解析錯誤

**症狀**：創建劇本時 YAML 解析失敗

**解決方案**：
1. 檢查 YAML 格式是否正確
2. 使用在線 YAML 驗證工具
3. 參考 `ai_models/group_scripts/daily_chat.yaml` 的格式

---

## 📊 測試檢查清單

- [ ] 後端服務正常啟動
- [ ] 前端服務正常啟動
- [ ] 健康檢查 API 正常
- [ ] 賬號列表 API 正常
- [ ] 劇本列表 API 正常
- [ ] 監控 API 正常
- [ ] 前端賬號管理頁面正常
- [ ] 前端劇本管理頁面正常
- [ ] 前端監控頁面正常
- [ ] 可以創建劇本
- [ ] 可以添加賬號
- [ ] 可以啟動賬號
- [ ] 可以停止賬號
- [ ] 可以調整賬號參數
- [ ] 監控數據正常顯示
- [ ] 劇本執行正常（如果測試環境允許）

---

## 🎯 下一步

完成基礎測試後，可以：

1. **集成測試**：運行 `python scripts/integration_test.py`
2. **單元測試**：運行各個模塊的測試腳本
3. **性能測試**：測試多賬號並發處理
4. **實際部署**：參考 `docs/DEPLOYMENT_GUIDE.md`

---

**狀態**: ✅ 測試指南已準備就緒

