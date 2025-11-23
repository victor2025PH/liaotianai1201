# 環境變量配置矩陣

本文檔列出所有關鍵環境變量，用於快速配置和排查問題。

> **注意**：生產環境必須修改所有默認值，特別是密碼、API Key 和 JWT Secret。

---

## 環境變量總表

| 變量名 | 所屬服務 | 是否必填 | 本地默認值示例 | 生產建議值 / 說明 | 相關模塊 |
|--------|---------|---------|---------------|-----------------|---------|
| `DATABASE_URL` | admin-backend | 否 | `sqlite:///./admin.db` | `postgresql://user:password@host:5432/dbname` | 數據庫連接 |
| `REDIS_URL` | admin-backend | 否 | `redis://localhost:6379/0` | `redis://redis:6379/0` | Redis 緩存/隊列 |
| `JWT_SECRET` | admin-backend | 是 | `change_me` | **必須修改**：隨機字符串（至少 32 字符） | 認證安全 |
| `JWT_ALGORITHM` | admin-backend | 否 | `HS256` | `HS256` | 認證安全 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | admin-backend | 否 | `60` | `60`（生產可調整為 30-120） | 認證安全 |
| `ADMIN_DEFAULT_EMAIL` | admin-backend | 否 | `admin@example.com` | **必須修改**：管理員郵箱 | 初始化數據 |
| `ADMIN_DEFAULT_PASSWORD` | admin-backend | 否 | `changeme123` | **必須修改**：強密碼 | 初始化數據 |
| `SESSION_SERVICE_URL` | admin-backend | 否 | `http://localhost:8001` | `http://session-service:8001` | 外部服務 |
| `REDPACKET_SERVICE_URL` | admin-backend | 否 | `http://localhost:8002` | `http://redpacket-service:8002` | 外部服務 |
| `MONITORING_SERVICE_URL` | admin-backend | 否 | `http://localhost:8003` | `http://monitoring-service:8003` | 外部服務 |
| `NEXT_PUBLIC_API_BASE_URL` | saas-demo | 否 | `http://localhost:8000/api/v1` | `https://api.example.com/api/v1` | API 基礎地址 |
| `VITE_API_BASE_URL` | admin-frontend | 否 | `http://localhost:8000/api/v1` | `https://api.example.com/api/v1` | API 基礎地址 |
| `TELEGRAM_API_ID` | session_service / main.py | 是 | - | 從 https://my.telegram.org 獲取 | Telegram 機器人 |
| `TELEGRAM_API_HASH` | session_service / main.py | 是 | - | 從 https://my.telegram.org 獲取 | Telegram 機器人 |
| `TELEGRAM_SESSION_NAME` | session_service / main.py | 是 | - | 會話名稱（如 `bot_session`） | Telegram 機器人 |
| `TELEGRAM_SESSION_STRING` | session_service / main.py | 否 | `""` | 會話字符串（可選） | Telegram 機器人 |
| `TELEGRAM_SESSION_FILE` | session_service / main.py | 否 | `""` | 會話文件路徑（如 `./sessions/bot.session`） | Telegram 機器人 |
| `OPENAI_API_KEY` | main.py | 是 | - | OpenAI API Key | AI 服務 |
| `OPENAI_MODEL` | main.py | 否 | `gpt-4` | `gpt-4` 或 `gpt-4-turbo` | AI 服務 |
| `OPENAI_VISION_MODEL` | main.py | 否 | `gpt-4o-mini` | `gpt-4o-mini` 或 `gpt-4-vision-preview` | AI 服務 |
| `OPENAI_STT_PRIMARY` | main.py | 否 | `gpt-4o-mini-transcribe` | `gpt-4o-mini-transcribe` | 語音轉文字 |
| `OPENAI_STT_FALLBACK` | main.py | 否 | `whisper-1` | `whisper-1` | 語音轉文字 |
| `ENABLE_VOICE_RESPONSES` | main.py | 否 | `1` | `1`（啟用）或 `0`（禁用） | 語音功能 |
| `MIN_VOICE_DURATION_SEC` | main.py | 否 | `1` | `1-5` | 語音功能 |
| `MAX_VOICE_DURATION_SEC` | main.py | 否 | `120` | `60-300` | 語音功能 |
| `MAX_VOICE_FILE_MB` | main.py | 否 | `8` | `8-20` | 語音功能 |
| `PROACTIVE_VOICE_MIN_TURN` | main.py | 否 | `4` | `3-10` | 語音功能 |
| `PROACTIVE_VOICE_INTERVAL` | main.py | 否 | `3` | `2-5` | 語音功能 |
| `PROACTIVE_VOICE_TEXT_THRESHOLD` | main.py | 否 | `60` | `50-100` | 語音功能 |
| `TENCENT_SECRET_ID` | main.py | 否 | - | 騰訊雲 Secret ID（可選） | 外部服務 |
| `TENCENT_SECRET_KEY` | main.py | 否 | - | 騰訊雲 Secret Key（可選） | 外部服務 |

