@echo off
chcp 65001 >nul
echo ============================================================
echo 🔄 切換到 SQLite 數據庫（開發環境）
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] 設置環境變量...
if exist .env (
    echo 備份現有 .env 文件...
    copy .env .env.backup >nul
    echo ✅ 已備份為 .env.backup
)

echo DATABASE_URL=sqlite:///./admin.db > .env.temp
if exist .env (
    findstr /V "DATABASE_URL" .env > .env.temp2
    type .env.temp2 .env.temp > .env.new
    move /Y .env.new .env >nul
    del .env.temp .env.temp2 >nul
) else (
    move /Y .env.temp .env >nul
)

echo ✅ 已設置 DATABASE_URL=sqlite:///./admin.db

echo.
echo [2/3] 初始化 SQLite 數據庫...
python init_db_tables.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 數據庫初始化失敗
    pause
    exit /b 1
)

echo.
echo [3/3] 驗證數據庫...
python -c "from app.db import engine; from sqlalchemy import inspect; tables = inspect(engine).get_table_names(); print('✅ 數據庫表數量:', len(tables)); required = ['users', 'group_ai_scripts', 'group_ai_automation_tasks']; missing = [t for t in required if t not in tables]; if missing: print('❌ 缺少的表:', missing); else: print('✅ 所有必需的表都已創建')"

echo.
echo ============================================================
echo ✅ 切換完成
echo ============================================================
echo.
echo 現在可以啟動服務：
echo   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo.
echo 或使用：
echo   python start_local.py
echo.
pause

