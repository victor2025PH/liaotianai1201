# 項目結構文檔

本文檔基於實際項目文件結構生成，僅包含源代碼和配置文件。

> **已排除的目錄和文件**：
> - `.git`, `.idea`, `.vscode`, `.pytest_cache`, `.mypy_cache`, `__pycache__`
> - `venv`, `.venv`, `env`, `node_modules`, `dist`, `build`, `.next`
> - `*.sqlite`, `*.session`, `*.log`, `logs/*`, `backup/*`, `downloads/*`, `photos/*`, `voices/*`

---

## 目錄樹結構

```
聊天AI08-继续开发/
├─ admin-backend/                    # FastAPI 後端管理系統，提供 RESTful API
│  ├─ app/                           # 應用主目錄
│  │  ├─ main.py                     # FastAPI 應用入口（端口 8000）
│  │  ├─ db.py                       # 數據庫連接和 ORM 配置
│  │  ├─ api/                        # API 路由模塊
│  │  │  ├─ routes.py                # 主要 API 路由定義（Dashboard、Sessions、Logs、Metrics、Settings、System Monitor）
│  │  │  ├─ auth.py                  # 認證相關路由（登錄、Token）
│  │  │  ├─ users.py                 # 用戶管理路由
│  │  │  └─ deps.py                  # 依賴注入（認證、數據庫會話等）
│  │  ├─ core/                       # 核心配置模塊
│  │  │  ├─ config.py                # 應用配置（環境變量、數據庫連接等）
│  │  │  └─ security.py             # 安全相關（JWT、密碼哈希）
│  │  ├─ models/                     # SQLAlchemy ORM 數據模型
│  │  │  ├─ user.py                  # 用戶模型
│  │  │  ├─ role.py                  # 角色模型
│  │  │  ├─ permission.py            # 權限模型
│  │  │  ├─ user_role.py             # 用戶-角色關聯表
│  │  │  └─ role_permission.py      # 角色-權限關聯表
│  │  ├─ schemas/                    # Pydantic 數據驗證模型
│  │  │  ├─ dashboard.py             # Dashboard 數據結構
│  │  │  ├─ session.py               # 會話數據結構
│  │  │  ├─ log.py                   # 日誌數據結構
│  │  │  ├─ metrics.py               # 指標數據結構
│  │  │  ├─ settings.py              # 設置數據結構
│  │  │  ├─ system.py                # 系統監控數據結構
│  │  │  ├─ user.py                  # 用戶數據結構
│  │  │  ├─ auth.py                  # 認證數據結構
│  │  │  ├─ account.py               # 賬戶數據結構
│  │  │  ├─ activity.py              # 活動數據結構
│  │  │  ├─ alert.py                 # 告警數據結構
│  │  │  └─ command.py               # 命令數據結構
│  │  ├─ services/                   # 業務邏輯層
│  │  │  └─ data_sources.py         # 數據源服務（對接外部 API、生成 Mock 數據）
│  │  ├─ crud/                        # 數據庫 CRUD 操作
│  │  │  ├─ user.py                  # 用戶 CRUD
│  │  │  └─ role.py                  # 角色 CRUD
│  │  └─ monitoring/                 # 監控相關（Prometheus 指標）
│  ├─ tests/                         # 測試文件
│  │  ├─ conftest.py                 # Pytest 配置和 Fixtures
│  │  └─ test_api.py                 # API 端點測試
│  ├─ pyproject.toml                 # Poetry 依賴管理配置
│  ├─ poetry.lock                    # Poetry 鎖定文件
│  ├─ Dockerfile                     # Docker 構建文件
│  ├─ docker-compose.yml             # Docker Compose 配置
│  ├─ prometheus.yml                 # Prometheus 監控配置
│  └─ README.md                      # 後端項目說明文檔
│
├─ admin-frontend/                   # React + Vite + Ant Design 前端管理系統
│  ├─ src/                           # 源代碼目錄
│  │  ├─ main.tsx                    # 應用入口文件（Vite）
│  │  ├─ App.tsx                     # React 根組件
│  │  ├─ pages/                      # 頁面組件
│  │  │  ├─ Dashboard.tsx            # 儀表板頁面
│  │  │  ├─ Accounts.tsx             # 賬戶管理頁面
│  │  │  ├─ Activities.tsx          # 活動記錄頁面
│  │  │  ├─ Alerts.tsx               # 告警管理頁面
│  │  │  ├─ Commands.tsx             # 命令管理頁面
│  │  │  └─ Settings.tsx             # 設置頁面
│  │  ├─ services/                   # API 服務
│  │  │  └─ api.ts                   # API 封裝（axios）
│  │  ├─ types/                      # TypeScript 類型定義
│  │  │  └─ api.ts                   # API 類型定義
│  │  └─ styles/                     # 樣式文件
│  │     ├─ index.css                # 全局樣式
│  │     └─ app.css                  # 應用樣式
│  ├─ tests/                         # 測試文件
│  │  └─ e2e/                        # E2E 測試
│  │     └─ dashboard.spec.ts        # Dashboard E2E 測試
│  ├─ package.json                   # npm 依賴配置
│  ├─ vite.config.ts                 # Vite 構建配置
│  ├─ tsconfig.json                  # TypeScript 配置
│  ├─ tsconfig.node.json             # TypeScript Node 配置
│  ├─ playwright.config.ts           # Playwright 測試配置
│  ├─ eslint.config.js               # ESLint 配置
│  ├─ Dockerfile                     # Docker 構建文件
│  ├─ docker-compose.yml             # Docker Compose 配置
│  └─ README.md                      # 前端項目說明文檔
│
├─ saas-demo/                        # Next.js + Tailwind + shadcn/ui 前端控制台
│  ├─ src/                           # 源代碼目錄
│  │  ├─ app/                        # Next.js App Router 頁面目錄
│  │  │  ├─ layout.tsx              # 根布局組件
│  │  │  ├─ page.tsx                # Dashboard 首頁（/）
│  │  │  ├─ globals.css             # 全局樣式
│  │  │  ├─ sessions/               # 會話相關頁面
│  │  │  │  ├─ page.tsx            # 會話列表頁面（/sessions）
│  │  │  │  └─ [id]/               # 會話詳情頁面（動態路由）
│  │  │  │     └─ page.tsx
│  │  │  ├─ logs/                   # 日誌中心
│  │  │  │  └─ page.tsx            # 日誌列表頁面（/logs）
│  │  │  ├─ monitoring/             # 系統監控
│  │  │  │  └─ page.tsx            # 系統監控頁面（/monitoring）
│  │  │  ├─ settings/               # 設置頁面
│  │  │  │  └─ alerts/             # 告警設置
│  │  │  │     └─ page.tsx        # 告警設置頁面（/settings/alerts）
│  │  │  └─ demo/                  # Demo 頁面
│  │  │     └─ page.tsx
│  │  ├─ components/                # React 組件
│  │  │  ├─ dashboard/             # Dashboard 專用組件
│  │  │  │  ├─ response-time-chart.tsx  # 響應時間趨勢圖表
│  │  │  │  └─ system-status.tsx        # 系統狀態卡片
│  │  │  ├─ ui/                    # shadcn/ui 基礎組件庫
│  │  │  │  ├─ button.tsx
│  │  │  │  ├─ card.tsx
│  │  │  │  ├─ table.tsx
│  │  │  │  ├─ dialog.tsx
│  │  │  │  ├─ input.tsx
│  │  │  │  ├─ select.tsx
│  │  │  │  ├─ badge.tsx
│  │  │  │  ├─ skeleton.tsx
│  │  │  │  ├─ alert.tsx
│  │  │  │  ├─ progress.tsx
│  │  │  │  └─ ...                  # 其他 UI 組件
│  │  │  ├─ sidebar.tsx            # 側邊欄導航組件
│  │  │  ├─ header.tsx             # 頁面頭部組件
│  │  │  ├─ theme-toggle.tsx       # 主題切換組件
│  │  │  └─ error-boundary.tsx     # 錯誤邊界組件
│  │  ├─ hooks/                    # React Hooks
│  │  │  ├─ useDashboardData.ts    # Dashboard 數據獲取 Hook
│  │  │  ├─ useSessions.ts         # 會話列表 Hook
│  │  │  ├─ useSessionsWithFilters.ts  # 帶過濾的會話列表 Hook
│  │  │  ├─ useSessionDetail.ts    # 會話詳情 Hook
│  │  │  ├─ useLogs.ts             # 日誌列表 Hook
│  │  │  ├─ useMetrics.ts          # 指標數據 Hook
│  │  │  ├─ useRealtimeMetrics.ts  # 實時指標 Hook（輪詢）
│  │  │  ├─ useSystemMonitor.ts    # 系統監控 Hook
│  │  │  ├─ useSSE.ts               # Server-Sent Events Hook（預留）
│  │  │  └─ use-toast.ts            # Toast 通知 Hook
│  │  ├─ lib/                      # 工具函數和 API 封裝
│  │  │  ├─ api.ts                 # API 函數定義（類型定義、API 調用函數）
│  │  │  ├─ api-client.ts          # 統一 API 客戶端（超時處理、Mock Fallback、錯誤處理）
│  │  │  └─ utils.ts               # 工具函數（cn、clsx 等）
│  │  └─ mock/                     # Mock 數據
│  │     ├─ sessions.ts            # 會話 Mock 數據
│  │     ├─ logs.ts                # 日誌 Mock 數據
│  │     └─ stats.ts               # 系統監控 Mock 數據
│  ├─ public/                      # 靜態資源目錄
│  ├─ package.json                 # npm 依賴配置
│  ├─ next.config.ts               # Next.js 構建配置
│  ├─ tailwind.config.ts           # Tailwind CSS 配置
│  ├─ tsconfig.json                # TypeScript 配置
│  ├─ components.json              # shadcn/ui 組件配置
│  ├─ postcss.config.mjs           # PostCSS 配置
│  ├─ eslint.config.mjs            # ESLint 配置
│  ├─ README.md                    # 項目說明文檔
│  ├─ QUICK_START.md               # 快速啟動指南
│  └─ DEVELOPMENT.md              # 開發文檔
│
├─ session_service/                # 會話服務模塊（Telegram 會話管理）
│  ├─ __init__.py
│  ├─ session_pool.py             # 會話池管理
│  ├─ dispatch.py                 # 會話分發邏輯
│  ├─ actions.py                  # 會話操作
│  └─ redpacket.py                # 紅包相關功能
│
├─ utils/                          # 工具函數模塊
│  ├─ logger.py                    # 日誌工具
│  ├─ db_manager.py                # 數據庫管理
│  ├─ excel_manager.py             # Excel 文件處理
│  ├─ ai_context_manager.py       # AI 上下文管理
│  ├─ business_ai.py               # 業務 AI 邏輯
│  ├─ speech_to_text.py           # 語音轉文字（STT）
│  ├─ tts_voice.py                # 文字轉語音（TTS）
│  ├─ media_utils.py              # 媒體文件處理
│  ├─ prompt_manager.py           # 提示詞管理
│  ├─ tag_analyzer.py             # 標籤分析
│  ├─ user_utils.py               # 用戶工具
│  ├─ yaml_config.py              # YAML 配置管理
│  ├─ auto_backup.py              # 自動備份
│  ├─ auto_batch_greet_and_reply.py  # 批量問候和回復
│  ├─ friend_auto_add.py          # 自動添加好友
│  ├─ friend_greet.py             # 好友問候
│  ├─ emoji_manager.py            # Emoji 管理
│  └─ async_utils.py              # 異步工具
│
├─ tools/                          # 工具腳本
│  ├─ dialogue_scene_editor.py    # 對話場景編輯器
│  ├─ validate_dialogue_yaml.py   # YAML 驗證工具
│  ├─ voice_script_builder.py     # 語音腳本構建器
│  └─ session_manager/            # 會話管理工具
│
├─ scripts/                        # 腳本目錄
│  ├─ __init__.py
│  ├─ login.py                    # 登錄腳本
│  └─ run_migrations.py           # 數據庫遷移腳本
│
├─ tests/                          # 測試目錄
│  ├─ __init__.py
│  ├─ conftest.py                 # Pytest 配置
│  ├─ test_session_pool.py        # 會話池測試
│  ├─ test_session_dispatch.py    # 會話分發測試
│  ├─ test_session_actions.py     # 會話操作測試
│  └─ test_operations.py           # 操作測試
│
├─ docs/                           # 文檔目錄
│  ├─ 開發文檔.md                  # 主要開發文檔
│  ├─ 開發文檔2號.md               # 開發文檔（更新版）
│  ├─ session_interaction_service.md  # 會話交互服務文檔
│  ├─ session_event_model.md          # 會話事件模型
│  ├─ session_cli_usage.md            # 會話 CLI 使用說明
│  ├─ redpacket_test_plan.md         # 紅包測試計劃
│  ├─ monitoring_and_release.md      # 監控與發布文檔
│  ├─ 安全準則.md                   # 安全準則
│  └─ env.example                   # 環境變量示例
│
├─ deploy/                         # 部署相關
│  ├─ deploy_guide.md              # 部署指南
│  ├─ docker-compose.yaml          # Docker Compose 配置
│  └─ session-service.Dockerfile   # 會話服務 Dockerfile
│
├─ ai_models/                      # AI 模型配置
│  ├─ dialogue_scene_scripts.yaml  # 對話場景腳本
│  └─ intro_segments.yaml          # 介紹片段
│
├─ migrations/                     # 數據庫遷移文件
│  └─ __init__.py
│
├─ main.py                         # Telegram 機器人主程序入口
├─ config.py                       # 主配置文件
├─ requirements.txt                # Python 依賴列表
├─ README.md                       # 項目主文檔
└─ PROJECT_STRUCTURE.md            # 本文件（項目結構文檔）
```

