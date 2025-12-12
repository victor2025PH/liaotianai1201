@echo off
chcp 65001 >nul
REM ============================================================
REM 启动 AI 聊天测试（Windows 版本）
REM ============================================================

echo ============================================================
echo AI 聊天测试启动脚本
echo ============================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装或未添加到 PATH
    echo 请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 切换到项目目录
cd /d "%~dp0\..\.." || (
    echo ❌ 无法切换到项目目录
    pause
    exit /b 1
)

REM 运行 Python 脚本
echo 正在启动 AI 聊天测试...
echo.
echo 用法:
echo   start-ai-chat-test.bat [账号数量] [群组ID]
echo.
echo 示例:
echo   start-ai-chat-test.bat 6        - 启动6个在线账号的聊天
echo   start-ai-chat-test.bat 6 12345  - 启动6个账号在群组12345中聊天
echo.

python scripts\local\start-ai-chat-test.py %*

if errorlevel 1 (
    echo.
    echo ❌ 启动失败
    pause
    exit /b 1
) else (
    echo.
    echo ✅ 启动完成
    pause
)