---

## 按服務分類

### admin-backend（FastAPI 後端）

**數據庫相關**：
- `DATABASE_URL`：數據庫連接字符串
  - SQLite（開發）：`sqlite:///./admin.db`
  - PostgreSQL（生產）：`postgresql://user:password@host:5432/dbname`

**緩存/隊列相關**：
- `REDIS_URL`：Redis 連接字符串
  - 本地：`redis://localhost:6379/0`
  - Docker：`redis://redis:6379/0`

**認證相關**：
- `JWT_SECRET`：**必須修改**，用於簽名 JWT Token
- `JWT_ALGORITHM`：JWT 算法（默認 `HS256`）
- `ACCESS_TOKEN_EXPIRE_MINUTES`：Token 過期時間（分鐘）

**初始化數據**：
- `ADMIN_DEFAULT_EMAIL`：默認管理員郵箱
- `ADMIN_DEFAULT_PASSWORD`：默認管理員密碼（首次啟動後應立即修改）

**外部服務 URL**：
- `SESSION_SERVICE_URL`：會話服務地址
- `REDPACKET_SERVICE_URL`：紅包服務地址
- `MONITORING_SERVICE_URL`：監控服務地址

### saas-demo（Next.js 前端）

**API 配置**：
- `NEXT_PUBLIC_API_BASE_URL`：後端 API 基礎地址
  - 開發：`http://localhost:8000/api/v1`
  - 生產：`https://api.example.com/api/v1`

> **注意**：Next.js 中只有以 `NEXT_PUBLIC_` 開頭的環境變量才會暴露給瀏覽器。

### admin-frontend（React + Vite 前端）

**API 配置**：
- `VITE_API_BASE_URL`：後端 API 基礎地址
  - 開發：`http://localhost:8000/api/v1`
  - 生產：`https://api.example.com/api/v1`

> **注意**：Vite 中只有以 `VITE_` 開頭的環境變量才會暴露給瀏覽器。

### session_service / main.py（Telegram 機器人）

**Telegram API**：
- `TELEGRAM_API_ID`：**必填**，從 https://my.telegram.org 獲取
- `TELEGRAM_API_HASH`：**必填**，從 https://my.telegram.org 獲取
- `TELEGRAM_SESSION_NAME`：**必填**，會話名稱
- `TELEGRAM_SESSION_STRING`：可選，會話字符串（優先於文件）
- `TELEGRAM_SESSION_FILE`：可選，會話文件路徑

**AI 服務**：
- `OPENAI_API_KEY`：**必填**，OpenAI API Key
- `OPENAI_MODEL`：使用的模型（默認 `gpt-4`）
- `OPENAI_VISION_MODEL`：視覺模型（默認 `gpt-4o-mini`）
- `OPENAI_STT_PRIMARY`：主要 STT 模型
- `OPENAI_STT_FALLBACK`：備用 STT 模型

**語音功能**：
- `ENABLE_VOICE_RESPONSES`：是否啟用語音響應
- `MIN_VOICE_DURATION_SEC`：最小語音時長（秒）
- `MAX_VOICE_DURATION_SEC`：最大語音時長（秒）
- `MAX_VOICE_FILE_MB`：最大語音文件大小（MB）
- `PROACTIVE_VOICE_MIN_TURN`：主動語音最小輪次
- `PROACTIVE_VOICE_INTERVAL`：主動語音間隔（輪次）
- `PROACTIVE_VOICE_TEXT_THRESHOLD`：主動語音文本閾值（字符數）