---

## 後端服務入口文件

### 端口 8000 - FastAPI 後端 API 服務

| 文件路徑 | 說明 |
|---------|------|
| `admin-backend/app/main.py` | FastAPI 應用入口，使用 `uvicorn` 運行，默認端口 8000 |

**啟動方式**：
```bash
cd admin-backend
poetry run uvicorn app.main:app --reload --port 8000
```

---

## API 路由文件

### FastAPI 路由定義

| 文件路徑 | 說明 | 主要端點 |
|---------|------|---------|
| `admin-backend/app/api/routes.py` | **主要 API 路由** | `/api/v1/dashboard`, `/api/v1/sessions`, `/api/v1/logs`, `/api/v1/metrics`, `/api/v1/settings/alerts`, `/api/v1/system/monitor` |
| `admin-backend/app/api/auth.py` | 認證相關路由 | `/api/v1/auth/login`, `/api/v1/auth/token` |
| `admin-backend/app/api/users.py` | 用戶管理路由 | `/api/v1/users/*` |

**路由註冊**：
- 所有路由在 `admin-backend/app/api/__init__.py` 中統一註冊
- 在 `admin-backend/app/main.py` 中通過 `app.include_router(api_router, prefix="/api/v1")` 掛載

---

## 前端服務入口文件

