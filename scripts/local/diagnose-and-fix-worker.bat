@echo off
chcp 65001 >nul
echo ========================================
echo Worker 节点诊断和修复工具
echo ========================================
echo.

:: 检测 Worker 节点目录
set WORKER_DIR=
if exist "%~dp0..\worker-deploy-pc-001" (
    set WORKER_DIR=%~dp0..\worker-deploy-pc-001
    echo 检测到 Worker 节点: pc-001
)
if exist "%~dp0..\worker-deploy-pc-002" (
    if defined WORKER_DIR (
        echo 检测到多个 Worker 节点，请选择：
        echo   1. pc-001
        echo   2. pc-002
        echo   3. 全部
        set /p choice="请输入选择 (1/2/3): "
        if "%choice%"=="1" (
            set WORKER_DIR=%~dp0..\worker-deploy-pc-001
        ) else if "%choice%"=="2" (
            set WORKER_DIR=%~dp0..\worker-deploy-pc-002
        ) else if "%choice%"=="3" (
            goto fix_all
        )
    ) else (
        set WORKER_DIR=%~dp0..\worker-deploy-pc-002
        echo 检测到 Worker 节点: pc-002
    )
)

if not defined WORKER_DIR (
    echo ❌ 未找到 Worker 节点目录
    echo 请确保 Worker 部署目录存在（worker-deploy-pc-001 或 worker-deploy-pc-002）
    pause
    exit /b 1
)

:fix_one
echo.
echo ========================================
echo 修复节点: %WORKER_DIR%
echo ========================================
cd /d "%WORKER_DIR%"

if not exist "sessions" (
    echo ❌ sessions 目录不存在
    goto next
)

echo.
echo [1/4] 检查 Session 文件...
set SESSION_COUNT=0
for %%f in (sessions\*.session) do (
    set /a SESSION_COUNT+=1
    echo   找到: %%~nxf
)
if %SESSION_COUNT%==0 (
    echo ⚠️  未找到 Session 文件
    goto next
)
echo ✅ 找到 %SESSION_COUNT% 个 Session 文件

echo.
echo [2/4] 修复 Session 文件...
if exist "fix_session.py" (
    python fix_session.py sessions
    if %errorlevel% neq 0 (
        echo ❌ 修复失败，尝试手动修复...
        python -c "import sqlite3; from pathlib import Path; [print(f'修复 {f.name}...') or sqlite3.connect(str(f)).execute('CREATE TABLE IF NOT EXISTS version (version INTEGER)') or sqlite3.connect(str(f)).execute('INSERT OR IGNORE INTO version (version) VALUES (1)') or sqlite3.connect(str(f)).execute('PRAGMA table_info(sessions)') or print('  ✅ 已修复') for f in Path('sessions').glob('*.session')]"
    )
) else (
    echo ⚠️  fix_session.py 不存在，使用内置修复...
    python -c "import sqlite3; from pathlib import Path; [print(f'修复 {f.name}...') or sqlite3.connect(str(f)).execute('CREATE TABLE IF NOT EXISTS version (version INTEGER)') or sqlite3.connect(str(f)).execute('INSERT OR IGNORE INTO version (version) VALUES (1)') or print('  ✅ 已修复') for f in Path('sessions').glob('*.session')]"
)

echo.
echo [3/4] 检查 Excel 配置...
if exist "sessions\*.xlsx" (
    echo ✅ Excel 配置文件已存在
    for %%f in (sessions\*.xlsx) do (
        echo    文件: %%~nxf
    )
) else (
    echo ⚠️  Excel 配置文件不存在
    if exist "create_excel_template.py" (
        echo 正在创建 Excel 模板...
        python create_excel_template.py
    ) else (
        echo ❌ create_excel_template.py 不存在
    )
)

echo.
echo [4/4] 验证修复结果...
python -c "import sqlite3; from pathlib import Path; errors=[]; [errors.append(f.name) if not sqlite3.connect(str(f)).execute('SELECT 1 FROM version').fetchone() else None for f in Path('sessions').glob('*.session')]; print('✅ 所有 Session 文件已修复') if not errors else print(f'❌ 仍有错误: {errors}')"

echo.
echo ✅ 修复完成！
echo.
echo 下一步：
echo 1. 检查 Excel 配置文件，确保填写了 api_id、api_hash、phone、enabled
echo 2. 重启 Worker 节点
echo.

:next
if "%choice%"=="3" (
    if "%WORKER_DIR%"=="%~dp0..\worker-deploy-pc-001" (
        set WORKER_DIR=%~dp0..\worker-deploy-pc-002
        goto fix_one
    )
)

pause
exit /b 0

:fix_all
echo.
echo [修复所有节点]
echo.
set WORKER_DIR=%~dp0..\worker-deploy-pc-001
if exist "%WORKER_DIR%" (
    call :fix_one
)
set WORKER_DIR=%~dp0..\worker-deploy-pc-002
if exist "%WORKER_DIR%" (
    call :fix_one
)
goto :eof

