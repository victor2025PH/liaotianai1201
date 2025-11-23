# 完整測試方法文檔

## 測試概述

本文檔詳細說明 Smart TG Business AI 系統的完整測試流程和方法。

## 測試分類

### 1. 單元測試 (Unit Tests)
- **目的**：測試單個函數或類的功能
- **範圍**：服務層、工具函數、數據模型
- **執行時間**：快速（秒級）

### 2. 集成測試 (Integration Tests)
- **目的**：測試多個組件協同工作
- **範圍**：API端點、數據庫操作、服務間通信
- **執行時間**：中等（分鐘級）

### 3. 端到端測試 (E2E Tests)
- **目的**：測試完整用戶流程
- **範圍**：前端到後端的完整流程
- **執行時間**：較長（分鐘到小時級）

### 4. 性能測試 (Performance Tests)
- **目的**：測試系統性能和負載能力
- **範圍**：API響應時間、並發處理、緩存效果
- **執行時間**：中等（分鐘級）

## 測試環境準備

### 前置條件

1. **數據庫準備**
   ```bash
   cd admin-backend
   python init_db_tables.py  # 創建所有表
   python -m alembic upgrade head  # 運行遷移
   ```

2. **後端服務啟動**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **前端服務啟動**（可選，用於E2E測試）
   ```bash
   cd saas-demo
   npm run dev
   ```

## 詳細測試方法

### 階段 1: 單元測試

#### 1.1 服務層測試

**測試文件：** `tests/test_*.py`

**執行命令：**
```bash
cd admin-backend
pytest tests/ -v -m unit --cov=app.services --cov-report=term-missing
```

**測試內容：**
- ✅ 任務執行器 (`test_automation_tasks.py`)
- ✅ 通知服務 (`test_notification_service.py`)
- ✅ 數據源服務 (`test_services_data_sources.py`)
- ✅ 告警檢查器 (`test_services_scheduled_alert_checker.py`)

**預期結果：** 所有單元測試通過

#### 1.2 數據模型測試

**測試文件：** `tests/test_db_crud.py`

**執行命令：**
```bash
pytest tests/test_db_crud.py -v
```

**測試內容：**
- ✅ 賬號 CRUD 操作
- ✅ 劇本 CRUD 操作
- ✅ 自動化任務 CRUD 操作
- ✅ 通知配置 CRUD 操作
- ✅ 角色分配方案 CRUD 操作

### 階段 2: API 集成測試

#### 2.1 認證與授權測試

**測試文件：** `tests/test_api.py`

**執行命令：**
```bash
pytest tests/test_api.py::test_auth -v
```

**測試內容：**
- ✅ 用戶登錄
- ✅ JWT Token 驗證
- ✅ 權限檢查
- ✅ 未授權訪問攔截

#### 2.2 Group AI API 測試

**測試文件：** `tests/test_group_ai.py`, `tests/test_integration_api.py`

**執行命令：**
```bash
pytest tests/test_group_ai.py tests/test_integration_api.py -v -m integration
```

**測試內容：**
- ✅ 賬號管理 API
  - 創建賬號
  - 列表查詢（分頁、搜索、過濾）
  - 更新賬號
  - 刪除賬號
  - 批量操作
- ✅ 劇本管理 API
  - 創建劇本
  - 版本管理
  - 審核流程
  - 發布/停用
- ✅ 自動化任務 API
  - 創建任務（含依賴和通知配置）
  - 執行任務
  - 查看日誌
  - 更新任務
  - 刪除任務
- ✅ 監控 API
  - 賬號指標
  - 系統指標
  - 告警規則
- ✅ 角色分配 API
  - 創建分配方案
  - 應用分配方案
  - 查看歷史

#### 2.3 通知系統 API 測試

**測試文件：** `tests/test_notification_service.py`

**執行命令：**
```bash
pytest tests/test_notification_service.py -v
```

**測試內容：**
- ✅ 通知配置 CRUD
- ✅ 通知模板 CRUD
- ✅ 發送通知（郵件、瀏覽器、Webhook）
- ✅ 通知列表查詢
- ✅ 批量操作（標記已讀、刪除）

