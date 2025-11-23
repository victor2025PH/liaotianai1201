# 系統架構文檔

本文檔詳細說明「聊天AI08-繼續開發」項目的系統架構、模塊劃分、數據流和運行流程。

> **文檔版本**: v1.0  
> **最後更新**: 2024-12-19  
> **基於**: PROJECT_STRUCTURE.md

---

## 目錄

1. [系統架構概述](#系統架構概述)
2. [模塊劃分](#模塊劃分)
3. [前後端交互流程](#前後端交互流程)
4. [數據流](#數據流)
5. [系統運行流程](#系統運行流程)
6. [外部依賴](#外部依賴)
7. [錯誤處理機制](#錯誤處理機制)
8. [架構圖](#架構圖)

---

## 系統架構概述

本系統是一個**多層次、模塊化**的 Telegram 業務聊天機器人與管理後台系統，採用**前後端分離**架構：

- **前端層**：兩個獨立的前端應用（Next.js + shadcn/ui、React + Ant Design），提供管理界面
- **後端層**：FastAPI RESTful API 服務，提供統一的數據接口
- **業務層**：Telegram 機器人主程序（`main.py`），處理 Telegram 消息和業務邏輯
- **服務層**：會話服務（`session_service`），管理 Telegram 會話池和分發
- **工具層**：工具函數（`utils`）、腳本（`scripts`）、工具（`tools`），提供輔助功能

### 核心設計理念

1. **分層架構**：清晰的職責分離，前端、後端、業務邏輯、數據存儲各司其職
2. **模塊化設計**：每個模塊獨立，易於維護和擴展
3. **容錯機制**：多層錯誤處理，Mock 數據 Fallback，確保系統穩定性
4. **可擴展性**：支持多實例部署、水平擴展
5. **可觀測性**：完整的日誌、監控、告警機制

---

## 模塊劃分

### 1. session_service（會話服務模塊）

**位置**: `session_service/`

**職責**：
- 管理 Telegram 會話池（Session Pool）
- 會話分發邏輯（Dispatch）
- 會話操作（Actions）
- 紅包相關功能（Redpacket）

**核心文件**：
- `session_pool.py`：會話池管理，維護多個 Telegram 會話實例
- `dispatch.py`：會話分發邏輯，根據策略分配會話
- `actions.py`：會話操作（發送消息、接收消息等）
- `redpacket.py`：紅包事件處理

**對外接口**：
- 通過 HTTP API 提供服務（端口 8001，可配置）
- 提供 `/api/accounts`、`/api/activities` 等端點

### 2. admin-backend（FastAPI 後端）

**位置**: `admin-backend/`

**職責**：
- 提供 RESTful API 服務
- 數據聚合和轉換
- 用戶認證和授權（RBAC）
- 數據庫管理（SQLAlchemy ORM）

**核心文件**：
- `app/main.py`：FastAPI 應用入口（端口 8000）
- `app/api/routes.py`：主要 API 路由定義
- `app/services/data_sources.py`：數據源服務，對接外部 API 和生成 Mock 數據
- `app/models/`：數據庫模型（User、Role、Permission 等）
- `app/schemas/`：Pydantic 數據驗證模型
- `app/core/config.py`：應用配置（環境變量、數據庫連接）

**主要 API 端點**：
- `/health`：健康檢查
- `/api/v1/dashboard`：Dashboard 統計數據
- `/api/v1/sessions`：會話列表（支持分頁、搜索、時間範圍過濾）
- `/api/v1/logs`：日誌列表（支持分頁、級別過濾、搜索）
- `/api/v1/metrics`：指標數據（響應時間趨勢、系統狀態）
- `/api/v1/system/monitor`：系統監控數據
- `/api/v1/settings/alerts`：告警設置（GET/POST）

### 3. saas-demo（Next.js 前端控制台）

**位置**: `saas-demo/`

**職責**：
- 提供現代化的管理控制台界面
- 數據可視化（圖表、統計卡片）
- 用戶交互（搜索、過濾、分頁）

**技術棧**：
- Next.js 14+（App Router）
- Tailwind CSS
- shadcn/ui 組件庫
- TypeScript

**核心文件**：
- `src/app/page.tsx`：Dashboard 首頁（`/`）
- `src/app/sessions/page.tsx`：會話列表頁面（`/sessions`）
- `src/app/logs/page.tsx`：日誌中心頁面（`/logs`）
- `src/app/monitoring/page.tsx`：系統監控頁面（`/monitoring`）
- `src/app/settings/alerts/page.tsx`：告警設置頁面（`/settings/alerts`）
- `src/lib/api-client.ts`：統一 API 客戶端（超時處理、Mock Fallback、錯誤處理）
- `src/lib/api.ts`：API 函數定義和類型定義
- `src/hooks/`：React Hooks（數據獲取、狀態管理）

**特性**：
- 自動 Mock 數據 Fallback（後端不可用時）
- 統一的錯誤處理和 Toast 提示
- 響應式設計（支持移動端）
- 深色主題支持

### 4. admin-frontend（React + Vite 前端）

**位置**: `admin-frontend/`

**職責**：
- 提供另一個管理界面（可選，用於不同場景）
- 賬戶管理、活動記錄、告警管理、命令管理

**技術棧**：
- React 18+
- Vite
- Ant Design
- TypeScript

**核心文件**：
- `src/main.tsx`：應用入口
- `src/pages/Dashboard.tsx`：儀表板
- `src/pages/Accounts.tsx`：賬戶管理
- `src/services/api.ts`：API 封裝（axios）

### 5. utils（工具函數模塊）

**位置**: `utils/`

**職責**：
- 提供業務邏輯工具函數
- AI 相關功能（業務 AI、上下文管理、提示詞管理）
- 媒體處理（語音轉文字、文字轉語音、媒體文件處理）
- 數據管理（數據庫管理、Excel 管理、自動備份）
- 用戶工具（用戶工具、標籤分析、好友問候）

**核心文件**：
- `business_ai.py`：業務 AI 邏輯（調用 OpenAI API）
- `ai_context_manager.py`：AI 上下文管理（對話歷史）
- `speech_to_text.py`：語音轉文字（STT）
- `tts_voice.py`：文字轉語音（TTS）
- `db_manager.py`：數據庫管理
- `excel_manager.py`：Excel 文件處理
- `auto_backup.py`：自動備份
- `prompt_manager.py`：提示詞管理

### 6. tools（工具腳本）

**位置**: `tools/`

**職責**：
- 提供輔助工具腳本
- 對話場景編輯器
- 會話管理工具

**核心文件**：
- `dialogue_scene_editor.py`：對話場景編輯器
- `validate_dialogue_yaml.py`：YAML 驗證工具
- `voice_script_builder.py`：語音腳本構建器
- `session_manager/`：會話管理工具（生成會話、導入會話、賬戶狀態管理）

### 7. scripts（腳本目錄）

**位置**: `scripts/`

**職責**：
- 提供系統腳本
- 數據庫遷移
- 登錄腳本

**核心文件**：
- `run_migrations.py`：數據庫遷移腳本
- `login.py`：登錄腳本

### 8. main.py（Telegram 機器人主程序）

**位置**: `main.py`（項目根目錄）

**職責**：
- Telegram 機器人主程序入口
- 處理 Telegram 消息和事件
- 調用業務邏輯（AI 回復、語音處理、媒體處理）
- 管理後台任務（自動問候、批量回復、標籤分析、備份）

**核心功能**：
- 消息處理（文本、語音、圖片、視頻）
- AI 業務回復（調用 `utils/business_ai.py`）
- 語音轉文字（調用 `utils/speech_to_text.py`）
- 文字轉語音（調用 `utils/tts_voice.py`）
- 自動問候新好友
- 批量自動回復
- 標籤分析
- 自動備份

**依賴**：
- Pyrogram（Telegram 客戶端庫）
- OpenAI API（AI 服務）
- 騰訊雲（可選，TTS）

---

## 前後端交互流程

### 前端（saas-demo）→ 後端（admin-backend）交互流程

```
┌─────────────────┐
│  saas-demo      │
│  (Next.js)      │
│  Port: 3000     │
└────────┬────────┘
         │
         │ HTTP Request
         │ (GET /api/v1/dashboard)
         │
         ▼
┌─────────────────┐
│  api-client.ts  │
│  (統一客戶端)    │
└────────┬────────┘
         │
         │ 1. 檢查超時（5秒）
         │ 2. 處理錯誤（4xx/5xx）
         │ 3. Mock Fallback（如果失敗）
         │
         ▼
┌─────────────────┐
│  admin-backend  │
│  (FastAPI)      │
│  Port: 8000     │
└────────┬────────┘
         │
         │ 調用 data_sources
         │
         ▼
┌─────────────────┐
│  data_sources.py│
│  (數據源服務)    │
└────────┬────────┘
         │
         │ 1. 嘗試調用外部服務
         │    (session_service, redpacket_service)
         │ 2. 如果失敗，返回 Mock 數據
         │
         ▼
┌─────────────────┐
│  外部服務       │
│  (可選)         │
│  Port: 8001+    │
└─────────────────┘
```

### 詳細交互示例

#### 1. Dashboard 數據獲取

```
用戶訪問 http://localhost:3000/
  ↓
Next.js 渲染 page.tsx
  ↓
useDashboardData Hook 調用
  ↓
api-client.ts: apiGet('/dashboard')
  ↓
發送 HTTP GET 請求到 http://localhost:8000/api/v1/dashboard
  ↓
admin-backend/app/api/routes.py: get_dashboard()
  ↓
admin-backend/app/services/data_sources.py: get_dashboard_stats()
  ↓
嘗試調用 session_service (http://localhost:8001/api/...)
  ↓
如果成功：返回真實數據
如果失敗：返回 Mock 數據
  ↓
返回 JSON 響應
  ↓
前端解析並渲染 Dashboard
```

#### 2. 會話列表獲取（帶過濾）

```
用戶訪問 http://localhost:3000/sessions?q=test&range=24h
  ↓
Next.js 渲染 sessions/page.tsx
  ↓
useSessionsWithFilters Hook 調用
  ↓
api-client.ts: apiGet('/sessions', { q: 'test', range: '24h' })
  ↓
發送 HTTP GET 請求到 http://localhost:8000/api/v1/sessions?q=test&range=24h
  ↓
admin-backend/app/api/routes.py: list_sessions(q='test', time_range='24h')
  ↓
admin-backend/app/services/data_sources.py: get_sessions(q='test', time_range='24h')
  ↓
返回過濾後的會話列表
  ↓
前端渲染表格和分頁
```

---

## 數據流

### 完整數據流：用戶輸入 → Telegram → session_service → FastAPI → DB

```
┌─────────────┐
│  用戶       │
│  (Telegram) │
└──────┬──────┘
       │
       │ 發送消息
       │
       ▼
┌─────────────────┐
│  Telegram API   │
│  (Pyrogram)     │
└──────┬──────────┘
       │
       │ 接收消息事件
       │
       ▼
┌─────────────────┐
│  main.py        │
│  (機器人主程序) │
└──────┬──────────┘
       │
       │ 1. 解析消息類型（文本/語音/圖片）
       │ 2. 調用業務邏輯
       │
       ├─────────────────┬─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  business_  │  │  speech_to_ │  │  analyze_   │
│  ai.py      │  │  text.py    │  │  image_     │
│  (AI回復)   │  │  (STT)      │  │  message()  │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                 │
       │                │                 │
       └────────────────┴─────────────────┘
                        │
                        │ 調用 OpenAI API
                        │
                        ▼
                ┌───────────────┐
                │  OpenAI API   │
                │  (GPT-4/Vision)│
                └───────┬───────┘
                        │
                        │ 返回 AI 回復
                        │
                        ▼
                ┌───────────────┐
                │  main.py      │
                │  (生成回復)   │
                └───────┬───────┘
                        │
                        │ 可選：TTS 轉語音
                        │
                        ▼
                ┌───────────────┐
                │  tts_voice.py  │
                │  (騰訊雲 TTS) │
                └───────┬───────┘
                        │
                        │ 發送回復
                        │
                        ▼
                ┌───────────────┐
                │  Telegram API  │
                │  (發送給用戶)  │
                └────────────────┘
                        │
                        │ 記錄到數據庫
                        │
                        ▼
                ┌───────────────┐
                │  db_manager.py │
                │  (SQLite/DB)  │
                └───────┬───────┘
                        │
                        │ 數據持久化
                        │
                        ▼
                ┌───────────────┐
                │  chat_history  │
                │  .db           │
                └────────────────┘
```

### 管理後台數據流

```
┌─────────────┐
│  管理員     │
│  (瀏覽器)   │
└──────┬──────┘
       │
       │ 訪問 http://localhost:3000
       │
       ▼
┌─────────────────┐
│  saas-demo      │
│  (Next.js)      │
└──────┬──────────┘
       │
       │ API 請求
       │
       ▼
┌─────────────────┐
│  admin-backend  │
│  (FastAPI)      │
└──────┬──────────┘
       │
       │ 1. 查詢數據庫（admin.db）
       │ 2. 調用 session_service
       │ 3. 聚合數據
       │
       ├─────────────────┬─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  admin.db   │  │  session_   │  │  chat_      │
│  (SQLite)   │  │  service    │  │  history.db │
│             │  │  (Port 8001)│  │  (SQLite)   │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## 系統運行流程

### 1. 系統啟動流程

```
1. 啟動 admin-backend (FastAPI)
   ├─ 加載環境變量 (config.py)
   ├─ 初始化數據庫 (Base.metadata.create_all)
   ├─ 創建默認管理員用戶
   └─ 啟動 uvicorn 服務器 (Port 8000)

2. 啟動 saas-demo (Next.js)
   ├─ 加載環境變量 (NEXT_PUBLIC_API_BASE_URL)
   ├─ 構建 Next.js 應用
   └─ 啟動開發服務器 (Port 3000)

3. 啟動 main.py (Telegram 機器人)
   ├─ 加載環境變量 (config.py)
   ├─ 初始化數據庫 (auto_init_db)
   ├─ 初始化 Excel (auto_init_excel)
   ├─ 初始化 Pyrogram 客戶端
   ├─ 註冊消息處理器
   ├─ 啟動後台任務：
   │   ├─ 自動問候新好友 (每 300 秒)
   │   ├─ 批量問候和回復 (每 180 秒)
   │   ├─ 標籤分析 (每 900 秒)
   │   └─ 自動備份 (每 3600 秒)
   └─ 進入 idle 狀態，等待消息
```

### 2. 消息處理流程

```
Telegram 消息到達
  ↓
main.py 接收消息事件
  ↓
判斷消息類型：
  ├─ 文本消息
  │   ├─ 檢測語言
  │   ├─ 檢查關鍵詞（按鈕、語音請求、機器人查詢）
  │   ├─ 獲取用戶資料
  │   ├─ 調用 AI 業務回復 (business_ai.py)
  │   ├─ 生成回復文本
  │   ├─ 可選：TTS 轉語音
  │   └─ 發送回復
  │
  ├─ 語音消息
  │   ├─ 下載語音文件
  │   ├─ 檢查語音質量（時長、大小）
  │   ├─ STT 轉文字 (speech_to_text.py)
  │   ├─ 處理文字（同文本消息流程）
  │   └─ 發送回復
  │
  ├─ 圖片消息
  │   ├─ 下載圖片
  │   ├─ 分析圖片 (analyze_image_message)
  │   ├─ 生成回復
  │   └─ 發送回復
  │
  └─ 視頻消息
      ├─ 下載視頻
      ├─ 提取音頻（如果包含語音）
      ├─ STT 轉文字
      ├─ 處理文字
      └─ 發送回復
  ↓
記錄到數據庫 (db_manager.py)
  ↓
更新用戶資料 (update_user_profile_async)
```

### 3. 後台任務流程

```
BackgroundTaskManager 啟動
  ↓
並行運行四個後台任務：

1. 自動問候新好友 (_run_auto_greet)
   ├─ 讀取 Excel 文件 (excel_manager.py)
   ├─ 查找新好友
   ├─ 生成問候消息
   ├─ 發送問候
   └─ 記錄到數據庫

2. 批量問候和回復 (_run_auto_batch_greet_and_reply)
   ├─ 讀取 Excel 文件
   ├─ 查找需要問候的用戶
   ├─ 批量生成問候消息
   ├─ 批量發送
   └─ 記錄到數據庫

3. 標籤分析 (_run_tag_analyzer)
   ├─ 讀取所有用戶
   ├─ 分析用戶標籤 (tag_analyzer.py)
   ├─ 更新用戶資料
   └─ 記錄到數據庫

4. 自動備份 (_run_auto_backup)
   ├─ 備份數據庫 (chat_history.db)
   ├─ 備份 Excel 文件
   ├─ 備份日誌文件
   └─ 記錄備份結果
```

---

## 外部依賴

### 1. Telegram API

**用途**：
- 接收和發送 Telegram 消息
- 管理 Telegram 會話

**依賴庫**：
- `pyrogram`：Telegram 客戶端庫

**配置**：
- `TELEGRAM_API_ID`：Telegram API ID
- `TELEGRAM_API_HASH`：Telegram API Hash
- `TELEGRAM_SESSION_NAME`：會話名稱
- `TELEGRAM_SESSION_FILE`：會話文件路徑（可選）

**使用位置**：
- `main.py`：主程序使用 Pyrogram 客戶端
- `session_service/`：會話服務管理多個會話

### 2. OpenAI API

**用途**：
- AI 文本生成（業務回復）
- 圖片分析（Vision API）
- 語音轉文字（Whisper API）

**依賴庫**：
- `openai`：OpenAI Python SDK

**配置**：
- `OPENAI_API_KEY`：OpenAI API Key
- `OPENAI_MODEL`：默認模型（如 `gpt-4`）
- `OPENAI_VISION_MODEL`：視覺模型（如 `gpt-4o-mini`）
- `OPENAI_STT_PRIMARY`：主要 STT 模型（如 `gpt-4o-mini-transcribe`）
- `OPENAI_STT_FALLBACK`：備用 STT 模型（如 `whisper-1`）

**使用位置**：
- `utils/business_ai.py`：業務 AI 回復
- `utils/speech_to_text.py`：語音轉文字

### 3. Excel 文件

**用途**：
- 存儲用戶數據（好友列表、用戶資料）
- 批量導入/導出

**依賴庫**：
- `pandas`：數據處理
- `openpyxl`：Excel 文件讀寫

**配置**：
- `EXCEL_PATH`：Excel 文件路徑（`data/friends.xlsx`）

**使用位置**：
- `utils/excel_manager.py`：Excel 管理
- `utils/auto_batch_greet_and_reply.py`：批量問候和回復
- `utils/friend_auto_add.py`：自動添加好友

### 4. STT（語音轉文字）

**用途**：
- 將語音消息轉換為文字
- 支持多種 STT 服務

**實現**：
- `utils/speech_to_text.py`：STT 封裝

**支持的服務**：
- OpenAI Whisper API
- OpenAI GPT-4o-mini Transcribe API
- 騰訊雲 STT（可選）

**使用位置**：
- `main.py`：處理語音消息時調用

### 5. TTS（文字轉語音）

**用途**：
- 將文字回復轉換為語音
- 支持主動語音回復

**實現**：
- `utils/tts_voice.py`：TTS 封裝

**支持的服務**：
- 騰訊雲 TTS（主要）
- OpenAI TTS（可選）

**配置**：
- `TENCENT_SECRET_ID`：騰訊雲 Secret ID
- `TENCENT_SECRET_KEY`：騰訊雲 Secret Key
- `ENABLE_VOICE_RESPONSES`：是否啟用語音回復

**使用位置**：
- `main.py`：生成語音回復時調用

### 6. 數據庫

**用途**：
- 存儲聊天歷史
- 存儲用戶資料
- 存儲管理後台數據

**數據庫類型**：
- SQLite（開發環境，默認）
- PostgreSQL（生產環境，可選）

**配置**：
- `DATABASE_URL`：數據庫連接字符串
  - SQLite：`sqlite:///./admin.db`（admin-backend）
  - SQLite：`data/chat_history.db`（main.py）

**使用位置**：
- `admin-backend/app/db.py`：後端數據庫連接
- `utils/db_manager.py`：主程序數據庫管理

---

## 錯誤處理機制

### 1. 前端錯誤處理（saas-demo）

#### API 調用錯誤處理

**位置**：`saas-demo/src/lib/api-client.ts`

**處理流程**：
```
API 調用
  ↓
超時檢查（5 秒）
  ├─ 超時 → 返回 Mock 數據 + _isMock: true
  └─ 未超時 → 繼續
  ↓
HTTP 狀態碼檢查
  ├─ 4xx（客戶端錯誤）
  │   ├─ 顯示 Toast 提示
  │   └─ 返回 error 對象
  ├─ 5xx（服務器錯誤）
  │   ├─ 返回 Mock 數據（如果可用）
  │   └─ 返回 error 對象
  └─ 200（成功）
      └─ 返回 data 對象
```

**Mock Fallback 機制**：
- 如果 API 調用失敗（超時、5xx、網絡錯誤），自動切換到 Mock 數據
- 在頁面上顯示「當前展示的是模擬數據」提示
- 確保頁面不會因為後端不可用而崩潰

#### 組件錯誤處理

**位置**：`saas-demo/src/components/error-boundary.tsx`

**處理流程**：
```
組件渲染
  ↓
發生 JavaScript 錯誤
  ↓
ErrorBoundary 捕獲錯誤
  ↓
顯示友好錯誤提示
  ├─ 錯誤信息
  ├─ 重試按鈕
  └─ 不影響其他組件
```

### 2. 後端錯誤處理（admin-backend）

#### API 端點錯誤處理

**位置**：`admin-backend/app/api/routes.py`

**處理方式**：
- FastAPI 自動處理 HTTP 異常（400、404、500 等）
- 使用 Pydantic 驗證請求參數
- 返回標準 JSON 錯誤響應

#### 數據源錯誤處理

**位置**：`admin-backend/app/services/data_sources.py`

**處理流程**：
```
調用外部服務（session_service、redpacket_service）
  ↓
使用 _safe_get() 封裝
  ├─ 設置超時（5 秒）
  ├─ 捕獲異常
  └─ 返回 None（如果失敗）
  ↓
檢查返回結果
  ├─ 成功 → 返回真實數據
  └─ 失敗 → 返回 Mock 數據
```

### 3. 主程序錯誤處理（main.py）

#### 消息處理錯誤處理

**處理方式**：
- 使用 `try-except` 包裹消息處理邏輯
- 記錄錯誤日誌（`utils/logger.py`）
- 發送友好錯誤提示給用戶（如果可能）

#### 後台任務錯誤處理

**位置**：`main.py` 中的 `BackgroundTaskManager`

**處理流程**：
```
後台任務執行
  ↓
捕獲異常（asyncio.CancelledError 除外）
  ↓
記錄錯誤日誌
  ↓
繼續運行（不中斷任務）
```

### 4. 數據庫錯誤處理

**處理方式**：
- 使用 SQLAlchemy 的異常處理
- 數據庫連接失敗時回退到 SQLite（如果配置了 PostgreSQL）
- 遷移失敗時自動備份

---

## 架構圖

### 系統整體架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        用戶層                                    │
├─────────────────────────────────────────────────────────────────┤
│  Telegram 用戶          │  管理員（瀏覽器）                      │
└──────────┬──────────────┴──────────────┬───────────────────────┘
           │                              │
           │                              │
           ▼                              ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│  Telegram API        │      │  saas-demo (Next.js)        │
│  (Pyrogram)          │      │  Port: 3000                 │
└──────────┬───────────┘      │  - Dashboard                │
           │                  │  - Sessions                  │
           │                  │  - Logs                       │
           │                  │  - Monitoring                 │
           │                  │  - Settings                   │
           │                  └──────────┬───────────────────┘
           │                             │
           │                             │ HTTP API
           │                             │
           ▼                             ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│  main.py             │      │  admin-backend (FastAPI)     │
│  (Telegram 機器人)   │      │  Port: 8000                 │
│                      │      │  - RESTful API               │
│  - 消息處理          │      │  - 數據聚合                  │
│  - AI 回復           │      │  - 認證授權                 │
│  - 語音處理          │      │  - 數據庫管理               │
│  - 後台任務          │      └──────────┬───────────────────┘
└──────────┬───────────┘                  │
           │                               │
           │                               │
           ├───────────────────────────────┤
           │                               │
           ▼                               ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│  utils/              │      │  session_service              │
│  - business_ai.py    │      │  Port: 8001                   │
│  - speech_to_text.py │      │  - 會話池管理                 │
│  - tts_voice.py      │      │  - 會話分發                   │
│  - db_manager.py     │      │  - 會話操作                   │
│  - excel_manager.py  │      └──────────────────────────────┘
└──────────┬───────────┘
           │
           │
           ▼
┌──────────────────────┐
│  外部服務            │
├──────────────────────┤
│  - OpenAI API        │
│  - 騰訊雲 TTS        │
│  - Telegram API      │
└──────────────────────┘
           │
           │
           ▼
┌──────────────────────┐
│  數據存儲層          │
├──────────────────────┤
│  - admin.db          │
│    (SQLite/PostgreSQL)│
│  - chat_history.db   │
│    (SQLite)          │
│  - friends.xlsx      │
│    (Excel)           │
│  - Redis             │
│    (緩存/隊列)       │
└──────────────────────┘
```

### 前端架構圖（saas-demo）

```
┌─────────────────────────────────────────────────────────┐
│                    saas-demo (Next.js)                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   page.tsx   │  │ sessions/    │  │ logs/        │  │
│  │  (Dashboard) │  │ page.tsx     │  │ page.tsx     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │          │
│         └─────────────────┴─────────────────┘          │
│                        │                                │
│                        ▼                                │
│              ┌─────────────────┐                        │
│              │  React Hooks   │                        │
│              │  - useDashboard │                        │
│              │  - useSessions │                        │
│              │  - useLogs     │                        │
│              └────────┬────────┘                       │
│                       │                                 │
│                       ▼                                 │
│              ┌─────────────────┐                       │
│              │  api-client.ts  │                       │
│              │  - 統一客戶端   │                       │
│              │  - 超時處理     │                       │
│              │  - Mock Fallback│                       │
│              │  - 錯誤處理    │                       │
│              └────────┬────────┘                       │
│                       │                                 │
│                       │ HTTP Request                    │
│                       │                                 │
└───────────────────────┼─────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  admin-backend  │
              │  (FastAPI)      │
              │  Port: 8000     │
              └─────────────────┘
```

### 後端架構圖（admin-backend）

```
┌─────────────────────────────────────────────────────────┐
│              admin-backend (FastAPI)                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │  app/api/routes.py                               │   │
│  │  - /api/v1/dashboard                              │   │
│  │  - /api/v1/sessions                               │   │
│  │  - /api/v1/logs                                   │   │
│  │  - /api/v1/metrics                               │   │
│  │  - /api/v1/system/monitor                         │   │
│  │  - /api/v1/settings/alerts                        │   │
│  └──────────────┬────────────────────────────────────┘   │
│                 │                                         │
│                 ▼                                         │
│  ┌───────────────────────────────────────────────────┐   │
│  │  app/services/data_sources.py                     │   │
│  │  - get_dashboard_stats()                          │   │
│  │  - get_sessions()                                 │   │
│  │  - get_logs()                                      │   │
│  │  - get_metrics()                                  │   │
│  │  - get_system_monitor()                           │   │
│  │  - Mock Fallback                                  │   │
│  └──────────────┬────────────────────────────────────┘   │
│                 │                                         │
│                 ├─────────────────┬───────────────────┐   │
│                 │                 │                   │   │
│                 ▼                 ▼                   ▼   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  session_     │  │  redpacket_ │  │  admin.db    │   │
│  │  service      │  │  service    │  │  (SQLite/    │   │
│  │  (Port 8001)  │  │  (Port 8002)│  │  PostgreSQL) │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### 主程序架構圖（main.py）

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (Telegram 機器人)              │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │  Pyrogram Client                                  │   │
│  │  - 接收消息                                       │   │
│  │  - 發送消息                                       │   │
│  └──────────────┬────────────────────────────────────┘   │
│                 │                                         │
│                 ▼                                         │
│  ┌───────────────────────────────────────────────────┐   │
│  │  消息處理器                                       │   │
│  │  - 文本消息                                       │   │
│  │  - 語音消息                                       │   │
│  │  - 圖片消息                                       │   │
│  │  - 視頻消息                                       │   │
│  └──────────────┬────────────────────────────────────┘   │
│                 │                                         │
│                 ├─────────────────┬───────────────────┐   │
│                 │                 │                   │   │
│                 ▼                 ▼                   ▼   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  business_   │  │  speech_to_ │  │  analyze_    │   │
│  │  ai.py       │  │  text.py    │  │  image_      │   │
│  │  (AI回復)    │  │  (STT)      │  │  message()   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │          │
│         └─────────────────┴─────────────────┘          │
│                        │                                │
│                        ▼                                │
│              ┌─────────────────┐                        │
│              │  OpenAI API     │                        │
│              └─────────────────┘                        │
│                                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │  BackgroundTaskManager                           │   │
│  │  - 自動問候新好友                                │   │
│  │  - 批量問候和回復                                │   │
│  │  - 標籤分析                                      │   │
│  │  - 自動備份                                      │   │
│  └───────────────────────────────────────────────────┘   │
│                                                           │
└───────────────────────────────────────────────────────────┘
           │
           │
           ▼
┌──────────────────────┐
│  數據存儲            │
├──────────────────────┤
│  - chat_history.db   │
│  - friends.xlsx     │
│  - logs/            │
└──────────────────────┘
```

---

## 總結

本系統採用**分層架構、模塊化設計**，實現了：

1. **前後端分離**：前端（Next.js、React）與後端（FastAPI）完全分離，通過 RESTful API 通信
2. **容錯機制**：多層錯誤處理，Mock 數據 Fallback，確保系統穩定性
3. **可擴展性**：模塊化設計，易於添加新功能
4. **可觀測性**：完整的日誌、監控、告警機制
5. **外部服務集成**：支持 Telegram、OpenAI、騰訊雲等多種外部服務

系統架構清晰，職責分明，易於維護和擴展。

---

**最後更新**: 2024-12-19  
**文檔維護**: 請根據實際代碼變更及時更新本文檔

