@echo off
chcp 65001 >nul
echo ========================================
echo 完整修复前端服务
echo ========================================
echo.

echo [步骤 1] 停止前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl stop liaotian-frontend"
timeout /t 2 /nobreak >nul
echo [OK] 服务已停止
echo.

echo [步骤 2] 检查并清理旧的构建...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && rm -rf .next && echo '已清理旧构建'"
echo.

echo [步骤 3] 重新构建前端（这可能需要几分钟）...
echo 正在构建，请耐心等待...
ssh ubuntu@165.154.233.55 "bash -c 'cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"\$HOME/.nvm\" && [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && nvm use 20 && npm run build'"
if %errorlevel% neq 0 (
    echo [错误] 构建失败，请检查上面的错误信息
    pause
    exit /b 1
)
echo [OK] 构建完成
echo.

echo [步骤 4] 验证构建结果...
ssh ubuntu@165.154.233.55 "test -f /home/ubuntu/liaotian/saas-demo/.next/BUILD_ID && echo '构建成功 - BUILD_ID存在' || echo '构建失败 - BUILD_ID不存在'"
echo.

echo [步骤 5] 检查服务配置...
ssh ubuntu@165.154.233.55 "cat /etc/systemd/system/liaotian-frontend.service | grep -E 'ExecStart|WorkingDirectory'"
echo.

echo [步骤 6] 重新加载systemd配置...
ssh ubuntu@165.154.233.55 "sudo systemctl daemon-reload"
echo [OK] 配置已重新加载
echo.

echo [步骤 7] 启动前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl start liaotian-frontend"
timeout /t 5 /nobreak >nul
echo [OK] 服务已启动
echo.

echo [步骤 8] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -20"
echo.

echo [步骤 9] 检查端口监听...
ssh ubuntu@165.154.233.55 "sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000' || echo '端口3000未监听'"
echo.

echo [步骤 10] 查看最新日志（如果有错误）...
ssh ubuntu@165.154.233.55 "sudo journalctl -u liaotian-frontend -n 20 --no-pager | tail -15"
echo.

echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 如果服务状态显示 "active (running)"，说明修复成功。
echo 如果仍然失败，请查看上面的日志信息。
echo.
echo 下一步：
echo 1. 清除浏览器缓存（Ctrl+Shift+Delete）
echo 2. 强制刷新页面（Ctrl+F5）
echo 3. 访问 http://aikz.usdt2026.cc
echo.
pause

