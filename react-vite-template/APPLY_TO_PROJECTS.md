# 如何應用到各自的 GitHub 倉庫

## 📋 三個項目配置指南

本模板需要應用到以下三個獨立的 React/Vite 項目：
- **aizkw** - 項目 A
- **tgmini** - 項目 B
- **hongbao** - 項目 C

## 🚀 快速應用步驟

### 對於每個項目（aizkw, tgmini, hongbao）

#### 步驟 1: 克隆或進入項目倉庫

```bash
# 如果項目在本地
cd /path/to/aizkw  # 或 tgmini, hongbao

# 如果項目在服務器上
cd /home/ubuntu/aizkw20251219  # 根據實際目錄修改
```

#### 步驟 2: 複製模板文件

從模板目錄複製以下文件到項目：

```bash
# 假設模板在當前倉庫的 react-vite-template 目錄
TEMPLATE_DIR="/path/to/telegram-ai-system/react-vite-template"

# 複製配置文件
cp ${TEMPLATE_DIR}/src/config.ts ./src/
cp ${TEMPLATE_DIR}/ecosystem.config.js ./
cp ${TEMPLATE_DIR}/.github/workflows/deploy.yml ./.github/workflows/
cp ${TEMPLATE_DIR}/DEPLOY_TEST.md ./
```

#### 步驟 3: 修改項目特定配置

**編輯 `src/config.ts`** - 填入實際聯繫方式：

```typescript
export const siteConfig: SiteConfig = {
  projectName: "AIZKW",  // 修改為: "AIZKW", "TGMINI", 或 "HONGBAO"
  contact: {
    telegram: {
      username: "@your_telegram",  // 填入實際 Telegram
      url: "https://t.me/your_telegram",
    },
    // ... 其他配置
  },
};
```

**編輯 `.github/workflows/deploy.yml`** - 修改項目路徑：

```yaml
# 對於 aizkw 項目
PROJECT_NAME="aizkw"
PROJECT_DIR="/home/ubuntu/aizkw20251219"

# 對於 tgmini 項目
PROJECT_NAME="tgmini"
PROJECT_DIR="/home/ubuntu/tgmini20251219"  # 根據實際目錄修改

# 對於 hongbao 項目
PROJECT_NAME="hongbao"
PROJECT_DIR="/home/ubuntu/hongbao20251219"  # 根據實際目錄修改
```

**編輯 `ecosystem.config.js`**（如果使用 PM2）：

```javascript
module.exports = {
  apps: [
    {
      name: "aizkw",  // 修改為對應項目名稱
      // ...
    },
  ],
};
```

#### 步驟 4: 配置 GitHub Secrets

在每個項目的 GitHub 倉庫中設置 Secrets：

1. 進入倉庫 → **Settings** → **Secrets and variables** → **Actions**
2. 添加以下 Secrets：
   - `SERVER_HOST`: 服務器 IP 地址
   - `SERVER_USER`: SSH 用戶名（通常是 `ubuntu`）
   - `SERVER_SSH_KEY`: SSH 私鑰內容

#### 步驟 5: 替換硬編碼的聯繫方式

在項目代碼中搜索並替換硬編碼的聯繫方式：

```bash
# 搜索硬編碼的聯繫方式
grep -r "https://t.me/" src/
grep -r "support@example.com" src/
grep -r "/logo.png" src/
```

替換為從 `config.ts` 引用：

```tsx
import { getTelegramUrl, getEmailAddress, getLogoPath } from '@/config';

// 使用
<a href={getTelegramUrl()}>聯繫我們</a>
<img src={getLogoPath()} alt="Logo" />
```

#### 步驟 6: 提交並推送

```bash
git add .
git commit -m "配置自動化部署和統一配置管理"
git push origin main
```

推送後，GitHub Actions 會自動觸發部署！

## ✅ 驗證部署

### 檢查 GitHub Actions

1. 進入項目 GitHub 倉庫
2. 點擊 **Actions** 標籤
3. 查看 "Deploy to Server" workflow 運行狀態
4. 確認所有步驟都顯示 ✅

### 檢查部署結果

1. 檢查 `DEPLOY_TEST.md` 文件是否更新
2. 訪問網站確認是否正常運行
3. 檢查服務器日誌（如果需要）

## 📝 項目特定配置示例

### aizkw 項目配置

```yaml
# .github/workflows/deploy.yml
PROJECT_NAME="aizkw"
PROJECT_DIR="/home/ubuntu/aizkw20251219"
```

```typescript
// src/config.ts
projectName: "AIZKW"
```

### tgmini 項目配置

```yaml
# .github/workflows/deploy.yml
PROJECT_NAME="tgmini"
PROJECT_DIR="/home/ubuntu/tgmini20251219"  # 根據實際修改
```

```typescript
// src/config.ts
projectName: "TGMINI"
```

### hongbao 項目配置

```yaml
# .github/workflows/deploy.yml
PROJECT_NAME="hongbao"
PROJECT_DIR="/home/ubuntu/hongbao20251219"  # 根據實際修改
```

```typescript
// src/config.ts
projectName: "HONGBAO"
```

## 🔄 後續更新

以後如果需要修改聯繫方式，只需：

1. 編輯 `src/config.ts`
2. 提交並推送：
   ```bash
   git add src/config.ts
   git commit -m "更新聯繫方式"
   git push origin main
   ```
3. GitHub Actions 會自動部署更新

## 🆘 需要幫助？

如果遇到問題：
1. 查看 GitHub Actions 日誌
2. 檢查服務器 SSH 連接
3. 確認項目目錄路徑是否正確
4. 確認 GitHub Secrets 是否正確配置