### 階段 3: 自動化任務功能測試

#### 3.1 任務執行器測試

**測試文件：** `test_automation_tasks.py`

**執行命令：**
```bash
python test_automation_tasks.py
```

**測試內容：**
- ✅ 任務創建與配置
- ✅ 任務執行（各種動作類型）
- ✅ 任務統計更新
- ✅ 任務依賴觸發
- ✅ 通知發送
- ✅ 任務日誌記錄

**詳細步驟：**

1. **創建測試任務**
   ```python
   task = GroupAIAutomationTask(
       name="測試任務",
       task_type="manual",
       task_action="alert_check",
       dependent_tasks=[],
       notify_on_success=False,
       notify_on_failure=True,
       notify_recipients=["test@example.com"]
   )
   ```

2. **執行任務**
   - 驗證任務執行成功
   - 檢查統計數據更新
   - 驗證日誌記錄

3. **測試依賴任務**
   - 創建依賴任務
   - 配置任務依賴
   - 執行主任務
   - 驗證依賴任務自動觸發

4. **測試通知**
   - 驗證通知發送
   - 檢查通知記錄

#### 3.2 新任務動作測試

**測試動作類型：**
- `account_batch_start` - 批量啟動賬號
- `account_batch_stop` - 批量停止賬號
- `script_review` - 劇本審核
- `data_export` - 數據導出
- `role_assignment` - 角色分配

**測試方法：**
```python
# 測試批量啟動
result = await executor._execute_account_batch_start(
    {"account_ids": ["account1", "account2"]},
    db
)
assert result["accounts_started"] >= 0
```

### 階段 4: 性能測試

#### 4.1 API 響應時間測試

**測試文件：** `tests/test_performance.py`

**執行命令：**
```bash
pytest tests/test_performance.py -v
```

**測試內容：**
- ✅ API 響應時間（目標 < 500ms）
- ✅ 並發請求處理
- ✅ 緩存效果驗證
- ✅ 數據庫查詢優化

#### 4.2 緩存測試

**測試方法：**
```python
# 測試緩存命中率
cache_stats = get_cache_manager().get_stats()
assert cache_stats["hit_rate"] > 0
```

### 階段 5: 前端功能測試

#### 5.1 手動測試清單

**測試頁面：**

1. **賬號管理頁面** (`/group-ai/accounts`)
   - ✅ 賬號列表顯示
   - ✅ 搜索和過濾功能
   - ✅ 批量創建賬號
   - ✅ 賬號編輯（頭像、資料）
   - ✅ 批量操作（啟動、停止、刪除）

2. **劇本管理頁面** (`/group-ai/scripts`)
   - ✅ 劇本列表
   - ✅ 創建/編輯劇本
   - ✅ 版本管理
   - ✅ 審核流程
   - ✅ 發布/停用

3. **自動化任務頁面** (`/group-ai/automation-tasks`)
   - ✅ 任務列表
   - ✅ 創建任務（含依賴和通知配置）
   - ✅ 編輯任務
   - ✅ 執行任務
   - ✅ 查看日誌
   - ✅ 依賴任務選擇器
   - ✅ 通知配置UI

4. **通知中心** (`/notifications`)
   - ✅ 通知列表
   - ✅ 批量操作（標記已讀、刪除）
   - ✅ 通知配置管理
   - ✅ 通知模板管理

5. **監控頁面** (`/monitor`)
   - ✅ 賬號監控
   - ✅ 系統監控
   - ✅ 告警設置

#### 5.2 自動化 E2E 測試（可選）

**使用 Playwright：**
```bash
cd saas-demo
npx playwright test
```

### 階段 6: 數據庫完整性測試

#### 6.1 數據一致性測試

**測試內容：**
- ✅ 外鍵約束
- ✅ 數據完整性
- ✅ 事務回滾
- ✅ 並發寫入

**測試方法：**
```python
# 測試事務回滾
try:
    db.begin()
    # 執行操作
    raise Exception("測試回滾")
except:
    db.rollback()
    # 驗證數據未改變
```

