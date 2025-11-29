@echo off
chcp 65001 >nul
echo ========================================
echo 查看构建错误详情
echo ========================================
echo.

echo [步骤 1] 查看构建错误（完整输出）...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\$HOME/.nvm && [ -s \$NVM_DIR/nvm.sh ] && . \$NVM_DIR/nvm.sh && nvm use 20 && npm run build 2>&1"
echo.

echo [步骤 2] 检查是否有语法错误...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\$HOME/.nvm && [ -s \$NVM_DIR/nvm.sh ] && . \$NVM_DIR/nvm.sh && nvm use 20 && npm run build 2>&1 | grep -i error | head -20"
echo.

echo [步骤 3] 检查TypeScript编译错误...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && export NVM_DIR=\$HOME/.nvm && [ -s \$NVM_DIR/nvm.sh ] && . \$NVM_DIR/nvm.sh && nvm use 20 && npm run build 2>&1 | grep -i 'error\|failed\|fail' | head -30"
echo.

pause

