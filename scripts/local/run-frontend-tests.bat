@echo off
chcp 65001 >nul
echo ============================================================
echo 运行前端 E2E 测试 (Frontend E2E Tests)
echo ============================================================
echo.

cd /d "%~dp0\..\..\saas-demo"

echo [1/3] 检查依赖...
if not exist "node_modules" (
    echo ⚠️  node_modules 不存在，正在安装依赖...
    call npm install
)

echo [2/3] 检查 Playwright...
if not exist "node_modules\@playwright\test" (
    echo ⚠️  Playwright 未安装，正在安装...
    call npx playwright install chromium
)

echo [3/3] 运行 E2E 测试...
call npm run test:e2e

echo.
echo ============================================================
echo 测试完成
echo ============================================================
pause

