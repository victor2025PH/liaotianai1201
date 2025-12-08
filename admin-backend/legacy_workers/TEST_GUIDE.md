# 完整測試指南

## 📋 測試方法總覽

本文檔提供 Smart TG Business AI 系統的完整測試方法和步驟。

## 🚀 快速開始

### 方法 1: 使用自動化測試腳本（推薦）

```bash
cd admin-backend
python run_all_tests.py
```

這個腳本會自動執行所有測試階段並生成報告。

### 方法 2: 手動執行各階段測試

按照以下順序逐步執行：

## 📝 詳細測試步驟

### 階段 1: 環境準備

#### 1.1 初始化數據庫

```bash
cd admin-backend
python init_db_tables.py
```

**預期結果：**
- ✅ 所有數據庫表創建成功
- ✅ 無錯誤輸出

**驗證方法：**
```bash
python -c "from app.db import engine; from sqlalchemy import inspect; print('表數量:', len(inspect(engine).get_table_names()))"
```

#### 1.2 運行數據庫遷移

```bash
python -m alembic upgrade head
```

**預期結果：**
- ✅ 所有遷移成功執行
- ✅ 數據庫結構最新

**驗證方法：**
```bash
python -c "from app.db import engine; from sqlalchemy import inspect; tables = inspect(engine).get_table_names(); print('關鍵表存在:', 'group_ai_automation_tasks' in tables, 'notifications' in tables)"
```

### 階段 2: 單元測試

#### 2.1 服務層測試

**測試文件：**
- `tests/test_notification_service.py` - 通知服務
- `tests/test_services_data_sources.py` - 數據源服務
- `tests/test_services_scheduled_alert_checker.py` - 告警檢查器

**執行命令：**
```bash
python -m pytest tests/test_notification_service.py tests/test_services_*.py -v
```

**測試內容：**
- ✅ 通知發送功能
- ✅ 通知模板應用
- ✅ 數據源獲取
- ✅ 告警檢查邏輯

**預期結果：** 所有測試通過

#### 2.2 數據模型 CRUD 測試

**測試文件：** `tests/test_db_crud.py`

**執行命令：**
```bash
python -m pytest tests/test_db_crud.py -v
```

**測試內容：**
- ✅ 賬號 CRUD
- ✅ 劇本 CRUD
- ✅ 自動化任務 CRUD
- ✅ 通知配置 CRUD

### 階段 3: 集成測試

#### 3.1 API 端點測試

**測試文件：**
- `tests/test_api.py` - 基礎 API
- `tests/test_integration_api.py` - 集成 API

**執行命令：**
```bash
python -m pytest tests/test_api.py tests/test_integration_api.py -v -m integration
```

**測試內容：**
- ✅ 認證與授權
- ✅ 賬號管理 API
- ✅ 劇本管理 API
- ✅ 自動化任務 API
- ✅ 監控 API

**測試方法：**

1. **啟動後端服務**（如果未運行）
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **執行測試**
   ```bash
   python -m pytest tests/test_api.py -v
   ```

#### 3.2 Group AI 功能測試

**測試文件：**
- `tests/test_group_ai.py` - Group AI 核心功能
- `tests/test_alert_rules.py` - 告警規則

**執行命令：**
```bash
python -m pytest tests/test_group_ai.py tests/test_alert_rules.py -v
```

### 階段 4: 自動化任務功能測試

**測試文件：** `test_automation_tasks.py`

**執行命令：**
```bash
python test_automation_tasks.py
```

**詳細測試步驟：**

#### 測試 1: 任務執行器

1. **創建測試任務**
   - 驗證任務創建成功
   - 檢查任務配置（依賴、通知）

2. **執行任務**
   - 驗證任務執行成功
   - 檢查執行結果

3. **驗證統計更新**
   - `run_count` 增加
   - `success_count` 增加
   - `last_result` 更新

4. **檢查通知**
   - 驗證通知記錄創建
   - 檢查通知內容

5. **測試依賴任務**
   - 創建依賴任務
   - 配置任務依賴
   - 執行主任務
   - 驗證依賴任務自動觸發

#### 測試 2: 新任務動作

**批量操作測試：**
```python
# 測試批量啟動
result = await executor._execute_account_batch_start(
    {"account_ids": ["account1", "account2"]},
    db
)
assert "accounts_started" in result
```

