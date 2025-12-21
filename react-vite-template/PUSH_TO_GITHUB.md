# 推送到各自的 GitHub 倉庫指南

## 🎯 目標

將自動化部署配置應用到三個項目（aizkw, tgmini, hongbao）並推送到各自的 GitHub 倉庫，觸發 GitHub Actions 自動部署。

## 📋 前置條件

1. ✅ 三個項目已創建各自的 GitHub 倉庫
2. ✅ 本地已克隆或可以訪問這些項目
3. ✅ 已配置 GitHub Secrets（SERVER_HOST, SERVER_USER, SERVER_SSH_KEY）

## 🚀 快速操作步驟

### 方法一：手動複製並推送（推薦）

#### 對於 aizkw 項目

```bash
# 1. 進入項目目錄
cd /path/to/aizkw  # 或 cd /home/ubuntu/aizkw20251219

# 2. 確保在 main 分支
git checkout main
git pull origin main

# 3. 複製模板文件
cp /path/to/telegram-ai-system/react-vite-template/src/config.ts ./src/
cp /path/to/telegram-ai-system/react-vite-template/ecosystem.config.js ./
cp /path/to/telegram-ai-system/react-vite-template/.github/workflows/deploy.yml ./.github/workflows/
cp /path/to/telegram-ai-system/react-vite-template/DEPLOY_TEST.md ./

# 4. 修改配置（編輯文件）
# - 編輯 src/config.ts，填入實際聯繫方式
# - 編輯 .github/workflows/deploy.yml，修改 PROJECT_NAME 和 PROJECT_DIR

# 5. 提交並推送
git add .
git commit -m "配置自動化部署和統一配置管理"
git push origin main

# 6. 查看 GitHub Actions
# 進入 GitHub 倉庫 → Actions → 查看 "Deploy to Server" workflow
```

#### 對於 tgmini 項目

```bash
cd /path/to/tgmini
git checkout main
git pull origin main

# 複製文件
cp /path/to/telegram-ai-system/react-vite-template/src/config.ts ./src/
cp /path/to/telegram-ai-system/react-vite-template/ecosystem.config.js ./
cp /path/to/telegram-ai-system/react-vite-template/.github/workflows/deploy.yml ./.github/workflows/
cp /path/to/telegram-ai-system/react-vite-template/DEPLOY_TEST.md ./

# 修改配置
# - src/config.ts: projectName = "TGMINI"
# - .github/workflows/deploy.yml: PROJECT_NAME="tgmini", PROJECT_DIR="/home/ubuntu/tgmini20251219"

git add .
git commit -m "配置自動化部署和統一配置管理"
git push origin main
```

#### 對於 hongbao 項目

```bash
cd /path/to/hongbao
git checkout main
git pull origin main

# 複製文件
cp /path/to/telegram-ai-system/react-vite-template/src/config.ts ./src/
cp /path/to/telegram-ai-system/react-vite-template/ecosystem.config.js ./
cp /path/to/telegram-ai-system/react-vite-template/.github/workflows/deploy.yml ./.github/workflows/
cp /path/to/telegram-ai-system/react-vite-template/DEPLOY_TEST.md ./

# 修改配置
# - src/config.ts: projectName = "HONGBAO"
# - .github/workflows/deploy.yml: PROJECT_NAME="hongbao", PROJECT_DIR="/home/ubuntu/hongbao20251219"

git add .
git commit -m "配置自動化部署和統一配置管理"
git push origin main
```

### 方法二：使用腳本批量應用（服務器端）

如果三個項目都在服務器上，可以使用提供的腳本：

```bash
# 在模板目錄中
cd /path/to/telegram-ai-system/react-vite-template
chmod +x apply-to-projects.sh
./apply-to-projects.sh

# 然後手動進入每個項目目錄推送
cd /home/ubuntu/aizkw20251219
git add .
git commit -m "配置自動化部署"
git push origin main

cd /home/ubuntu/tgmini20251219
git add .
git commit -m "配置自動化部署"
git push origin main

cd /home/ubuntu/hongbao20251219
git add .
git commit -m "配置自動化部署"
git push origin main
```

