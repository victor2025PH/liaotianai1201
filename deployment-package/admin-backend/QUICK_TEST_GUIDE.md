# 快速測試指南

## 🚀 一鍵執行所有測試

```bash
cd admin-backend
python run_all_tests.py
```

## 📋 分階段測試方法

### 1. 環境準備（必須先執行）

```bash
# 初始化數據庫
python init_db_tables.py

# 運行遷移
python -m alembic upgrade head
```

### 2. 自動化任務功能測試（核心功能）

```bash
python test_automation_tasks.py
```

**預期結果：** ✅ 所有測試通過 (3/3)

### 3. 單元測試

```bash
# 服務層測試
python -m pytest tests/test_notification_service.py -v

# 數據模型測試
python -m pytest tests/test_db_crud.py -v
```

### 4. 集成測試

```bash
# API 測試
python -m pytest tests/test_api.py -v

# Group AI 測試
python -m pytest tests/test_group_ai.py -v
```

### 5. 性能測試

```bash
python -m pytest tests/test_performance.py -v
```

## 📊 測試報告位置

- **測試總結：** `test_reports/test_summary.md`
- **詳細日誌：** `test_reports/*.log`
- **自動化任務測試：** `test_automation_output.log`

## ✅ 快速驗證清單

運行以下命令快速驗證系統狀態：

```bash
# 1. 檢查數據庫表
python -c "from app.db import engine; from sqlalchemy import inspect; print('表數量:', len(inspect(engine).get_table_names()))"

# 2. 檢查後端服務
curl http://localhost:8000/health

# 3. 運行自動化任務測試
python test_automation_tasks.py
```

## 📖 詳細文檔

- **完整測試方法：** `TEST_METHODOLOGY.md`
- **測試指南：** `TEST_GUIDE.md`
- **自動化任務測試報告：** `TEST_REPORT_AUTOMATION_TASKS.md`

