# Telegram 群組多 AI 賬號智能管理系統 - 完整開發計劃

> **文檔版本**: v1.0  
> **創建日期**: 2024-12-19  
> **項目代號**: Group AI Management System (GAMS)

---

## 目錄

1. [項目概述](#項目概述)
2. [功能模塊劃分](#功能模塊劃分)
3. [技術選型](#技術選型)
4. [開發時間節點](#開發時間節點)
5. [測試計劃](#測試計劃)
6. [交付標準](#交付標準)
7. [自動化開發流程](#自動化開發流程)
8. [實施執行](#實施執行)

---

## 項目概述

### 1.1 項目目標

設計並實現一個**高效、穩定、可擴展**的 Telegram 群組多 AI 賬號智能管理系統，支持：

- **1-100 個 AI 賬號**並行運行
- **批量導入** `.session` 文件，動態管理賬號
- **劇本驅動**的自動對話系統
- **上下文感知**的智能話術調整
- **紅包遊戲**自動參與
- **實時監控**和行為調控

### 1.2 核心價值

- **規模化運營**: 支持大規模 AI 賬號矩陣運營
- **智能化互動**: 基於劇本和 AI 的自然對話
- **自動化參與**: 紅包遊戲等群組活動自動參與
- **可觀測性**: 完整的監控和調控能力

---

## 功能模塊劃分

### 2.1 模塊架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Web 管理界面層                            │
│  (saas-demo: 賬號管理、劇本配置、監控儀表板、調控面板)      │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    API 服務層                                │
│  (admin-backend: RESTful API)                               │
│  - /api/v1/group-ai/accounts (賬號管理)                      │
│  - /api/v1/group-ai/scripts (劇本管理)                      │
│  - /api/v1/group-ai/monitor (監控數據)                      │
│  - /api/v1/group-ai/control (行為調控)                      │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   核心服務層                                 │
├─────────────────────────────────────────────────────────────┤
│  Module 1: AccountManager (賬號管理器)                       │
│  ├─ 批量加載 .session 文件                                   │
│  ├─ 動態添加/移除賬號                                        │
│  ├─ 賬號生命週期管理                                         │
│  └─ 異常處理和重連                                           │
│                                                              │
│  Module 2: ScriptEngine (劇本引擎)                           │
│  ├─ YAML 劇本解析                                            │
│  ├─ 場景狀態機                                                │
│  ├─ 變量替換和動態內容                                       │
│  └─ 劇本版本管理                                             │
│                                                              │
│  Module 3: DialogueManager (對話管理器)                      │
│  ├─ 消息語義理解                                              │
│  ├─ 上下文管理                                                │
│  ├─ AI 回復生成                                              │
│  └─ 自然度優化                                               │
│                                                              │
│  Module 4: RedpacketHandler (紅包處理器)                     │
│  ├─ 紅包消息檢測                                              │
│  ├─ 參與策略評估                                              │
│  ├─ 搶紅包執行                                                │
│  └─ 結果記錄和統計                                           │
│                                                              │
│  Module 5: MonitorService (監控服務)                         │
│  ├─ 指標收集                                                  │
│  ├─ 實時監控                                                  │
│  ├─ 告警機制                                                  │
│  └─ 數據可視化                                                │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   會話池層                                    │
│  SessionPool (擴展現有 session_service)                     │
│  ├─ SessionClient 1 (Pyrogram)                               │
│  ├─ SessionClient 2 (Pyrogram)                                │
│  ├─ ...                                                      │
│  └─ SessionClient N (N ≤ 100)                                │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   Telegram API                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模塊詳細說明

#### 模塊 1: AccountManager（賬號管理器）

**職責**:
- 批量加載和管理 `.session` 文件
- 動態添加/移除賬號
- 賬號狀態管理（啟動、停止、重啟）
- 異常處理和自動重連

**核心接口**:
```python
class AccountManager:
    async def load_accounts_from_sessions(session_files: List[str]) -> List[str]
    async def add_account(account_id: str, session_file: str, config: AccountConfig) -> AccountInstance
    async def remove_account(account_id: str) -> bool
    async def start_account(account_id: str) -> bool
    async def stop_account(account_id: str) -> bool
    def get_account_status(account_id: str) -> AccountStatus
    def list_accounts() -> List[AccountInfo]
```

**依賴**:
- `session_service/session_pool.py` (擴展)
- `tools/session_manager/` (會話管理工具)

#### 模塊 2: ScriptEngine（劇本引擎）

**職責**:
- 解析 YAML 格式的對話劇本
- 執行場景狀態機
- 處理條件分支和變量替換
- 劇本版本管理

**劇本格式**:
- YAML 格式，支持場景、觸發條件、回復模板、狀態轉換
- 變量替換：`{{variable_name}}`
- AI 生成標記：`ai_generate: true`

**核心接口**:
```python
class ScriptEngine:
    def load_script(script_id: str, script_path: str) -> Script
    async def process_message(account_id: str, message: Message, context: DialogueContext) -> Optional[Response]
    def get_current_scene(account_id: str) -> str
    def transition_scene(account_id: str, scene_id: str) -> bool
```

**依賴**:
- `pyyaml` (YAML 解析)
- `ai_models/` (劇本存儲)

#### 模塊 3: DialogueManager（對話管理器）

**職責**:
- 理解用戶消息語義
- 管理多輪對話上下文
- 生成上下文相關的回復
- 優化回復自然度

**核心接口**:
```python
class DialogueManager:
    async def understand_message(message: Message, context: DialogueContext) -> MessageIntent
    async def generate_reply(account_id: str, message: Message, script: Script, context: DialogueContext) -> str
    def update_context(account_id: str, message: Message, reply: str)
    def should_reply(account_id: str, message: Message, context: DialogueContext) -> bool
```

**依賴**:
- `utils/business_ai.py` (AI 生成)
- `utils/prompt_manager.py` (提示詞管理)
- OpenAI API

#### 模塊 4: RedpacketHandler（紅包處理器）

**職責**:
- 檢測群內紅包消息
- 評估參與策略
- 執行搶紅包操作
- 記錄和統計結果

**核心接口**:
```python
class RedpacketHandler:
    async def detect_redpacket(message: Message) -> Optional[RedpacketInfo]
    async def should_participate(account_id: str, redpacket: RedpacketInfo, context: DialogueContext) -> bool
    async def participate(account_id: str, redpacket: RedpacketInfo) -> RedpacketResult
    def get_statistics(account_id: str, time_range: TimeRange) -> RedpacketStats
```

**依賴**:
- `session_service/redpacket.py` (現有紅包功能)
- Pyrogram API

#### 模塊 5: MonitorService（監控服務）

**職責**:
- 收集賬號運行指標
- 實時監控系統狀態
- 觸發告警
- 生成監控報告

**核心接口**:
```python
class MonitorService:
    def record_message(account_id: str, message_type: str, success: bool)
    def record_reply(account_id: str, reply_time: float, success: bool)
    def record_redpacket(account_id: str, result: RedpacketResult)
    def get_account_metrics(account_id: str, time_range: TimeRange) -> AccountMetrics
    def get_system_metrics(time_range: TimeRange) -> SystemMetrics
    def check_alerts() -> List[Alert]
```

**依賴**:
- 數據庫（指標存儲）
- Prometheus (可選)

---

## 技術選型

### 3.1 後端技術棧

| 組件 | 技術選型 | 版本 | 說明 |
|------|---------|------|------|
| 編程語言 | Python | 3.11+ | 主要開發語言 |
| Web 框架 | FastAPI | 0.115+ | RESTful API 服務 |
| Telegram 客戶端 | Pyrogram | 2.0+ | Telegram API 封裝 |
| AI 服務 | OpenAI API | - | GPT-4, GPT-4o-mini |
| 數據庫 | PostgreSQL / SQLite | - | 主數據庫 |
| ORM | SQLAlchemy | 2.0+ | 數據庫 ORM |
| 數據遷移 | Alembic | 1.13+ | 數據庫遷移工具 |
| 配置管理 | Pydantic Settings | 2.4+ | 配置驗證 |
| 異步框架 | asyncio | 內置 | 異步處理 |
| 日誌 | logging | 內置 | 日誌系統 |
| YAML 解析 | PyYAML | 6.0+ | 劇本解析 |

### 3.2 前端技術棧

| 組件 | 技術選型 | 版本 | 說明 |
|------|---------|------|------|
| 前端框架 | Next.js | 16+ | React 框架 |
| 樣式 | Tailwind CSS | 3.4+ | CSS 框架 |
| UI 組件 | shadcn/ui | - | 組件庫 |
| 狀態管理 | React Hooks | - | 狀態管理 |
| 類型檢查 | TypeScript | 5+ | 類型安全 |
| API 客戶端 | fetch / axios | - | HTTP 請求 |

### 3.3 開發工具

| 工具 | 用途 | 說明 |
|------|------|------|
| Poetry | Python 依賴管理 | 後端依賴管理 |
| npm/yarn | Node.js 包管理 | 前端依賴管理 |
| pytest | Python 測試 | 單元測試、集成測試 |
| Playwright | E2E 測試 | 前端 E2E 測試 |
| Docker | 容器化 | 部署容器化 |
| GitHub Actions | CI/CD | 自動化流程 |

### 3.4 監控與運維

| 工具 | 用途 | 說明 |
|------|------|------|
| Prometheus | 指標收集 | 可選 |
| Grafana | 數據可視化 | 可選 |
| Redis | 緩存/隊列 | 可選 |
| Nginx | 反向代理 | 生產環境 |

---

## 開發時間節點

### 4.1 總體時間線

| 階段 | 時間 | 主要交付物 | 狀態 |
|------|------|-----------|------|
| 階段 1: 基礎架構搭建 | Week 1-2 | 賬號管理模塊、數據庫設計 | 🔄 待開始 |
| 階段 2: 劇本引擎開發 | Week 3-4 | 劇本解析和執行引擎 | ⏳ 未開始 |
| 階段 3: 智能對話系統 | Week 5-6 | 對話管理器和 AI 生成 | ⏳ 未開始 |
| 階段 4: 紅包遊戲功能 | Week 7 | 紅包檢測和參與 | ⏳ 未開始 |
| 階段 5: 監控與調控系統 | Week 8 | 監控服務和 Web 界面 | ⏳ 未開始 |
| 階段 6: 測試與優化 | Week 9-10 | 測試報告和優化 | ⏳ 未開始 |

**總計**: 10 週（約 2.5 個月）

### 4.2 詳細時間節點

#### 階段 1: 基礎架構搭建 (Week 1-2, 14.5 天)

| 任務 | 時間 | 交付物 |
|------|------|--------|
| 1.1 創建模塊結構 | 0.5 天 | 目錄結構 |
| 1.2 數據模型設計 | 1 天 | `models/account.py` |
| 1.3 批量加載功能 | 2 天 | `account_manager.py` (部分) |
| 1.4 動態管理功能 | 3 天 | `account_manager.py` (完整) |
| 1.5 會話池擴展 | 3 天 | `session_pool.py` (擴展) |
| 1.6 數據庫設計與遷移 | 2 天 | 數據庫模型和遷移 |

**里程碑 M1**: Week 2 結束 - 基礎架構完成

#### 階段 2: 劇本引擎開發 (Week 3-4, 17 天)

| 任務 | 時間 | 交付物 |
|------|------|--------|
| 2.1 劇本格式與解析器 | 3 天 | `script_parser.py` |
| 2.2 場景狀態機 | 4 天 | `script_engine.py` (狀態機) |
| 2.3 變量替換 | 3 天 | `variable_resolver.py` |
| 2.4 劇本執行引擎 | 4 天 | `script_engine.py` (完整) |
| 2.5 劇本管理 API | 3 天 | `api/group_ai/scripts.py` |

**里程碑 M2**: Week 4 結束 - 劇本引擎完成

#### 階段 3: 智能對話系統 (Week 5-6, 14 天)

| 任務 | 時間 | 交付物 |
|------|------|--------|
| 3.1 消息理解模塊 | 4 天 | `message_analyzer.py` |
| 3.2 上下文管理 | 3 天 | `context_manager.py` |
| 3.3 AI 回復生成 | 4 天 | `ai_generator.py` |
| 3.4 自然度優化 | 3 天 | `naturalness_optimizer.py` |

**里程碑 M3**: Week 6 結束 - 智能對話完成

#### 階段 4: 紅包遊戲功能 (Week 7, 7 天)

| 任務 | 時間 | 交付物 |
|------|------|--------|
| 4.1 紅包檢測 | 2 天 | `redpacket_handler.py` (檢測) |
| 4.2 參與策略 | 3 天 | `redpacket_strategies.py` |
| 4.3 執行與記錄 | 2 天 | `redpacket_handler.py` (完整) |

**里程碑 M4**: Week 7 結束 - 紅包功能完成

#### 階段 5: 監控與調控系統 (Week 8, 14 天)

| 任務 | 時間 | 交付物 |
|------|------|--------|
| 5.1 監控服務 | 4 天 | `monitor_service.py` |
| 5.2 監控 API | 3 天 | `api/group_ai/monitor.py` |
| 5.3 調控接口 | 2 天 | `api/group_ai/control.py` |
| 5.4 Web 管理界面 | 5 天 | `saas-demo/src/app/group-ai/` |

**里程碑 M5**: Week 8 結束 - 監控系統完成

#### 階段 6: 測試與優化 (Week 9-10, 17 天)

| 任務 | 時間 | 交付物 |
|------|------|--------|
| 6.1 單元測試 | 5 天 | 測試文件和覆蓋率報告 |
| 6.2 集成測試 | 4 天 | 集成測試套件 |
| 6.3 性能測試 | 5 天 | 性能測試報告 |
| 6.4 用戶體驗測試 | 3 天 | 評估報告 |

**里程碑 M6**: Week 10 結束 - 測試完成，系統上線

---

## 測試計劃

### 5.1 測試策略

#### 單元測試

**目標覆蓋率**: 80%+

**測試範圍**:
- 所有核心模塊的函數和類
- 數據模型驗證
- 工具函數

**工具**: `pytest`, `pytest-cov`

**執行命令**:
```bash
cd group_ai_service
pytest tests/unit/ -v --cov=. --cov-report=html
```

#### 集成測試

**測試範圍**:
- 模塊間交互
- API 端點功能
- 數據庫操作
- 外部服務集成

**工具**: `pytest`, `httpx` (API 測試)

**執行命令**:
```bash
pytest tests/integration/ -v
```

#### 端到端測試

**測試範圍**:
- 完整用戶流程
- 多賬號並行場景
- 劇本執行流程
- 紅包參與流程

**工具**: `pytest`, `asyncio`

**執行命令**:
```bash
pytest tests/e2e/ -v
```

#### 性能測試

**測試場景**:
- 10 賬號並行
- 50 賬號並行
- 100 賬號並行
- 高頻消息壓力測試
- 長時間運行測試（24h+）

**工具**: `pytest-benchmark`, 自定義性能測試腳本

**執行命令**:
```bash
pytest tests/performance/ -v --benchmark-only
```

### 5.2 測試環境

| 環境 | 用途 | 配置 |
|------|------|------|
| 開發環境 | 日常開發測試 | 1-5 個測試賬號 |
| 測試環境 | 集成測試 | 10-20 個測試賬號 |
| 預生產環境 | 性能測試 | 50-100 個測試賬號 |
| 生產環境 | 正式運行 | 實際賬號數量 |

### 5.3 測試數據

- **測試賬號**: 使用測試 Telegram 賬號
- **測試群組**: 創建專用測試群組
- **測試劇本**: 提供標準測試劇本
- **Mock 數據**: 使用 Mock 數據進行離線測試

---

## 交付標準

### 6.1 代碼質量標準

#### 代碼規範

- **Python**: 遵循 PEP 8，使用 `black` 格式化，`ruff` 檢查
- **TypeScript**: 遵循 ESLint 規則，使用 `prettier` 格式化
- **文檔**: 所有公共函數和類必須有文檔字符串

#### 測試覆蓋率

- **單元測試**: ≥ 80%
- **集成測試**: 所有核心流程必須有測試
- **E2E 測試**: 關鍵用戶流程必須有測試

#### 性能標準

| 指標 | 目標值 | 測試方法 |
|------|--------|---------|
| 單個消息處理延遲 | < 2 秒 | 性能測試 |
| 系統響應時間 | < 500ms | API 測試 |
| 100 賬號並行 CPU | < 80% | 壓力測試 |
| 100 賬號並行內存 | < 70% | 壓力測試 |

### 6.2 文檔交付標準

#### 必須交付的文檔

- [ ] 系統設計文檔（已完成）
- [ ] API 文檔（Swagger/OpenAPI）
- [ ] 數據庫設計文檔
- [ ] 部署文檔
- [ ] 用戶手冊（管理界面使用）
- [ ] 開發者指南
- [ ] 測試報告

#### 文檔格式

- Markdown 格式
- 包含清晰的目錄結構
- 代碼示例和圖表
- 版本控制

### 6.3 功能交付標準

#### 必須實現的功能

- [ ] 支持 1-100 個賬號並行運行
- [ ] 批量導入 `.session` 文件
- [ ] 動態添加/移除賬號
- [ ] 劇本驅動的自動對話
- [ ] 上下文感知的智能回復
- [ ] 紅包遊戲自動參與
- [ ] 實時監控和告警
- [ ] Web 管理界面

#### 功能驗收標準

- 所有功能通過單元測試
- 所有功能通過集成測試
- 關鍵功能通過 E2E 測試
- 性能測試達到目標值
- 用戶體驗測試通過

---

## 自動化開發流程

### 7.1 CI/CD 流程設計

#### 持續集成 (CI)

**觸發條件**:
- Push 到主分支
- Pull Request
- 手動觸發

**CI 流程**:
```
1. 代碼檢查
   ├─ Linting (ruff, eslint)
   ├─ 類型檢查 (mypy, tsc)
   └─ 代碼格式化檢查

2. 單元測試
   ├─ 後端單元測試 (pytest)
   ├─ 前端單元測試 (vitest)
   └─ 生成覆蓋率報告

3. 集成測試
   ├─ API 集成測試
   └─ 數據庫集成測試

4. 構建驗證
   ├─ Docker 鏡像構建
   └─ 前端構建驗證
```

#### 持續部署 (CD)

**部署環境**:
- 開發環境: 自動部署
- 測試環境: PR 合併後自動部署
- 生產環境: 手動觸發部署

**CD 流程**:
```
1. 構建 Docker 鏡像
2. 運行測試
3. 部署到目標環境
4. 健康檢查
5. 回滾機制（如果失敗）
```

### 7.2 自動化工具配置

#### GitHub Actions Workflow

**文件**: `.github/workflows/group-ai-ci.yml`

**Jobs**:
1. **Lint & Format Check**: 代碼檢查
2. **Unit Tests**: 單元測試
3. **Integration Tests**: 集成測試
4. **Build**: Docker 構建
5. **Deploy (Dev)**: 自動部署到開發環境

#### 自動化腳本

**文件**: `scripts/automation/`

- `scripts/automation/run_tests.sh` - 運行所有測試
- `scripts/automation/check_code_quality.sh` - 代碼質量檢查
- `scripts/automation/generate_docs.sh` - 生成文檔
- `scripts/automation/deploy.sh` - 部署腳本

### 7.3 開發環境自動化

#### 環境初始化腳本

**文件**: `scripts/setup_dev_env.sh`

**功能**:
- 創建虛擬環境
- 安裝依賴
- 初始化數據庫
- 加載測試數據
- 啟動開發服務

#### 數據庫遷移自動化

**文件**: `scripts/automation/migrate_db.sh`

**功能**:
- 自動檢測待遷移
- 執行遷移
- 驗證遷移結果
- 回滾機制

---

## 實施執行

### 8.1 階段 1 執行計劃

**當前階段**: 階段 1 - 基礎架構搭建

**立即執行任務**:
1. 創建 `group_ai_service/` 目錄結構
2. 設計數據模型
3. 實現賬號管理基礎功能
4. 擴展會話池

**執行方式**: 自動化腳本 + 手動開發

### 8.2 自動化執行流程

**每日自動執行**:
1. 代碼質量檢查
2. 單元測試
3. 構建驗證
4. 部署到開發環境

**每週自動執行**:
1. 完整測試套件
2. 性能基準測試
3. 文檔生成
4. 代碼覆蓋率報告

---

**文檔版本**: v1.0  
**最後更新**: 2024-12-19  
**維護者**: 開發團隊

