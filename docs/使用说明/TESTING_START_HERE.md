# 🚀 測試開始指南

> **快速開始測試系統**

---

## ✅ 當前狀態

- ✅ 後端服務已啟動：http://localhost:8000
- ✅ 前端服務已啟動：http://localhost:3000
- ✅ 數據庫已初始化
- ✅ Session 文件已準備（2 個）

---

## 📋 第一步：驗證服務運行

### 1.1 檢查後端

打開瀏覽器訪問：
- **健康檢查**: http://localhost:8000/health
- **API 文檔**: http://localhost:8000/docs

應該看到：
- `/health` 返回 `{"status": "ok"}`
- `/docs` 顯示 Swagger API 文檔界面

### 1.2 檢查前端

打開瀏覽器訪問：
- **前端界面**: http://localhost:3000

應該看到登錄頁面或主界面。

---

## 🧪 第二步：基礎 API 測試

### 2.1 測試賬號列表 API

在瀏覽器中訪問或使用 curl：

```bash
curl http://localhost:8000/api/v1/group-ai/accounts/
```

**預期結果**：返回空數組 `[]`

### 2.2 測試劇本列表 API

```bash
curl http://localhost:8000/api/v1/group-ai/scripts/
```

**預期結果**：返回空數組 `[]`

### 2.3 測試監控 API

```bash
curl http://localhost:8000/api/v1/group-ai/monitor/system
```

**預期結果**：返回系統指標 JSON

---

## 🎨 第三步：前端界面測試

### 3.1 測試賬號管理頁面

1. 訪問：http://localhost:3000/group-ai/accounts
2. 應該看到：
   - 賬號列表（初始為空）
   - 「添加賬號」按鈕
   - 頁面無錯誤

### 3.2 測試劇本管理頁面

1. 訪問：http://localhost:3000/group-ai/scripts
2. 應該看到：
   - 劇本列表（初始為空）
   - 「創建劇本」按鈕
   - 頁面無錯誤

### 3.3 測試監控頁面

1. 訪問：http://localhost:3000/group-ai/monitor
2. 應該看到：
   - 系統指標卡片
   - 賬號指標列表
   - 告警列表
   - 數據自動刷新（30秒間隔）

---

## 🔧 第四步：創建測試數據

### 4.1 創建測試劇本

**通過前端**：
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

**通過 API**：
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

### 4.2 添加測試賬號

**前提**：確保 `sessions/` 目錄下有有效的 `.session` 文件

**通過前端**：
1. 訪問：http://localhost:3000/group-ai/accounts
2. 點擊「添加賬號」
3. 填寫：
   - 賬號 ID: `test_account_001`
   - Session 文件: `sessions/你的session文件名.session`
   - 劇本 ID: `test_script`
   - 群組 ID（可選）: `-1001234567890`
4. 點擊「保存」

**通過 API**：
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

### 4.3 啟動賬號

**通過前端**：
1. 在賬號列表中，找到 `test_account_001`
2. 點擊「啟動」按鈕
3. 等待幾秒鐘，狀態應該變為 `ONLINE`

**通過 API**：
```bash
curl -X POST http://localhost:8000/api/v1/group-ai/accounts/test_account_001/start
```

---

## 📊 第五步：運行自動化測試

### 5.1 運行系統啟動測試

```bash
py scripts/test_system_startup.py
```

### 5.2 運行快速檢查腳本

```powershell
.\scripts\quick_test.ps1
```

---

## 🐛 常見問題

### 問題 1：後端無法啟動

**解決方案**：
1. 檢查端口 8000 是否被佔用
2. 確認 Python 依賴已安裝
3. 查看後端日誌錯誤信息

### 問題 2：前端無法連接後端

**解決方案**：
1. 確認後端正在運行
2. 檢查 `saas-demo/.env.local` 中的 `NEXT_PUBLIC_API_URL`
3. 確認後端 CORS 設置正確

### 問題 3：Session 文件無效

**解決方案**：
1. 確認 session 文件路徑正確
2. 重新生成 session 文件（參考 `docs/GENERATE_SESSION_FILES.md`）
3. 確認 `API_ID` 和 `API_HASH` 正確

---

## 📚 詳細文檔

- **逐步測試指南**: `docs/STEP_BY_STEP_TESTING.md`
- **快速開始**: `docs/QUICK_START.md`
- **API 文檔**: http://localhost:8000/docs

---

## 🎯 下一步

完成基礎測試後，可以：

1. **集成測試**：運行 `py scripts/integration_test.py`
2. **單元測試**：運行各個模塊的測試腳本
3. **實際使用**：在真實 Telegram 群組中測試

---

**狀態**: ✅ 系統已準備就緒，可以開始測試！

