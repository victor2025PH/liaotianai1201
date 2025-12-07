# 📁 後端腳本文件說明

## 📋 目錄結構

```
admin-backend/scripts/
├── setup/              # 設置和配置腳本
│   ├── init-database.py
│   ├── setup-security.py
│   └── start-service.bat
│
├── test/               # 測試腳本
│   ├── auto_test_and_fix.py
│   ├── check_security_config.py
│   └── run-all-tests.bat
│
├── deploy/             # 部署腳本（必須英文命名）
│   └── deploy.sh
│
└── maintenance/         # 維護和修復腳本
    ├── fix-database.bat
    └── backup-database.py
```

## 🖥️ 運行環境說明

### 本地運行（Windows）

**一鍵執行：**
```bash
# 啟動服務
admin-backend\scripts\setup\start-service.bat

# 運行測試
admin-backend\scripts\test\run-all-tests.bat

# 修復數據庫
admin-backend\scripts\maintenance\fix-database.bat
```

**分步執行：**
```bash
# 1. 初始化數據庫
cd admin-backend
python scripts/setup/init-database.py

# 2. 啟動服務
set DATABASE_URL=sqlite:///./admin.db
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. 運行測試
python scripts/test/auto_test_and_fix.py
```

### 服務器運行（Linux）

**一鍵執行：**
```bash
# 啟動服務
bash admin-backend/scripts/deploy/start-service.sh

# 運行測試
bash admin-backend/scripts/deploy/run-tests.sh
```

**分步執行：**
```bash
# 1. 初始化數據庫
cd admin-backend
export DATABASE_URL="sqlite:///./admin.db"
python scripts/setup/init-database.py

# 2. 啟動服務
export DATABASE_URL="sqlite:///./admin.db"
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 3. 運行測試
python scripts/test/auto_test_and_fix.py
```

---

**最後更新：** 2025-01-17

