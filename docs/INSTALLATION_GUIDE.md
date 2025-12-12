# 安裝和配置指南

## 📋 目錄

1. [系統要求](#系統要求)
2. [安裝依賴](#安裝依賴)
3. [環境配置](#環境配置)
4. [驗證安裝](#驗證安裝)

## 系統要求

### 後端 (Python)
- Python 3.9 或更高版本
- pip (Python 包管理器)
- 虛擬環境支持

### 前端 (Node.js)
- Node.js 18 或更高版本
- npm 或 yarn

### 系統依賴
- Redis (可選，用於緩存)
- SQLite (默認數據庫)

## 安裝依賴

### 方法 1: 使用自動安裝腳本（推薦）

```bash
# 在項目根目錄執行
bash scripts/server/install-dependencies.sh
```

### 方法 2: 手動安裝

#### 1. 安裝 Python 依賴

```bash
# 進入後端目錄
cd admin-backend

# 創建虛擬環境（如果不存在）
python3 -m venv venv

# 激活虛擬環境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 升級 pip
pip install --upgrade pip

# 安裝依賴
pip install -r requirements.txt

# 安裝根目錄的額外依賴（如果存在）
cd ..
pip install -r requirements.txt
```

#### 2. 安裝 Node.js 依賴

```bash
# 進入前端目錄
cd saas-demo

# 安裝依賴
npm install
```

## 環境配置

### 1. 後端配置

在 `admin-backend` 目錄下創建或編輯 `.env` 文件：

```env
# 應用配置
APP_NAME=Smart TG Admin API
DATABASE_URL=sqlite:///./admin.db
REDIS_URL=redis://localhost:6379/0

# JWT 配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 管理員默認賬號（首次啟動後請修改）
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123

# OpenAI API 配置（用於 AI 聊天功能）
OPENAI_API_KEY=your-openai-api-key-here
AI_PROVIDER=openai  # 或 mock（用於測試）

# Telegram API 配置（用於群組 AI 功能）
TELEGRAM_API_ID=your-telegram-api-id
TELEGRAM_API_HASH=your-telegram-api-hash

# 群組 AI 配置
GROUP_AI_AI_PROVIDER=openai  # openai 或 mock
GROUP_AI_AI_API_KEY=your-openai-api-key-here
GROUP_AI_MAX_ACCOUNTS=100
GROUP_AI_SESSION_FILES_DIRECTORY=sessions
```

### 2. 前端配置

在 `saas-demo` 目錄下創建或編輯 `.env.local` 文件：

```env
# API 基礎 URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_GROUP_AI_API_BASE_URL=http://localhost:8000/api/v1/group-ai

# WebSocket URL
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/notifications/ws

# 環境
NODE_ENV=development
```

### 3. 生成 JWT Secret Key

```bash
# 使用 Python 生成安全的隨機密鑰
cd admin-backend
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

將生成的密鑰複製到 `.env` 文件的 `SECRET_KEY` 字段。

## 驗證安裝

### 1. 驗證 Python 依賴

```bash
cd admin-backend
source venv/bin/activate
python -c "import fastapi, uvicorn, sqlalchemy, pydantic, openai, pyrogram; print('✅ 所有核心依賴已安裝')"
```

### 2. 驗證 Node.js 依賴

```bash
cd saas-demo
npm list --depth=0
```

### 3. 檢查配置文件

```bash
# 檢查後端配置
cd admin-backend
python -c "from app.core.config import get_settings; s = get_settings(); print(f'✅ 配置加載成功: {s.app_name}')"

# 檢查群組 AI 配置
python -c "from group_ai_service.config import get_group_ai_config; c = get_group_ai_config(); print(f'✅ 群組 AI 配置加載成功: {c.ai_provider}')"
```

## 常見問題

### 1. Python 虛擬環境問題

**問題**: `venv/bin/activate: No such file or directory`

**解決方案**:
```bash
cd admin-backend
python3 -m venv venv
source venv/bin/activate
```

### 2. 依賴安裝失敗

**問題**: `pip install` 失敗

**解決方案**:
```bash
# 升級 pip
pip install --upgrade pip setuptools wheel

# 清除緩存
pip cache purge

# 重新安裝
pip install -r requirements.txt
```

### 3. Node.js 版本問題

**問題**: `npm install` 失敗或版本不兼容

**解決方案**:
```bash
# 檢查 Node.js 版本
node --version  # 應該是 18.x 或更高

# 使用 nvm 切換版本（如果已安裝）
nvm use 18

# 清除 npm 緩存
npm cache clean --force

# 刪除 node_modules 和 package-lock.json 後重新安裝
rm -rf node_modules package-lock.json
npm install
```

### 4. OpenAI API 密鑰問題

**問題**: AI 功能無法使用

**解決方案**:
1. 確認 `.env` 文件中的 `OPENAI_API_KEY` 已正確設置
2. 檢查 API 密鑰是否有效：
   ```bash
   python -c "import openai; openai.api_key = 'your-key'; print('✅ API Key 格式正確')"
   ```
3. 如果使用 mock 模式測試，設置 `AI_PROVIDER=mock`

### 5. 數據庫初始化

**問題**: 數據庫表不存在

**解決方案**:
```bash
cd admin-backend
source venv/bin/activate
python -c "from app.db.database import init_db; init_db()"
```

## 下一步

安裝完成後，請參考以下文檔：

1. [部署指南](./DEPLOYMENT_GUIDE.md) - 如何部署到服務器
2. [配置指南](./CONFIGURATION_GUIDE.md) - 詳細配置選項
3. [使用手冊](./USER_MANUAL.md) - 系統使用說明

## 獲取幫助

如果遇到問題，請：

1. 檢查日誌文件：`admin-backend/logs/`
2. 查看 [常見問題](./FAQ.md)
3. 提交 Issue 到項目倉庫

