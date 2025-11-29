@echo off
chcp 65001 >nul
echo ========================================
echo 部署账号管理功能增强
echo ========================================
echo.

echo [步骤 1] 上传修改的前端文件...
scp saas-demo/src/lib/api/group-ai.ts ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/lib/api/group-ai.ts
if %errorlevel% neq 0 (
    echo [错误] 上传 group-ai.ts 失败
    pause
    exit /b 1
)
echo [OK] group-ai.ts 上传成功
echo.

scp saas-demo/src/app/group-ai/accounts/page.tsx ubuntu@165.154.233.55:/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx
if %errorlevel% neq 0 (
    echo [错误] 上传 accounts/page.tsx 失败
    pause
    exit /b 1
)
echo [OK] accounts/page.tsx 上传成功
echo.

echo [步骤 2] 重新构建前端...
echo 正在构建前端，请稍候...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use 20 && rm -rf .next && npm run build 2>&1 | tail -50"
if %errorlevel% neq 0 (
    echo [警告] 前端构建可能有问题，请检查输出
) else (
    echo [OK] 前端构建成功
)
echo.

echo [步骤 3] 重启前端服务...
ssh ubuntu@165.154.233.55 "sudo systemctl restart liaotian-frontend"
timeout /t 3 /nobreak >nul
echo [OK] 前端服务已重启
echo.

echo [步骤 4] 检查服务状态...
ssh ubuntu@165.154.233.55 "sudo systemctl status liaotian-frontend --no-pager | head -15"
echo.

echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 功能更新：
echo - 从所有Worker节点读取账号
echo - 合并显示数据库账号和Worker节点账号
echo - 角色分配功能集成到账号管理
echo - 选择剧本时自动加载角色列表
echo.
echo 下一步：
echo 1. 清除浏览器缓存（Ctrl+Shift+Delete）
echo 2. 强制刷新页面（Ctrl+F5）
echo 3. 检查账号列表是否正确显示所有账号
echo 4. 测试角色分配功能
echo.
pause

