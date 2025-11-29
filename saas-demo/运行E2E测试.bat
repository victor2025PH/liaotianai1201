@echo off
chcp 65001 >nul
echo ========================================
echo E2E 测试运行脚本
echo ========================================
echo.

cd /d "%~dp0"

echo 当前目录: %CD%
echo.

if not exist "package.json" (
    echo 错误：未找到 package.json
    echo 请确保在 saas-demo 目录下运行此脚本
    pause
    exit /b 1
)

echo ✓ 找到 package.json
echo.

if not exist "node_modules" (
    echo ⚠ node_modules 不存在
    echo 正在安装依赖...
    echo.
    call npm install
    if errorlevel 1 (
        echo ✗ 依赖安装失败
        pause
        exit /b 1
    )
    echo.
) else (
    echo ✓ node_modules 已存在
    echo.
)

echo 检查 Playwright 浏览器...
call npx playwright --version >nul 2>&1
if errorlevel 1 (
    echo ⚠ 需要安装 Playwright 浏览器
    echo 正在安装...
    call npx playwright install chromium
    echo.
)

echo 开始运行 E2E 测试...
echo 注意：这可能需要几分钟时间
echo.

call npm run test:e2e

if errorlevel 1 (
    echo.
    echo ========================================
    echo ✗ 部分测试失败
    echo ========================================
    echo.
    echo 查看 HTML 报告: npx playwright show-report
) else (
    echo.
    echo ========================================
    echo ✓ 所有测试通过！
    echo ========================================
)

echo.
pause