**數據導出測試：**
```python
result = await executor._execute_data_export(
    {"export_type": "csv", "data_type": "accounts"},
    db
)
assert result["export_completed"] == True
```

#### 測試 3: 通知集成

**發送通知測試：**
```python
notification_id = await notification_service.send_browser_notification(
    recipient="test@example.com",
    title="測試通知",
    message="測試消息",
    level="info"
)
assert notification_id > 0
```

### 階段 5: 性能測試

**測試文件：** `tests/test_performance.py`

**執行命令：**
```bash
python -m pytest tests/test_performance.py -v
```

**測試內容：**
- ✅ API 響應時間（目標 < 500ms）
- ✅ 緩存命中率
- ✅ 數據庫查詢性能
- ✅ 並發處理能力

**性能基準：**
- API 響應時間：< 500ms
- 緩存命中率：> 50%
- 數據庫查詢：< 100ms

### 階段 6: 前端功能測試

#### 6.1 手動測試清單

**賬號管理頁面** (`/group-ai/accounts`)

1. **基本功能**
   - [ ] 打開頁面，驗證列表加載
   - [ ] 測試搜索功能（賬號ID、名稱）
   - [ ] 測試過濾功能（狀態、劇本、服務器）
   - [ ] 測試排序功能

2. **賬號操作**
   - [ ] 創建單個賬號
   - [ ] 批量創建賬號（選擇 session 文件）
   - [ ] 編輯賬號（頭像、資料信息）
   - [ ] 批量操作（啟動、停止、刪除）
   - [ ] 刪除賬號

3. **數據驗證**
   - [ ] 驗證賬號資料信息顯示（頭像、名稱、內容）
   - [ ] 驗證狀態更新實時性

**劇本管理頁面** (`/group-ai/scripts`)

1. **基本功能**
   - [ ] 劇本列表顯示
   - [ ] 搜索和過濾
   - [ ] 版本管理

2. **劇本操作**
   - [ ] 創建劇本
   - [ ] 編輯劇本
   - [ ] 提交審核
   - [ ] 審核通過/拒絕
   - [ ] 發布劇本
   - [ ] 停用劇本

3. **數據持久化**
   - [ ] 驗證劇本創建後不丟失
   - [ ] 驗證版本歷史保存

**自動化任務頁面** (`/group-ai/automation-tasks`)

1. **基本功能**
   - [ ] 任務列表顯示
   - [ ] 任務詳情查看

2. **任務創建**
   - [ ] 創建定時任務
   - [ ] 配置調度（Cron、間隔、模板）
   - [ ] 選擇任務動作
   - [ ] 配置動作參數
   - [ ] **選擇依賴任務**（新功能）
   - [ ] **配置通知**（新功能）
     - 成功時通知開關
     - 失敗時通知開關
     - 添加通知接收人

3. **任務操作**
   - [ ] 編輯任務
   - [ ] 啟用/停用任務
   - [ ] 手動執行任務
   - [ ] 查看執行日誌
   - [ ] 刪除任務

4. **驗證新功能**
   - [ ] 驗證依賴任務選擇器工作正常
   - [ ] 驗證通知配置保存
   - [ ] 驗證任務執行後通知發送

**通知中心** (`/notifications`)

1. **通知列表**
   - [ ] 通知列表顯示
   - [ ] 未讀數量顯示
   - [ ] 過濾功能（已讀/未讀）

2. **批量操作**
   - [ ] 選擇多個通知
   - [ ] 批量標記已讀
   - [ ] 批量刪除

3. **通知配置** (`/notifications/configs`)
   - [ ] 通知配置列表
   - [ ] 創建通知配置
   - [ ] 編輯通知配置
   - [ ] **通知模板管理**（新功能）
     - 創建模板
     - 編輯模板
     - 預覽模板
     - 刪除模板

#### 6.2 API 測試（使用 curl 或 Postman）

**測試自動化任務 API：**

```bash
# 1. 登錄獲取 Token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" \
  | jq -r '.access_token')

# 2. 創建任務（含依賴和通知）
curl -X POST "http://localhost:8000/api/v1/group-ai/automation-tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試任務",
    "task_type": "scheduled",
    "task_action": "alert_check",
    "schedule_config": {"cron": "0 9 * * *"},
    "action_config": {},
    "dependent_tasks": ["task-id-1"],
    "notify_on_success": true,
    "notify_on_failure": true,
    "notify_recipients": ["admin@example.com"]
  }'

# 3. 執行任務
curl -X POST "http://localhost:8000/api/v1/group-ai/automation-tasks/{task_id}/run" \
  -H "Authorization: Bearer $TOKEN"

# 4. 查看任務日誌
curl "http://localhost:8000/api/v1/group-ai/automation-tasks/{task_id}/logs" \
  -H "Authorization: Bearer $TOKEN"
```