### Next.js 前端（端口 3000）

| 文件路徑 | 說明 |
|---------|------|
| `saas-demo/src/app/layout.tsx` | Next.js 根布局組件 |
| `saas-demo/src/app/page.tsx` | Dashboard 首頁（路由：`/`） |

**啟動方式**：
```bash
cd saas-demo
npm run dev
# 默認運行在 http://localhost:3000
```

### Vite + React 前端（端口 5173）

| 文件路徑 | 說明 |
|---------|------|
| `admin-frontend/src/main.tsx` | Vite 應用入口文件 |
| `admin-frontend/src/App.tsx` | React 根組件 |

**啟動方式**：
```bash
cd admin-frontend
npm run dev
# 默認運行在 http://localhost:5173
```

---

## 前端頁面入口文件

### Next.js 頁面（saas-demo）

| 路由路徑 | 文件路徑 | 說明 |
|---------|---------|------|
| `/` | `saas-demo/src/app/page.tsx` | Dashboard 總覽頁面 |
| `/sessions` | `saas-demo/src/app/sessions/page.tsx` | 會話列表頁面 |
| `/sessions/[id]` | `saas-demo/src/app/sessions/[id]/page.tsx` | 會話詳情頁面（動態路由） |
| `/logs` | `saas-demo/src/app/logs/page.tsx` | 日誌中心頁面 |
| `/monitoring` | `saas-demo/src/app/monitoring/page.tsx` | 系統監控頁面 |
| `/settings/alerts` | `saas-demo/src/app/settings/alerts/page.tsx` | 告警設置頁面 |
| `/demo` | `saas-demo/src/app/demo/page.tsx` | Demo 頁面 |

