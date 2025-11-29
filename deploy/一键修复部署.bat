@echo off
chcp 65001 >nul
echo ========================================
echo 一键修复部署 - 重新构建并重启
echo ========================================
echo.

echo [1/4] 上传修复后的文件（如果需要）...
echo 文件应该已经上传，跳过...
echo.

echo [2/4] 重新构建前端...
echo 这可能需要几分钟，请耐心等待...
ssh ubuntu@165.154.233.55 "bash -c 'cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"\$HOME/.nvm\" && [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && nvm use 20 && rm -rf .next && npm run build'"
echo.

echo [3/4] 重启前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
timeout /t 5 /nobreak >nul
echo.

echo [4/4] 验证服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -15"
echo.

echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 请检查上面的服务状态。
echo 如果显示 "active (running)"，说明修复成功。
echo.
echo 下一步：
echo 1. 清除浏览器缓存（Ctrl+Shift+Delete）
echo 2. 强制刷新页面（Ctrl+F5）
echo 3. 访问 http://aikz.usdt2026.cc
echo.
pause

