@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 啟動後端服務
echo ============================================================
echo.

cd /d "%~dp0"

echo 設置數據庫配置...
if not exist .env (
    echo DATABASE_URL=sqlite:///./admin.db > .env
    echo ✅ 已創建 .env 文件
) else (
    echo ✅ .env 文件已存在
)

echo 檢查數據庫配置...
python -c "from app.core.config import get_settings; import os; os.environ.pop('DATABASE_URL', None); from importlib import reload; import app.core.config; reload(app.core.config); s = app.core.config.get_settings(); print(f'數據庫: {s.database_url}')"

echo.
echo 啟動服務...
echo 後端地址: http://localhost:8000
echo API 文檔: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服務
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

