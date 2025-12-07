# 📁 腳本文件組織說明

## 📋 目錄結構

```
scripts/
├── local/              # 本地開發環境腳本（Windows）
│   ├── *.bat          # Windows 批處理腳本
│   └── *.ps1          # PowerShell 腳本
│
├── server/             # 服務器環境腳本（Linux，必須英文命名）
│   ├── *.sh           # Linux Shell 腳本
│   └── *.py           # Python 服務器腳本
│
└── common/             # 通用腳本（跨平台）
    └── *.py           # Python 通用腳本
```

## 🖥️ 運行環境說明

### 本地運行（Windows）

**一鍵執行：**
```bash
# 啟動所有服務
scripts\local\start-all-services.bat

# 自動測試和修復
scripts\local\auto-test-and-fix.bat

# 驗證前端
scripts\local\verify-frontend.bat
```

**分步執行：**
```bash
# 1. 啟動後端
cd admin-backend
set DATABASE_URL=sqlite:///./admin.db
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. 啟動前端（另一個終端）
cd saas-demo
npm run dev

# 3. 驗證服務
curl http://localhost:8000/health
```

### 服務器運行（Linux）

**一鍵執行：**
```bash
# 啟動所有服務
bash scripts/server/start-all-services.sh

# 自動測試和修復
bash scripts/server/auto-test-and-fix.sh

# 驗證服務
bash scripts/server/verify-services.sh
```

**分步執行：**
```bash
# 1. 啟動後端
cd admin-backend
export DATABASE_URL="sqlite:///./admin.db"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# 或生產環境：
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 2. 啟動前端（另一個終端）
cd saas-demo
npm run build
npm start

# 3. 驗證服務
curl http://localhost:8000/health
```

## 📝 文件命名規則

### 本地腳本（Windows）
- 可以使用中文命名
- 格式：`功能描述.bat` 或 `功能描述.ps1`
- 示例：`啟動服務.bat`, `執行測試.ps1`

### 服務器腳本（Linux）
- **必須使用英文命名**
- 格式：`功能描述.sh` 或 `功能描述.py`
- 使用小寫字母和連字符
- 示例：`start-service.sh`, `run-tests.sh`, `deploy-backend.sh`

## 🔍 功能分類

### admin-backend/scripts/

```
admin-backend/scripts/
├── setup/              # 設置和配置
│   ├── init-database.py
│   └── setup-security.py
│
├── test/               # 測試相關
│   ├── auto_test_and_fix.py
│   └── run-all-tests.bat
│
├── deploy/             # 部署相關
│   └── deploy.sh
│
└── maintenance/        # 維護和修復
    ├── fix-database.bat
    └── backup-database.py
```

## ✅ 使用檢查清單

創建或使用腳本時：

- [ ] 確認運行環境（本地/服務器）
- [ ] 使用正確的執行命令
- [ ] 服務器腳本使用英文命名
- [ ] 腳本放在正確的分類目錄
- [ ] 文檔標註運行環境
- [ ] 提供一鍵和分步兩種執行方式

---

**最後更新：** 2025-01-17