### React 頁面（admin-frontend）

| 路由路徑 | 文件路徑 | 說明 |
|---------|---------|------|
| `/` | `admin-frontend/src/pages/Dashboard.tsx` | 儀表板頁面 |
| `/accounts` | `admin-frontend/src/pages/Accounts.tsx` | 賬戶管理頁面 |
| `/activities` | `admin-frontend/src/pages/Activities.tsx` | 活動記錄頁面 |
| `/alerts` | `admin-frontend/src/pages/Alerts.tsx` | 告警管理頁面 |
| `/commands` | `admin-frontend/src/pages/Commands.tsx` | 命令管理頁面 |
| `/settings` | `admin-frontend/src/pages/Settings.tsx` | 設置頁面 |

---

## 主要配置文件

### 後端配置
- `admin-backend/pyproject.toml` - Poetry 依賴管理
- `admin-backend/app/core/config.py` - 後端應用配置（環境變量、數據庫連接）
- `admin-backend/app/db.py` - 數據庫連接配置

### 前端配置
- `saas-demo/package.json` - Next.js 項目依賴
- `saas-demo/next.config.ts` - Next.js 構建配置
- `saas-demo/tailwind.config.ts` - Tailwind CSS 配置
- `admin-frontend/package.json` - React 項目依賴
- `admin-frontend/vite.config.ts` - Vite 構建配置

### 主程序配置
- `config.py` - Telegram 機器人主配置
- `requirements.txt` - Python 全局依賴

---

## 快速定位

### 查找後端 API 路由
→ `admin-backend/app/api/routes.py`

### 查找前端頁面
→ `saas-demo/src/app/`（Next.js）或 `admin-frontend/src/pages/`（React）

### 查找數據模型
→ `admin-backend/app/models/`（後端 ORM）或 `saas-demo/src/lib/api.ts`（前端類型）

### 查找 API 封裝
→ `saas-demo/src/lib/api-client.ts`（統一 API 客戶端，含 Mock Fallback）

### 查找 Mock 數據
→ `saas-demo/src/mock/` 或 `saas-demo/src/lib/api-client.ts`

### 查找會話服務邏輯
→ `session_service/` 目錄

### 查找工具函數
→ `utils/` 目錄

---

**最後更新**: 2024-12-19  
**生成方式**: 基於實際文件結構掃描
