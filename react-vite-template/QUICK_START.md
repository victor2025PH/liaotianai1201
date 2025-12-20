# 快速開始指南

## 🎯 目標

為三個 React/Vite 項目（aizkw, tgmini, hongbao）配置自動化部署。

## 📦 已創建的文件

1. **`src/config.ts`** - 統一配置管理文件
2. **`ecosystem.config.js`** - PM2 進程配置文件
3. **`.github/workflows/deploy.yml`** - GitHub Actions 自動化部署配置
4. **`DEPLOY_TEST.md`** - 部署測試文件

## 🚀 快速應用步驟

### 方法一：手動複製（推薦）

#### 步驟 1: 複製文件到項目

對於每個項目（aizkw, tgmini, hongbao），執行：

```bash
# 假設項目在 /home/ubuntu/aizkw20251219
cd /home/ubuntu/aizkw20251219

# 複製配置文件
cp /path/to/template/src/config.ts ./src/
cp /path/to/template/ecosystem.config.js ./
cp /path/to/template/.github/workflows/deploy.yml ./.github/workflows/
cp /path/to/template/DEPLOY_TEST.md ./
```

#### 步驟 2: 修改配置

**編輯 `src/config.ts`**，填入實際信息：

```typescript
export const siteConfig: SiteConfig = {
  projectName: "AIZKW",  // 修改為實際項目名稱
  contact: {
    telegram: {
      username: "@your_telegram",  // 修改為實際 Telegram
      url: "https://t.me/your_telegram",
    },
    whatsapp: {
      number: "+1234567890",  // 修改為實際 WhatsApp
      url: "https://wa.me/1234567890",
    },
    email: {
      address: "support@example.com",  // 修改為實際郵箱
    },
  },
  branding: {
    logoPath: "/logo.png",  // 修改為實際 Logo 路徑
  },
};
```

**編輯 `.github/workflows/deploy.yml`**，修改項目路徑：

```yaml
PROJECT_NAME="aizkw"  # 修改為對應項目名稱
PROJECT_DIR="/home/ubuntu/aizkw20251219"  # 修改為實際目錄
```

**編輯 `ecosystem.config.js`**（如果使用 PM2）：

```javascript
name: "aizkw",  // 修改為對應項目名稱
```

#### 步驟 3: 替換硬編碼的聯繫方式

在項目中搜索並替換硬編碼的聯繫方式：

**搜索關鍵詞：**
- `@your_telegram`
- `https://t.me/`
- `https://wa.me/`
- `support@example.com`
- `/logo.png`

**替換為：**
```tsx
import { siteConfig, getTelegramUrl, getWhatsAppUrl, getEmailAddress, getLogoPath } from '@/config';

// 使用示例
<a href={getTelegramUrl()}>聯繫我們</a>
<img src={getLogoPath()} alt="Logo" />
```

#### 步驟 4: 提交並推送

```bash
git add .
git commit -m "配置自動化部署和統一配置管理"
git push origin main
```

### 方法二：使用腳本（服務器端）

如果模板文件在服務器上，可以使用提供的腳本：

```bash
# 在模板目錄中運行
cd /path/to/react-vite-template
chmod +x apply-to-projects.sh
./apply-to-projects.sh
```

## ✅ 驗證清單

完成配置後，請確認：

- [ ] `src/config.ts` 已填入實際聯繫方式
- [ ] `.github/workflows/deploy.yml` 中的項目路徑正確
- [ ] `ecosystem.config.js` 中的項目名稱正確（如果使用 PM2）
- [ ] 代碼中硬編碼的聯繫方式已替換為 config.ts 引用
- [ ] GitHub Secrets 已配置（SERVER_HOST, SERVER_USER, SERVER_SSH_KEY）
- [ ] 已提交並推送到 GitHub

## 🔄 觸發部署

### 自動觸發
向 `main` 分支推送代碼時自動觸發。

### 手動觸發
1. 進入 GitHub 倉庫
2. 點擊 "Actions" 標籤
3. 選擇 "Deploy to Server"
4. 點擊 "Run workflow"

## 📝 項目特定配置

### aizkw 項目
- 項目目錄: `/home/ubuntu/aizkw20251219`
- GitHub Actions 中的 `PROJECT_NAME`: `"aizkw"`

### tgmini 項目
- 項目目錄: `/home/ubuntu/tgmini20251219`（根據實際修改）
- GitHub Actions 中的 `PROJECT_NAME`: `"tgmini"`

### hongbao 項目
- 項目目錄: `/home/ubuntu/hongbao20251219`（根據實際修改）
- GitHub Actions 中的 `PROJECT_NAME`: `"hongbao"`

## 🆘 常見問題

### Q: 如何確認部署是否成功？
A: 檢查 GitHub Actions 日誌，確認所有步驟都顯示 ✅。同時檢查 `DEPLOY_TEST.md` 文件是否更新。

### Q: 部署失敗怎麼辦？
A: 
1. 查看 GitHub Actions 日誌中的錯誤信息
2. 確認服務器 SSH 連接是否正常
3. 確認項目目錄路徑是否正確
4. 確認 `npm install` 和 `npm run build` 是否成功

### Q: 如何修改聯繫方式？
A: 只需編輯 `src/config.ts` 文件，修改後提交並推送，部署會自動更新。

### Q: 項目使用 Nginx，還需要 PM2 嗎？
A: 如果使用 Nginx 服務靜態文件，可以忽略 PM2 配置。GitHub Actions 會自動重載 Nginx。

## 📚 更多信息

詳細說明請查看 `README_DEPLOYMENT.md`。