### 階段 7: 安全性測試

#### 7.1 權限測試

**測試內容：**
- ✅ 未授權訪問攔截
- ✅ 權限檢查中間件
- ✅ 角色權限分配
- ✅ 用戶角色管理

**測試方法：**
```python
# 測試無權限訪問
response = client.get("/api/v1/group-ai/accounts", headers={})
assert response.status_code == 401 or 403
```

## 完整測試執行流程

### 快速測試（開發階段）

```bash
# 1. 單元測試
pytest tests/ -v -m unit

# 2. 集成測試
pytest tests/ -v -m integration

# 3. 自動化任務測試
python test_automation_tasks.py
```

### 完整測試（發布前）

```bash
# 1. 所有測試 + 覆蓋率報告
pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# 2. 性能測試
pytest tests/test_performance.py -v

# 3. API 測試
pytest tests/test_api.py tests/test_integration_api.py -v

# 4. 自動化任務完整測試
python test_automation_tasks.py

# 5. 生成測試報告
pytest tests/ --html=test_report.html --self-contained-html
```

## 測試數據準備

### 測試數據腳本

創建 `admin-backend/scripts/prepare_test_data.py`：

```python
"""
準備測試數據
"""
from app.db import SessionLocal
from app.models.group_ai import GroupAIAccount, GroupAIScript, GroupAIAutomationTask
from app.models.user import User
from app.core.security import get_password_hash

def prepare_test_data():
    db = SessionLocal()
    try:
        # 創建測試用戶
        # 創建測試賬號
        # 創建測試劇本
        # 創建測試任務
        pass
    finally:
        db.close()
```

## 測試報告

### 生成測試報告

```bash
# HTML 報告
pytest tests/ --html=reports/test_report.html --self-contained-html

# 覆蓋率報告
pytest tests/ --cov=app --cov-report=html --cov-report=term
# 查看: htmlcov/index.html

# XML 報告（用於 CI/CD）
pytest tests/ --junitxml=reports/junit.xml
```

## 持續集成測試

### GitHub Actions 配置（示例）

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/ -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 測試最佳實踐

### 1. 測試隔離
- 每個測試應該獨立運行
- 使用測試數據庫或事務回滾
- 清理測試數據

### 2. 測試命名
- 使用描述性的測試名稱
- 遵循 `test_<功能>_<場景>_<預期結果>` 格式

### 3. 測試覆蓋率
- 目標覆蓋率：> 80%
- 關鍵業務邏輯：100%

### 4. 測試數據
- 使用固定測試數據
- 避免依賴外部服務
- 使用 Mock 對象

### 5. 錯誤處理
- 測試正常流程
- 測試錯誤流程
- 測試邊界條件

## 常見問題排查

### 問題 1: 數據庫表不存在
**解決方案：**
```bash
python init_db_tables.py
python -m alembic upgrade head
```

### 問題 2: 測試數據衝突
**解決方案：**
- 使用 UUID 生成唯一ID
- 測試後清理數據
- 使用測試專用數據庫

### 問題 3: 異步測試失敗
**解決方案：**
- 確保使用 `pytest-asyncio`
- 使用 `@pytest.mark.asyncio` 裝飾器
- 檢查事件循環配置

## 測試檢查清單

### 發布前檢查

- [ ] 所有單元測試通過
- [ ] 所有集成測試通過
- [ ] API 測試通過
- [ ] 自動化任務測試通過
- [ ] 性能測試通過
- [ ] 前端功能測試通過
- [ ] 安全性測試通過
- [ ] 測試覆蓋率 > 80%
- [ ] 無嚴重錯誤日誌
- [ ] 文檔更新完成

## 聯繫與支持

如有測試相關問題，請查看：
- 測試日誌：`admin-backend/test_automation_output.log`
- 測試報告：`admin-backend/TEST_REPORT_AUTOMATION_TASKS.md`
- 代碼覆蓋率：`admin-backend/htmlcov/index.html`

