@echo off
chcp 65001 >nul
echo ========================================
echo 修复构建并启动服务
echo ========================================
echo.

echo [步骤 1] 停止服务...
ssh ubuntu@165.154.233.55 "sudo systemctl stop liaotian-frontend"
timeout /t 2 /nobreak >nul
echo [OK] 服务已停止
echo.

echo [步骤 2] 清理旧构建...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && rm -rf .next node_modules/.cache"
echo [OK] 已清理
echo.

echo [步骤 3] 重新构建（使用简化的命令）...
echo 正在构建，请耐心等待...
echo.
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && source \$HOME/.nvm/nvm.sh && nvm use 20 && npm run build"
if %errorlevel% neq 0 (
    echo.
    echo [错误] 构建失败！
    echo 请查看上面的错误信息，或运行: .\deploy\查看构建错误.bat
    pause
    exit /b 1
)
echo.
echo [OK] 构建完成
echo.

echo [步骤 4] 验证构建结果...
ssh ubuntu@165.154.233.55 "test -f /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID && echo '构建成功' || echo '构建失败'"
echo.

echo [步骤 5] 重新加载并启动服务...
ssh ubuntu@165.154.233.55 "sudo systemctl daemon-reload && sudo systemctl start liaotian-frontend"
timeout /t 5 /nobreak >nul
echo.

echo [步骤 6] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -20"
echo.

echo [步骤 7] 查看服务日志（如果有错误）...
ssh ubuntu@165.154.233.55 "sudo journalctl -u liaotian-frontend -n 20 --no-pager | tail -15"
echo.

echo ========================================
echo 完成！
echo ========================================
echo.
echo 如果服务状态显示 "active (running)"，说明修复成功。
echo 如果仍然失败，请查看上面的日志信息。
echo.
pause

