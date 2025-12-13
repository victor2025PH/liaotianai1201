@echo off
chcp 65001 >nul
REM ============================================================
REM Worker 节点连接诊断脚本 (Windows)
REM ============================================================

echo ============================================================
echo 🔍 Worker 节点连接诊断
echo ============================================================
echo.

set SERVER_URL=https://aikz.usdt2026.cc
set HEARTBEAT_ENDPOINT=%SERVER_URL%/api/v1/workers/heartbeat

echo 服务器配置:
echo   - 服务器 URL: %SERVER_URL%
echo   - 心跳端点: %HEARTBEAT_ENDPOINT%
echo.

REM 1. 检查网络连接
echo [1/5] 检查网络连接...
echo   - 测试 DNS 解析...
nslookup aikz.usdt2026.cc >nul 2>&1
if %errorlevel% equ 0 (
    echo     ✅ DNS 解析成功
    nslookup aikz.usdt2026.cc | findstr "Address"
) else (
    echo     ❌ DNS 解析失败
    echo     请检查网络连接或 DNS 配置
)

echo   - 测试 HTTP 连接...
curl -s -o nul -w "%%{http_code}" --connect-timeout 10 %SERVER_URL% >temp_http_code.txt 2>nul
set /p HTTP_CODE=<temp_http_code.txt
del temp_http_code.txt 2>nul
if "%HTTP_CODE%"=="200" (
    echo     ✅ HTTP 连接成功 (状态码: %HTTP_CODE%^)
) else if "%HTTP_CODE%"=="301" (
    echo     ✅ HTTP 连接成功 (状态码: %HTTP_CODE%^)
) else if "%HTTP_CODE%"=="302" (
    echo     ✅ HTTP 连接成功 (状态码: %HTTP_CODE%^)
) else (
    echo     ❌ HTTP 连接失败 (状态码: %HTTP_CODE%^)
    echo     请检查网络连接或服务器是否运行
)
echo.

REM 2. 测试后端 API 端点
echo [2/5] 测试后端 API 端点...
echo   - 测试健康检查端点...
curl -s -o nul -w "%%{http_code}" --connect-timeout 10 %SERVER_URL%/health >temp_health_code.txt 2>nul
set /p HEALTH_CODE=<temp_health_code.txt
del temp_health_code.txt 2>nul
if "%HEALTH_CODE%"=="200" (
    echo     ✅ 健康检查端点可访问 (状态码: %HEALTH_CODE%^)
) else (
    echo     ❌ 健康检查端点不可访问 (状态码: %HEALTH_CODE%^)
)

echo   - 测试心跳端点...
curl -s -o nul -w "%%{http_code}" --connect-timeout 10 -X POST "%HEARTBEAT_ENDPOINT%" ^
    -H "Content-Type: application/json" ^
    -d "{\"node_id\":\"test\",\"status\":\"online\",\"account_count\":0,\"accounts\":[]}" >temp_heartbeat_code.txt 2>nul
set /p HEARTBEAT_CODE=<temp_heartbeat_code.txt
del temp_heartbeat_code.txt 2>nul
if "%HEARTBEAT_CODE%"=="200" (
    echo     ✅ 心跳端点可访问 (状态码: %HEARTBEAT_CODE%^)
) else if "%HEARTBEAT_CODE%"=="401" (
    echo     ✅ 心跳端点可访问，需要认证 (状态码: %HEARTBEAT_CODE%^)
) else if "%HEARTBEAT_CODE%"=="403" (
    echo     ✅ 心跳端点可访问，需要认证 (状态码: %HEARTBEAT_CODE%^)
) else (
    echo     ❌ 心跳端点不可访问 (状态码: %HEARTBEAT_CODE%^)
    echo     请检查后端服务是否运行
)
echo.

REM 3. 检查 Worker 节点配置
echo [3/5] 检查 Worker 节点配置...
if exist worker_config.py (
    echo     ✅ 找到 worker_config.py
    findstr /C:"SERVER_URL" /C:"server_url" worker_config.py >nul 2>&1
    if %errorlevel% equ 0 (
        echo     配置的服务器 URL:
        findstr /C:"SERVER_URL" /C:"server_url" worker_config.py | findstr /V "REM" | findstr /V "#"
    )
) else if exist config.py (
    echo     ✅ 找到 config.py
    findstr /C:"SERVER_URL" /C:"server_url" config.py >nul 2>&1
    if %errorlevel% equ 0 (
        echo     配置的服务器 URL:
        findstr /C:"SERVER_URL" /C:"server_url" config.py | findstr /V "REM" | findstr /V "#"
    )
) else (
    echo     ⚠️  未找到 Worker 配置文件
    echo     请确认 Worker 节点配置文件位置
)
echo.

REM 4. 检查 Worker 节点进程
echo [4/5] 检查 Worker 节点进程...
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr /C:"worker" >nul 2>&1
if %errorlevel% equ 0 (
    echo     ✅ 找到 Worker 进程:
    tasklist /FI "IMAGENAME eq python.exe" /FO LIST | findstr /C:"worker"
) else (
    echo     ❌ 未找到 Worker 进程
    echo     请确认 Worker 节点是否正在运行
)
echo.

REM 5. 检查防火墙
echo [5/5] 检查防火墙设置...
netsh advfirewall show allprofiles state | findstr "State" >nul 2>&1
if %errorlevel% equ 0 (
    echo     Windows 防火墙状态:
    netsh advfirewall show allprofiles state | findstr "State"
    echo     ⚠️  请确保允许出站 HTTPS 连接（端口 443^）
) else (
    echo     ⚠️  无法检查防火墙状态
)
echo.

echo ============================================================
echo 诊断完成
echo ============================================================
echo.
echo 建议:
echo   1. 如果网络连接失败，检查网络配置和 DNS 设置
echo   2. 如果 API 端点不可访问，检查后端服务状态
echo   3. 如果 Worker 进程未运行，启动 Worker 节点
echo   4. 如果防火墙阻止，允许出站 HTTPS 连接（端口 443^）
echo.

pause

