# 快速開始指南

## 🚀 一鍵安裝和配置

### 在 Linux 服務器上

```bash
# 1. 安裝所有依賴
bash scripts/server/install-dependencies.sh

# 2. 配置環境變量
bash scripts/server/configure-env.sh

# 3. 編輯配置文件（必需）
nano admin-backend/.env
# 填入你的 OPENAI_API_KEY 等配置

# 4. 驗證安裝
cd admin-backend
source venv/bin/activate
python -c "import fastapi, uvicorn, openai, pyrogram; print('✅ 依賴安裝成功')"
```

### 在 Windows 本地開發環境

```powershell
# 1. 安裝 Python 依賴
cd admin-backend
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# 2. 安裝 Node.js 依賴
cd ..\saas-demo
npm install

# 3. 配置環境變量
# 手動創建 admin-backend/.env 和 saas-demo/.env.local
# 參考下面的配置模板
```

## 📝 必需配置項

### admin-backend/.env

```env
# 必須配置
SECRET_KEY=你的安全密鑰（使用 python -c "import secrets; print(secrets.token_urlsafe(32))" 生成）
OPENAI_API_KEY=你的OpenAI API密鑰

# 可選配置
TELEGRAM_API_ID=你的Telegram API ID
TELEGRAM_API_HASH=你的Telegram API Hash
GROUP_AI_AI_PROVIDER=openai
```

### saas-demo/.env.local

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_GROUP_AI_API_BASE_URL=http://localhost:8000/api/v1/group-ai
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/notifications/ws
```

## ✅ 驗證步驟

1. **檢查 Python 依賴**
   ```bash
   cd admin-backend
   source venv/bin/activate
   python -c "import fastapi, uvicorn, sqlalchemy, pydantic, openai, pyrogram; print('✅ OK')"
   ```

2. **檢查 Node.js 依賴**
   ```bash
   cd saas-demo
   npm list --depth=0
   ```

3. **測試配置加載**
   ```bash
   cd admin-backend
   source venv/bin/activate
   python -c "from app.core.config import get_settings; print('✅ 配置加載成功')"
   ```

## 🔑 獲取 API 密鑰

### OpenAI API Key
1. 訪問 https://platform.openai.com/api-keys
2. 登錄並創建新的 API Key
3. 複製到 `.env` 文件的 `OPENAI_API_KEY`

### Telegram API Credentials
1. 訪問 https://my.telegram.org/apps
2. 登錄並創建應用
3. 獲取 `api_id` 和 `api_hash`
4. 複製到 `.env` 文件

## 📚 詳細文檔

- [完整安裝指南](./INSTALLATION_GUIDE.md)
- [配置說明](./CONFIGURATION_GUIDE.md)
- [部署指南](./DEPLOYMENT_GUIDE.md)