**外部服務（可選）**：
- `TENCENT_SECRET_ID`：騰訊雲 Secret ID
- `TENCENT_SECRET_KEY`：騰訊雲 Secret Key

---

## 配置文件位置

### 後端（admin-backend）

環境變量從以下位置讀取（按優先級）：
1. 系統環境變量
2. `.env` 文件（項目根目錄或 `admin-backend/` 目錄）
3. `admin-backend/app/core/config.py` 中的默認值

**配置文件**：`admin-backend/app/core/config.py`

### 前端（saas-demo）

環境變量從以下位置讀取：
1. 系統環境變量
2. `.env.local` 文件（`saas-demo/` 目錄）
3. `.env` 文件（`saas-demo/` 目錄）

**注意**：Next.js 在構建時會將 `NEXT_PUBLIC_*` 變量嵌入到代碼中，修改後需要重新構建。

### 前端（admin-frontend）

環境變量從以下位置讀取：
1. 系統環境變量
2. `.env.local` 文件（`admin-frontend/` 目錄）
3. `.env` 文件（`admin-frontend/` 目錄）

**注意**：Vite 在構建時會將 `VITE_*` 變量嵌入到代碼中，修改後需要重新構建。

### 主程序（main.py）

環境變量從以下位置讀取：
1. 系統環境變量
2. `.env` 文件（項目根目錄）
3. `config.py` 中的默認值

**配置文件**：`config.py`（項目根目錄）

---

## 生產環境檢查清單

### 必須修改的變量

- [ ] `JWT_SECRET`：生成至少 32 字符的隨機字符串
- [ ] `ADMIN_DEFAULT_EMAIL`：設置實際管理員郵箱
- [ ] `ADMIN_DEFAULT_PASSWORD`：設置強密碼（首次登錄後立即修改）
- [ ] `DATABASE_URL`：使用 PostgreSQL（生產環境不建議 SQLite）
- [ ] `TELEGRAM_API_ID` 和 `TELEGRAM_API_HASH`：確保已正確配置
- [ ] `OPENAI_API_KEY`：確保已正確配置

### 建議修改的變量

- [ ] `REDIS_URL`：使用專用 Redis 實例（非本地）
- [ ] `NEXT_PUBLIC_API_BASE_URL`：設置生產 API 地址
- [ ] `VITE_API_BASE_URL`：設置生產 API 地址
- [ ] `SESSION_SERVICE_URL`、`REDPACKET_SERVICE_URL`、`MONITORING_SERVICE_URL`：根據實際部署調整

### 安全檢查

- [ ] 所有 `.env` 文件已添加到 `.gitignore`
- [ ] 生產環境的 `.env` 文件權限設置為 `600`（僅所有者可讀寫）
- [ ] 不要在代碼中硬編碼敏感信息
- [ ] 使用密鑰管理服務（如 AWS Secrets Manager、HashiCorp Vault）存儲敏感信息

---

## 環境變量驗證

### 後端驗證

```bash
# 檢查 admin-backend 配置
cd admin-backend
poetry run python -c "from app.core.config import get_settings; s = get_settings(); print(f'DB: {s.database_url[:20]}...')"
```

### 前端驗證

```bash
# 檢查 saas-demo 環境變量（構建時）
cd saas-demo
npm run build
# 檢查構建輸出中是否包含正確的 API_BASE_URL

# 檢查 admin-frontend 環境變量（構建時）
cd admin-frontend
npm run build
# 檢查構建輸出中是否包含正確的 API_BASE_URL
```

---

## 故障排查

### 問題：後端無法連接數據庫

**檢查**：
1. `DATABASE_URL` 是否正確
2. 數據庫服務是否運行
3. 網絡連接是否正常

### 問題：前端無法調用後端 API

**檢查**：
1. `NEXT_PUBLIC_API_BASE_URL` 或 `VITE_API_BASE_URL` 是否正確
2. 後端服務是否運行在指定端口
3. CORS 配置是否正確（`admin-backend/app/main.py`）

### 問題：Telegram 機器人無法啟動

**檢查**：
1. `TELEGRAM_API_ID` 和 `TELEGRAM_API_HASH` 是否正確
2. `TELEGRAM_SESSION_NAME` 或 `TELEGRAM_SESSION_FILE` 是否配置
3. 會話文件是否存在且有效

---

**最後更新**: 2024-12-19
