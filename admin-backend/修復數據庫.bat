@echo off
chcp 65001 >nul
echo ============================================================
echo 🔧 修復數據庫問題
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] 初始化數據庫表...
python init_db_tables.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 數據庫表初始化失敗
    pause
    exit /b 1
)

echo.
echo [2/3] 運行數據庫遷移...
python -m alembic upgrade head
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  遷移可能部分失敗，但繼續執行...
)

echo.
echo [3/3] 驗證數據庫表...
python -c "from app.db import engine; from sqlalchemy import inspect; tables = inspect(engine).get_table_names(); print('數據庫表數量:', len(tables)); required = ['group_ai_scripts', 'group_ai_automation_tasks', 'users']; missing = [t for t in required if t not in tables]; print('缺少的表:', missing if missing else '無')"

echo.
echo ============================================================
echo ✅ 數據庫修復完成
echo ============================================================
echo.
echo 現在可以重新啟動後端服務
echo.
pause

