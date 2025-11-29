@echo off
chcp 65001 >nul
echo ========================================
echo 部署节点统计修复
echo ========================================
echo.

echo [1] 上传文件到服务器...
scp saas-demo/src/app/group-ai/nodes/page.tsx ubuntu@165.154.233.55:/tmp/nodes_page.tsx
scp saas-demo/src/lib/i18n/translations.ts ubuntu@165.154.233.55:/tmp/translations.ts

echo.
echo [2] 在服务器上替换文件并重新构建...
ssh ubuntu@165.154.233.55 "cd /home/ubuntu/liaotian/saas-demo && sudo systemctl stop liaotian-frontend && cp /tmp/nodes_page.tsx src/app/group-ai/nodes/page.tsx && cp /tmp/translations.ts src/lib/i18n/translations.ts && export NVM_DIR=\"\$HOME/.nvm\" && [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && nvm use 20 && npm run build && sudo systemctl start liaotian-frontend && sleep 5 && sudo systemctl status liaotian-frontend --no-pager | head -15"

echo.
echo ========================================
echo 部署完成！
echo ========================================
pause

