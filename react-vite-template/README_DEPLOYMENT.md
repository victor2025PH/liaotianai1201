# React/Vite 項目自動化部署指南

本指南說明如何為 React/Vite 項目配置自動化部署。

## 📋 項目列表

- **aizkw**: 項目 A
- **tgmini**: 項目 B  
- **hongbao**: 項目 C

## 🚀 快速開始

### 1. 複製模板文件到你的項目

將以下文件複製到你的 React/Vite 項目根目錄：

```bash
# 假設你的項目在 /path/to/your/project
cp react-vite-template/src/config.ts /path/to/your/project/src/
cp react-vite-template/ecosystem.config.js /path/to/your/project/
cp react-vite-template/.github/workflows/deploy.yml /path/to/your/project/.github/workflows/
cp react-vite-template/DEPLOY_TEST.md /path/to/your/project/
```

### 2. 配置 config.ts

編輯 `src/config.ts`，填入你的實際信息：

```typescript
export const siteConfig: SiteConfig = {
  projectName: "你的項目名稱",  // 例如: "AIZKW"
  projectDescription: "項目描述",
  
  contact: {
    telegram: {
      username: "@your_telegram",  // 修改為實際 Telegram 用戶名
      url: "https://t.me/your_telegram",
      displayName: "Telegram 客服",
    },
    whatsapp: {
      number: "+1234567890",  // 修改為實際 WhatsApp 號碼
      url: "https://wa.me/1234567890",
      displayName: "WhatsApp 客服",
    },
    email: {
      address: "support@example.com",  // 修改為實際郵箱
      displayName: "support@example.com",
    },
  },
  
  branding: {
    logoPath: "/logo.png",  // 修改為實際 Logo 路徑
    faviconPath: "/favicon.ico",
    companyName: "你的公司名稱",
  },
};
```

### 3. 替換硬編碼的聯繫方式

在項目中搜索硬編碼的聯繫方式，替換為從 `config.ts` 引用：

**替換前：**
```tsx
<a href="https://t.me/your_telegram">聯繫我們</a>
<img src="/logo.png" alt="Logo" />
```

**替換後：**
```tsx
import { getTelegramUrl, getLogoPath } from '@/config';

<a href={getTelegramUrl()}>聯繫我們</a>
<img src={getLogoPath()} alt="Logo" />
```

### 4. 配置 ecosystem.config.js（可選）

如果使用 PM2 管理進程，編輯 `ecosystem.config.js`：

```javascript
module.exports = {
  apps: [
    {
      name: "aizkw",  // 修改為你的項目名稱
      script: "serve",
      args: "-s dist -l 3000",  // 修改端口號（如果需要）
      // ... 其他配置
    },
  ],
};
```

**注意**: 如果項目使用 Nginx 服務靜態文件，可以忽略 PM2 配置。

### 5. 配置 GitHub Actions

編輯 `.github/workflows/deploy.yml`，修改以下變量：

```yaml
PROJECT_NAME="aizkw"  # 修改為對應項目名稱
PROJECT_DIR="/home/ubuntu/aizkw20251219"  # 修改為實際項目目錄
```

### 6. 配置 GitHub Secrets

在 GitHub 倉庫設置中添加以下 Secrets：

1. 進入倉庫 → Settings → Secrets and variables → Actions
2. 添加以下 Secrets：
   - `SERVER_HOST`: 服務器 IP 地址
   - `SERVER_USER`: SSH 用戶名（通常是 `ubuntu`）
   - `SERVER_SSH_KEY`: SSH 私鑰內容

### 7. 測試部署

1. 提交並推送代碼到 `main` 分支：
   ```bash
   git add .
   git commit -m "配置自動化部署"
   git push origin main
   ```

2. 查看 GitHub Actions：
   - 進入倉庫 → Actions 標籤
   - 查看 "Deploy to Server" workflow 運行狀態

3. 驗證部署：
   - 檢查 `DEPLOY_TEST.md` 文件是否更新
   - 訪問網站確認是否正常運行

## 🔄 如何觸發更新

### 自動觸發
當你向 `main` 分支推送代碼時，GitHub Actions 會自動運行部署流程。

### 手動觸發
1. 進入 GitHub 倉庫
2. 點擊 "Actions" 標籤
3. 選擇 "Deploy to Server" workflow
4. 點擊 "Run workflow" 按鈕
5. 選擇分支（通常是 `main`）
6. 點擊 "Run workflow"

## 📝 部署流程說明

每次部署會執行以下步驟：

1. **代碼拉取** (`git pull`)
   - 從 GitHub 拉取最新代碼

2. **安裝依賴** (`npm install`)
   - 安裝項目依賴包

3. **構建項目** (`npm run build`)
   - 構建生產版本到 `dist` 目錄

4. **重載 Nginx** (`sudo systemctl reload nginx`)
   - 重載 Nginx 配置（如果需要）

5. **重啟 PM2**（如果使用）
   - 重啟 PM2 管理的應用進程

## ⚙️ 項目特定配置

### aizkw 項目
```yaml
PROJECT_NAME="aizkw"
PROJECT_DIR="/home/ubuntu/aizkw20251219"
```

### tgmini 項目
```yaml
PROJECT_NAME="tgmini"
PROJECT_DIR="/home/ubuntu/tgmini20251219"  # 根據實際目錄修改
```

### hongbao 項目
```yaml
PROJECT_NAME="hongbao"
PROJECT_DIR="/home/ubuntu/hongbao20251219"  # 根據實際目錄修改
```

## 🔍 故障排查

### 部署失敗

1. **檢查 GitHub Actions 日誌**
   - 進入 Actions 頁面查看詳細錯誤信息

2. **檢查服務器連接**
   - 確認 SSH 密鑰是否正確
   - 確認服務器 IP 和用戶名是否正確

3. **檢查項目目錄**
   - 確認 `PROJECT_DIR` 路徑是否正確
   - 確認目錄是否存在且有讀寫權限

4. **檢查構建過程**
   - 確認 `npm install` 是否成功
   - 確認 `npm run build` 是否成功生成 `dist` 目錄

### 網站無法訪問

1. **檢查 Nginx 配置**
   - 確認 Nginx 配置是否正確指向 `dist` 目錄
   - 檢查 Nginx 是否正在運行：`sudo systemctl status nginx`

2. **檢查文件權限**
   - 確認 `dist` 目錄權限：`ls -la dist`

3. **檢查端口**
   - 確認端口是否被正確監聽：`netstat -tulpn | grep :80`

## 📚 相關文件

- `src/config.ts`: 全局配置管理
- `ecosystem.config.js`: PM2 進程配置
- `.github/workflows/deploy.yml`: GitHub Actions 部署流程
- `DEPLOY_TEST.md`: 部署測試文件

## 💡 最佳實踐

1. **配置統一管理**: 所有聯繫方式、Logo 路徑等都在 `config.ts` 中管理
2. **版本控制**: 確保所有配置文件都提交到 Git
3. **測試部署**: 在測試環境先驗證部署流程
4. **監控日誌**: 定期檢查部署日誌和應用日誌
5. **備份配置**: 重要配置做好備份

## 🆘 需要幫助？

如果遇到問題，請檢查：
1. GitHub Actions 日誌
2. 服務器日誌：`/var/log/nginx/error.log`
3. PM2 日誌：`pm2 logs`