## ⚙️ 必須修改的配置

### 1. src/config.ts

每個項目需要修改：

```typescript
export const siteConfig: SiteConfig = {
  projectName: "AIZKW",  // 改為 "AIZKW", "TGMINI", 或 "HONGBAO"
  contact: {
    telegram: {
      username: "@your_telegram",  // 填入實際 Telegram
      url: "https://t.me/your_telegram",
    },
    whatsapp: {
      number: "+1234567890",  // 填入實際 WhatsApp
      url: "https://wa.me/1234567890",
    },
    email: {
      address: "support@example.com",  // 填入實際郵箱
    },
  },
  branding: {
    logoPath: "/logo.png",  // 修改為實際 Logo 路徑
  },
};
```

### 2. .github/workflows/deploy.yml

每個項目需要修改：

```yaml
# aizkw 項目
PROJECT_NAME="aizkw"
PROJECT_DIR="/home/ubuntu/aizkw20251219"

# tgmini 項目
PROJECT_NAME="tgmini"
PROJECT_DIR="/home/ubuntu/tgmini20251219"  # 根據實際目錄修改

# hongbao 項目
PROJECT_NAME="hongbao"
PROJECT_DIR="/home/ubuntu/hongbao20251219"  # 根據實際目錄修改
```

### 3. ecosystem.config.js（如果使用 PM2）

```javascript
module.exports = {
  apps: [
    {
      name: "aizkw",  // 改為對應項目名稱
      // ...
    },
  ],
};
```

## ✅ 驗證部署

推送後，檢查以下內容：

### 1. GitHub Actions 狀態

1. 進入項目 GitHub 倉庫
2. 點擊 **Actions** 標籤
3. 查看 "Deploy to Server" workflow
4. 確認所有步驟顯示 ✅

### 2. 部署結果

- ✅ `DEPLOY_TEST.md` 文件已更新
- ✅ 網站可以正常訪問
- ✅ 功能正常運行

### 3. 服務器驗證

```bash
# 檢查項目目錄
ls -la /home/ubuntu/aizkw20251219/dist

# 檢查 Nginx（如果需要）
sudo systemctl status nginx

# 檢查 PM2（如果使用）
pm2 status
```

## 🔄 後續更新流程

以後如果需要更新：

1. **修改聯繫方式**：
   ```bash
   # 編輯 src/config.ts
   git add src/config.ts
   git commit -m "更新聯繫方式"
   git push origin main
   ```

2. **修改代碼**：
   ```bash
   # 正常開發流程
   git add .
   git commit -m "功能更新"
   git push origin main
   ```

推送後，GitHub Actions 會自動觸發部署！

## 🆘 故障排查

### 問題 1: GitHub Actions 失敗

**檢查**：
- GitHub Secrets 是否正確配置
- 服務器 SSH 連接是否正常
- 項目目錄路徑是否正確

**解決**：
```bash
# 測試 SSH 連接
ssh -i ~/.ssh/your_key ubuntu@SERVER_HOST

# 檢查項目目錄
ls -la /home/ubuntu/aizkw20251219
```

### 問題 2: 構建失敗

**檢查**：
- `npm install` 是否成功
- `npm run build` 是否成功
- 查看 GitHub Actions 日誌

### 問題 3: 部署後網站無法訪問

**檢查**：
- Nginx 配置是否正確
- 文件權限是否正確
- 端口是否被監聽

## 📝 檢查清單

在推送前，確認：

- [ ] `src/config.ts` 已填入實際聯繫方式
- [ ] `.github/workflows/deploy.yml` 中的項目路徑正確
- [ ] `ecosystem.config.js` 中的項目名稱正確（如果使用 PM2）
- [ ] GitHub Secrets 已配置
- [ ] 代碼中硬編碼的聯繫方式已替換（可選，後續完成）
- [ ] 已測試本地構建：`npm run build`

完成後，推送即可觸發自動部署！
