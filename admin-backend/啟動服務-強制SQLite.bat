@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 啟動後端服務（強制使用 SQLite）
echo ============================================================
echo.

cd /d "%~dp0"

echo 強制設置 SQLite 數據庫...
set DATABASE_URL=sqlite:///./admin.db

echo 檢查數據庫配置...
python -c "import os; os.environ['DATABASE_URL']='sqlite:///./admin.db'; from app.core.config import get_settings; import importlib; import app.core.config; importlib.reload(app.core.config); s = app.core.config.get_settings(); print(f'數據庫: {s.database_url}')"

echo.
echo 啟動服務...
echo 後端地址: http://localhost:8000
echo API 文檔: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服務
echo.

set DATABASE_URL=sqlite:///./admin.db
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

