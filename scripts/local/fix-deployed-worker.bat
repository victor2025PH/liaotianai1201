@echo off
chcp 65001 >nul
echo ========================================
echo 修复已部署的 Worker 节点
echo ========================================
echo.

set WORKER_DIR=%~dp0..\worker-deploy-pc-001
if exist "%~dp0..\worker-deploy-pc-002" (
    echo 检测到多个 Worker 节点目录
    echo.
    echo 请选择要修复的节点：
    echo   1. pc-001
    echo   2. pc-002
    echo   3. 全部
    echo.
    set /p choice="请输入选择 (1/2/3): "
    
    if "%choice%"=="1" (
        set WORKER_DIR=%~dp0..\worker-deploy-pc-001
    ) else if "%choice%"=="2" (
        set WORKER_DIR=%~dp0..\worker-deploy-pc-002
    ) else if "%choice%"=="3" (
        goto fix_all
    ) else (
        echo 无效选择，使用默认: pc-001
    )
)

:fix_one
echo.
echo [修复节点] %WORKER_DIR%
cd /d "%WORKER_DIR%"

if not exist "sessions" (
    echo ❌ sessions 目录不存在
    pause
    exit /b 1
)

echo [1/3] 修复 Session 文件...
if exist "fix_session.py" (
    python fix_session.py sessions
) else (
    echo ⚠️  fix_session.py 不存在，跳过
)

echo.
echo [2/3] 检查 Excel 配置...
if exist "sessions\*.xlsx" (
    echo ✅ Excel 配置文件已存在
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
echo [3/3] 验证修复结果...
python -c "import sqlite3; from pathlib import Path; [print(f'  ✅ {f.name}') if sqlite3.connect(str(f)).execute('SELECT 1').fetchone() else print(f'  ❌ {f.name}') for f in Path('sessions').glob('*.session')]"

echo.
echo ✅ 修复完成！
echo.
echo 下一步：
echo 1. 如果 Excel 文件不存在，请手动创建并填写账号信息
echo 2. 重启 Worker 节点
echo.
pause
exit /b 0

:fix_all
echo.
echo [修复所有节点]
echo.

if exist "%~dp0..\worker-deploy-pc-001" (
    set WORKER_DIR=%~dp0..\worker-deploy-pc-001
    call :fix_one
)

if exist "%~dp0..\worker-deploy-pc-002" (
    set WORKER_DIR=%~dp0..\worker-deploy-pc-002
    call :fix_one
)

echo.
echo ✅ 所有节点修复完成！
pause

