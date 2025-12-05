#!/bin/bash
# 一鍵部署命令 - 直接複製執行

cd ~/liaotian && \
git pull origin main && \
echo "✅ [1/4] 代碼拉取完成" && \
cd admin-backend && \
sudo systemctl restart liaotian-backend && \
echo "✅ [2/4] 後端服務重啟完成" && \
cd ../saas-demo && \
npm run build && \
echo "✅ [3/4] 前端構建完成" && \
sudo systemctl restart liaotian-frontend && \
echo "✅ [4/4] 前端服務重啟完成" && \
echo "" && \
echo "==========================================" && \
echo "  ✅ 部署完成！" && \
echo "==========================================" && \
echo "" && \
echo "服務狀態:" && \
sudo systemctl is-active liaotian-backend && \
sudo systemctl is-active liaotian-frontend