### 階段 7: 端到端測試（E2E）

#### 7.1 完整流程測試

**場景 1: 創建並執行自動化任務**

1. 登錄系統
2. 導航到自動化任務頁面
3. 點擊"創建任務"
4. 填寫任務信息：
   - 名稱：每日告警檢查
   - 類型：定時任務
   - 動作：告警檢查
   - 調度：每天 9:00
5. **配置依賴任務**（選擇一個已存在的任務）
6. **配置通知**：
   - 啟用"失敗時通知"
   - 添加接收人：admin@example.com
7. 保存任務
8. 手動執行任務
9. 驗證：
   - 任務執行成功
   - 統計數據更新
   - 依賴任務被觸發
   - 通知已發送（如果失敗）

**場景 2: 批量賬號操作**

1. 導航到賬號管理頁面
2. 選擇多個賬號
3. 執行批量操作（啟動/停止）
4. 驗證所有選中賬號狀態更新

## 📊 測試報告生成

### 生成覆蓋率報告

```bash
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

**查看報告：**
- HTML 報告：`htmlcov/index.html`
- 終端報告：直接顯示在終端

### 生成 HTML 測試報告

```bash
python -m pytest tests/ --html=test_reports/test_report.html --self-contained-html
```

**查看報告：** `test_reports/test_report.html`

### 生成 XML 報告（用於 CI/CD）

```bash
python -m pytest tests/ --junitxml=test_reports/junit.xml
```

## 🔍 測試檢查清單

### 發布前必須通過的測試

- [ ] **單元測試** - 所有服務層測試通過
- [ ] **集成測試** - 所有 API 測試通過
- [ ] **自動化任務測試** - 完整功能測試通過
- [ ] **性能測試** - 響應時間符合要求
- [ ] **前端功能測試** - 所有頁面功能正常
- [ ] **數據庫測試** - CRUD 操作正常
- [ ] **安全性測試** - 權限檢查正常
- [ ] **通知系統測試** - 通知發送正常

### 新功能驗證清單

#### 自動化任務擴展功能

- [ ] 依賴任務選擇器顯示正確
- [ ] 可以選擇多個依賴任務
- [ ] 依賴任務正確保存
- [ ] 任務執行後依賴任務自動觸發
- [ ] 通知配置開關工作正常
- [ ] 可以添加多個通知接收人
- [ ] 任務執行成功後發送通知（如果啟用）
- [ ] 任務執行失敗後發送通知（如果啟用）
- [ ] 新任務動作（批量操作、數據導出等）正常工作

## 🐛 問題排查

### 常見問題

#### 問題 1: 數據庫表不存在

**錯誤信息：** `no such table: xxx`

**解決方法：**
```bash
python init_db_tables.py
python -m alembic upgrade head
```

#### 問題 2: 測試數據衝突

**錯誤信息：** `UNIQUE constraint failed`

**解決方法：**
- 使用 UUID 生成唯一 ID
- 測試前清理舊數據
- 使用測試專用數據庫

#### 問題 3: 權限錯誤

**錯誤信息：** `403 Forbidden` 或 `401 Unauthorized`

**解決方法：**
- 檢查用戶是否登錄
- 驗證用戶權限配置
- 檢查權限檢查中間件

#### 問題 4: 服務未啟動

**錯誤信息：** `Connection refused`

**解決方法：**
```bash
# 啟動後端服務
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📈 測試指標

### 目標指標

- **測試覆蓋率：** > 80%
- **API 響應時間：** < 500ms
- **測試通過率：** 100%
- **緩存命中率：** > 50%

### 當前狀態

運行 `python run_all_tests.py` 查看當前測試狀態。

## 📚 相關文檔

- **測試方法文檔：** `TEST_METHODOLOGY.md`
- **測試報告：** `TEST_REPORT_AUTOMATION_TASKS.md`
- **測試總結：** `test_reports/test_summary.md`

## 🎯 下一步

完成所有測試後：
1. 檢查測試報告
2. 修復發現的問題
3. 重新運行失敗的測試
4. 確認所有測試通過
5. 準備部署

