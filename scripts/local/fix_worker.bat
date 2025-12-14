@echo off
chcp 65001 >nul
echo ========================================
echo Worker 节点快速修复脚本
echo ========================================
echo.

set WORKER_DIR=%~dp0..\worker-deploy-pc-002
set PROJECT_DIR=%~dp0..\..

echo [1/5] 检查目录...
if not exist "%WORKER_DIR%" (
    echo ❌ Worker 目录不存在: %WORKER_DIR%
    echo 请确认 Worker 节点目录路径
    pause
    exit /b 1
)

if not exist "%PROJECT_DIR%\scripts\local\fix-worker-session-reader.py" (
    echo ❌ 修复脚本不存在
    echo 请确认项目目录: %PROJECT_DIR%
    pause
    exit /b 1
)

echo ✅ 目录检查通过
echo.

echo [2/5] 修复 Session 文件...
cd /d "%WORKER_DIR%"
if not exist "sessions" (
    echo ❌ sessions 目录不存在
    pause
    exit /b 1
)

python "%PROJECT_DIR%\scripts\local\fix-worker-session-reader.py" sessions
if errorlevel 1 (
    echo ❌ Session 文件修复失败
    pause
    exit /b 1
)

echo ✅ Session 文件修复完成
echo.

echo [3/5] 停止当前 Worker 进程...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Worker*" 2>nul
timeout /t 2 /nobreak >nul
echo ✅ Worker 进程已停止
echo.

echo [4/5] 验证 Session 文件...
python -c "import sqlite3; from pathlib import Path; [print(f'  ✅ {f.name}') if sqlite3.connect(str(f)).execute('SELECT 1').fetchone() else print(f'  ❌ {f.name}') for f in Path('sessions').glob('*.session')]"
if errorlevel 1 (
    echo ⚠️  Session 文件验证失败（可能不是致命错误）
)
echo.

echo [5/5] 重新启动 Worker...
if exist "start_worker.bat" (
    echo 启动 Worker 节点...
    start "" "start_worker.bat"
    echo ✅ Worker 节点已启动
) else (
    echo ⚠️  未找到 start_worker.bat，请手动启动 Worker 节点
)

echo.
echo ========================================
echo ✅ 修复完成！
echo ========================================
echo.
echo 下一步：
echo 1. 检查 Worker 节点日志，确认账号已正确加载
echo 2. 检查前端页面，确认"在线节点"和"活跃账号"显示正常
echo 3. 尝试"一键启动所有账号"功能
echo.
pause

