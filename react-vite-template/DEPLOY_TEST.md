# 自動化部署測試

**狀態**: 成功 ✅

**測試時間**: 請查看 GitHub Actions 運行時間

**說明**: 此文件用於驗證 GitHub Actions 自動化部署是否正常工作。如果此文件存在且內容已更新，說明部署流程已成功觸發。

## 如何觸發更新

1. **自動觸發**: 當你向 `main` 分支推送代碼時，GitHub Actions 會自動運行
2. **手動觸發**: 在 GitHub 倉庫的 Actions 頁面，選擇 "Deploy to Server" workflow，點擊 "Run workflow"

## 部署流程

1. ✅ 代碼拉取 (git pull)
2. ✅ 依賴安裝 (npm install)
3. ✅ 項目構建 (npm run build)
4. ✅ Nginx 重載 (sudo systemctl reload nginx)
5. ✅ PM2 重啟（如果使用）

## 驗證部署

部署完成後，請訪問你的網站確認：
- 網站是否正常加載
- 功能是否正常
- 是否有錯誤日誌

## 注意事項

- 確保服務器上的項目目錄路徑正確
- 確保 GitHub Secrets 已正確配置（SERVER_HOST, SERVER_USER, SERVER_SSH_KEY）
- 如果部署失敗，請查看 GitHub Actions 日誌
