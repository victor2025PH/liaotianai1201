@echo off
chcp 65001 >nul
echo ========================================
echo 启动前端服务 (Next.js)
echo ========================================
echo.

cd /d "%~dp0..\saas-demo"

echo 当前目录: %CD%
echo.
echo 正在启动 Next.js 开发服务器...
echo 请等待服务启动完成...
echo.

npm run dev

pause

