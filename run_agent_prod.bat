@echo off
REM ============================================================
REM Agent 生产环境启动脚本 (Windows)
REM 连接到生产服务器: https://api.usdt2026.cc
REM ============================================================

echo ============================================================
echo 正在启动 Agent (连接至生产环境: https://api.usdt2026.cc)
echo ============================================================
echo.

REM 设置配置文件路径
set AGENT_CONFIG=agent\config_prod.json

REM 检查配置文件是否存在
if not exist "%AGENT_CONFIG%" (
    echo 错误: 配置文件不存在: %AGENT_CONFIG%
    echo 请确保 agent/config_prod.json 文件存在
    pause
    exit /b 1
)

echo 使用配置文件: %AGENT_CONFIG%
echo.

REM 启动 Agent
python agent\main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Agent 启动失败，错误代码: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

pause
