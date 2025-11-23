# Telegram 群組多 AI 賬號智能管理系統設計方案

> **文檔版本**: v1.0  
> **設計日期**: 2024-12-19  
> **適用範圍**: 1-100 個 AI 賬號並行管理

---

## 目錄

1. [系統概述](#系統概述)
2. [需求分析](#需求分析)
3. [系統架構設計](#系統架構設計)
4. [核心模塊設計](#核心模塊設計)
5. [數據流設計](#數據流設計)
6. [實施計劃](#實施計劃)
7. [技術規格](#技術規格)
8. [監控與調控系統](#監控與調控系統)
9. [測試策略](#測試策略)

---

## 系統概述

### 1.1 系統目標

設計並實現一個**高效、穩定、可擴展**的 Telegram 群組多 AI 賬號智能管理系統，支持：

- **1-100 個 AI 賬號**並行運行
- **批量導入** `.session` 文件，動態管理賬號
- **劇本驅動**的自動對話系統
- **上下文感知**的智能話術調整
- **紅包遊戲**自動參與
- **實時監控**和行為調控

### 1.2 核心特性

| 特性 | 說明 | 優先級 |
|------|------|--------|
| 多賬號並行管理 | 支持 1-100 個賬號同時運行 | P0 |
| 批量會話導入 | 從 `.session` 文件批量加載賬號 | P0 |
| 劇本驅動對話 | 基於預設劇本的智能對話引擎 | P0 |
| 上下文感知 | 多輪對話，上下文關聯 | P0 |
| 紅包遊戲參與 | 自動觸發和響應紅包活動 | P0 |
| 實時監控 | 賬號狀態、互動表現監控 | P1 |
| 行為調控 | 動態調整活躍度、回復頻率 | P1 |
| 會話持久化 | 每個賬號獨立的會話歷史 | P0 |

---

## 需求分析

### 2.1 功能需求

#### FR1: 賬號管理
- **FR1.1**: 支持批量導入 `.session` 文件（1-100 個）
- **FR1.2**: 動態添加/移除賬號，無需重啟系統
- **FR1.3**: 每個賬號獨立的會話狀態和歷史記錄
- **FR1.4**: 賬號健康狀態檢查和自動重連機制

#### FR2: 劇本驅動對話
- **FR2.1**: 支持為每個賬號配置獨立的對話劇本
- **FR2.2**: 劇本支持多場景切換（日常聊天、紅包互動、業務推廣等）
- **FR2.3**: 劇本支持條件分支和狀態機
- **FR2.4**: 劇本支持變量替換和動態內容生成

#### FR3: 智能對話
- **FR3.1**: 理解真實用戶消息的語義
- **FR3.2**: 基於上下文生成自然回復
- **FR3.3**: 支持多輪對話，保持話題連續性
- **FR3.4**: 避免重複回復和無意義互動

#### FR4: 紅包遊戲
- **FR4.1**: 自動檢測群內紅包消息
- **FR4.2**: 根據策略決定是否參與
- **FR4.3**: 模擬真實用戶的搶紅包行為
- **FR4.4**: 記錄紅包參與結果和統計

#### FR5: 監控與調控
- **FR5.1**: 實時監控所有賬號的在線狀態
- **FR5.2**: 統計每個賬號的互動頻率和效果
- **FR5.3**: 提供 Web 界面進行參數調整
- **FR5.4**: 支持批量操作（啟用/禁用、調整參數）

### 2.2 非功能需求

#### NFR1: 性能
- **NFR1.1**: 支持 100 個賬號並行運行，CPU 使用率 < 80%
- **NFR1.2**: 單個消息處理延遲 < 2 秒
- **NFR1.3**: 系統響應時間 < 500ms

#### NFR2: 穩定性
- **NFR2.1**: 單個賬號異常不影響其他賬號
- **NFR2.2**: 自動重連機制，斷線恢復時間 < 30 秒
- **NFR2.3**: 系統可用性 > 99%

#### NFR3: 可擴展性
- **NFR3.1**: 支持動態擴展到 100+ 賬號
- **NFR3.2**: 模塊化設計，易於添加新功能
- **NFR3.3**: 支持分佈式部署

#### NFR4: 安全性
- **NFR4.1**: `.session` 文件加密存儲
- **NFR4.2**: API 接口認證和授權
- **NFR4.3**: 操作日誌記錄和審計

---

## 系統架構設計

### 3.1 整體架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        管理層                                    │
├─────────────────────────────────────────────────────────────────┤
│  Web 管理界面 (saas-demo)                                       │
│  - 賬號管理界面                                                  │
│  - 劇本配置界面                                                  │
│  - 監控儀表板                                                    │
│  - 行為調控面板                                                  │
└──────────────────────┬──────────────────────────────────────────┘
                        │ HTTP API
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API 服務層                                   │
├─────────────────────────────────────────────────────────────────┤
│  admin-backend (FastAPI)                                        │
│  - /api/v1/group-ai/accounts (賬號管理)                          │
│  - /api/v1/group-ai/scripts (劇本管理)                          │
│  - /api/v1/group-ai/monitor (監控數據)                          │
│  - /api/v1/group-ai/control (行為調控)                          │
└──────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      核心服務層                                   │
├─────────────────────────────────────────────────────────────────┤
│  GroupAIService (群組 AI 服務)                                    │
│  ├─ AccountManager (賬號管理器)                                 │
│  ├─ ScriptEngine (劇本引擎)                                     │
│  ├─ DialogueManager (對話管理器)                                │
│  ├─ RedpacketHandler (紅包處理器)                               │
│  └─ MonitorService (監控服務)                                    │
└──────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     會話池層                                     │
├─────────────────────────────────────────────────────────────────┤
│  SessionPool (會話池)                                            │
│  ├─ SessionClient 1 (Pyrogram Client)                            │
│  ├─ SessionClient 2 (Pyrogram Client)                            │
│  ├─ ...                                                          │
│  └─ SessionClient N (Pyrogram Client, N ≤ 100)                   │
└──────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Telegram API                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 模塊劃分

#### 模塊 1: 賬號管理模塊 (AccountManager)

**職責**：
- 批量加載 `.session` 文件
- 管理賬號生命週期（創建、啟動、停止、移除）
- 維護賬號配置和狀態
- 處理賬號異常和重連

**位置**: `group_ai_service/account_manager.py`

#### 模塊 2: 劇本引擎模塊 (ScriptEngine)

**職責**：
- 解析和執行對話劇本
- 管理劇本狀態機
- 處理條件分支和變量替換
- 劇本版本管理

**位置**: `group_ai_service/script_engine.py`

#### 模塊 3: 對話管理器模塊 (DialogueManager)

**職責**：
- 理解用戶消息語義
- 生成上下文相關的回復
- 管理多輪對話歷史
- 避免重複和無意義互動

**位置**: `group_ai_service/dialogue_manager.py`

#### 模塊 4: 紅包處理器模塊 (RedpacketHandler)

**職責**：
- 檢測群內紅包消息
- 決定參與策略
- 執行搶紅包操作
- 記錄參與結果

**位置**: `group_ai_service/redpacket_handler.py`

#### 模塊 5: 監控服務模塊 (MonitorService)

**職責**：
- 收集賬號運行狀態
- 統計互動數據
- 生成監控報告
- 觸發告警

**位置**: `group_ai_service/monitor_service.py`

---

## 核心模塊設計

### 4.1 賬號管理模塊 (AccountManager)

#### 4.1.1 類設計

```python
class AccountManager:
    """賬號管理器"""
    
    def __init__(self):
        self.accounts: Dict[str, AccountInstance] = {}
        self.session_pool: SessionPool = SessionPool()
    
    async def load_accounts_from_sessions(
        self, 
        session_files: List[str]
    ) -> List[str]:
        """批量加載 .session 文件"""
        pass
    
    async def add_account(
        self, 
        account_id: str, 
        session_file: str,
        config: AccountConfig
    ) -> AccountInstance:
        """添加單個賬號"""
        pass
    
    async def remove_account(self, account_id: str) -> bool:
        """移除賬號"""
        pass
    
    async def start_account(self, account_id: str) -> bool:
        """啟動賬號"""
        pass
    
    async def stop_account(self, account_id: str) -> bool:
        """停止賬號"""
        pass
    
    def get_account_status(self, account_id: str) -> AccountStatus:
        """獲取賬號狀態"""
        pass
    
    def list_accounts(self) -> List[AccountInfo]:
        """列出所有賬號"""
        pass
```

#### 4.1.2 數據結構

```python
@dataclass
class AccountConfig:
    """賬號配置"""
    account_id: str
    session_file: str
    script_id: str  # 關聯的劇本 ID
    group_ids: List[int]  # 監聽的群組 ID 列表
    active: bool = True
    reply_rate: float = 0.3  # 回復頻率 (0-1)
    redpacket_enabled: bool = True
    custom_params: Dict[str, Any] = None

@dataclass
class AccountStatus:
    """賬號狀態"""
    account_id: str
    online: bool
    last_activity: datetime
    message_count: int
    reply_count: int
    redpacket_count: int
    error_count: int
    last_error: Optional[str] = None
```

### 4.2 劇本引擎模塊 (ScriptEngine)

#### 4.2.1 劇本格式設計

**YAML 格式示例** (`scripts/daily_chat.yaml`):

```yaml
script_id: daily_chat
version: 1.0
description: 日常聊天劇本

scenes:
  - id: greeting
    triggers:
      - type: keyword
        keywords: ["你好", "hello", "hi"]
      - type: new_member
    responses:
      - template: "你好！很高興認識你 😊"
      - template: "Hi! Nice to meet you!"
    next_scene: conversation

  - id: conversation
    triggers:
      - type: message
        min_length: 5
    responses:
      - template: "{{contextual_reply}}"
        ai_generate: true
        context_window: 10
    next_scene: conversation

  - id: redpacket_detected
    triggers:
      - type: redpacket
    responses:
      - action: participate_redpacket
        strategy: random
        probability: 0.7
    next_scene: conversation

states:
  - name: waiting_for_response
    timeout: 300
    on_timeout: send_followup

variables:
  user_name: "{{extract_name}}"
  conversation_topic: "{{detect_topic}}"
```

#### 4.2.2 類設計

```python
class ScriptEngine:
    """劇本引擎"""
    
    def __init__(self):
        self.scripts: Dict[str, Script] = {}
        self.running_states: Dict[str, ScriptState] = {}
    
    def load_script(self, script_id: str, script_path: str) -> Script:
        """加載劇本"""
        pass
    
    async def process_message(
        self,
        account_id: str,
        message: Message,
        context: DialogueContext
    ) -> Optional[Response]:
        """處理消息，返回回復"""
        pass
    
    def get_current_scene(self, account_id: str) -> str:
        """獲取當前場景"""
        pass
    
    def transition_scene(
        self, 
        account_id: str, 
        scene_id: str
    ) -> bool:
        """切換場景"""
        pass
```

### 4.3 對話管理器模塊 (DialogueManager)

#### 4.3.1 類設計

```python
class DialogueManager:
    """對話管理器"""
    
    def __init__(self):
        self.contexts: Dict[str, DialogueContext] = {}
        self.ai_client: AsyncOpenAI = None
    
    async def understand_message(
        self,
        message: Message,
        context: DialogueContext
    ) -> MessageIntent:
        """理解消息意圖"""
        pass
    
    async def generate_reply(
        self,
        account_id: str,
        message: Message,
        script: Script,
        context: DialogueContext
    ) -> str:
        """生成回復"""
        pass
    
    def update_context(
        self,
        account_id: str,
        message: Message,
        reply: str
    ):
        """更新對話上下文"""
        pass
    
    def should_reply(
        self,
        account_id: str,
        message: Message,
        context: DialogueContext
    ) -> bool:
        """判斷是否應該回復"""
        pass
```

#### 4.3.2 上下文管理

```python
@dataclass
class DialogueContext:
    """對話上下文"""
    account_id: str
    group_id: int
    history: List[MessagePair]  # [(user_msg, ai_reply), ...]
    current_topic: Optional[str]
    last_reply_time: datetime
    reply_count_today: int
    mentioned_users: Set[int]
    active_conversations: Dict[int, ConversationThread]
```

### 4.4 紅包處理器模塊 (RedpacketHandler)

#### 4.4.1 類設計

```python
class RedpacketHandler:
    """紅包處理器"""
    
    def __init__(self):
        self.strategies: Dict[str, RedpacketStrategy] = {}
        self.participation_log: List[RedpacketRecord] = []
    
    async def detect_redpacket(
        self,
        message: Message
    ) -> Optional[RedpacketInfo]:
        """檢測紅包消息"""
        pass
    
    async def should_participate(
        self,
        account_id: str,
        redpacket: RedpacketInfo,
        context: DialogueContext
    ) -> bool:
        """決定是否參與"""
        pass
    
    async def participate(
        self,
        account_id: str,
        redpacket: RedpacketInfo
    ) -> RedpacketResult:
        """執行搶紅包"""
        pass
    
    def get_statistics(
        self,
        account_id: str,
        time_range: TimeRange
    ) -> RedpacketStats:
        """獲取紅包統計"""
        pass
```

#### 4.4.2 紅包策略

```python
class RedpacketStrategy:
    """紅包參與策略"""
    
    def evaluate(
        self,
        redpacket: RedpacketInfo,
        account_config: AccountConfig,
        context: DialogueContext
    ) -> float:
        """評估參與概率 (0-1)"""
        pass

class RandomStrategy(RedpacketStrategy):
    """隨機策略"""
    base_probability: float = 0.5

class TimeBasedStrategy(RedpacketStrategy):
    """基於時間的策略"""
    peak_hours: List[int] = [18, 19, 20, 21]
    peak_probability: float = 0.8
    off_peak_probability: float = 0.3

class FrequencyStrategy(RedpacketStrategy):
    """基於頻率的策略"""
    max_per_hour: int = 5
    cooldown_seconds: int = 300
```

### 4.5 監控服務模塊 (MonitorService)

#### 4.5.1 類設計

```python
class MonitorService:
    """監控服務"""
    
    def __init__(self):
        self.metrics: Dict[str, AccountMetrics] = {}
        self.alerts: List[Alert] = []
    
    def record_message(
        self,
        account_id: str,
        message_type: str,
        success: bool
    ):
        """記錄消息事件"""
        pass
    
    def record_reply(
        self,
        account_id: str,
        reply_time: float,
        success: bool
    ):
        """記錄回復事件"""
        pass
    
    def record_redpacket(
        self,
        account_id: str,
        result: RedpacketResult
    ):
        """記錄紅包事件"""
        pass
    
    def get_account_metrics(
        self,
        account_id: str,
        time_range: TimeRange
    ) -> AccountMetrics:
        """獲取賬號指標"""
        pass
    
    def get_system_metrics(
        self,
        time_range: TimeRange
    ) -> SystemMetrics:
        """獲取系統指標"""
        pass
    
    def check_alerts(self) -> List[Alert]:
        """檢查告警"""
        pass
```

---

## 數據流設計

### 5.1 消息處理流程

```
Telegram 群組消息
    ↓
SessionPool 接收消息事件
    ↓
AccountManager 路由到對應賬號
    ↓
DialogueManager 理解消息
    ├─ 提取意圖
    ├─ 更新上下文
    └─ 判斷是否需要回復
    ↓
ScriptEngine 執行劇本
    ├─ 匹配場景
    ├─ 生成回復模板
    └─ 切換場景
    ↓
DialogueManager 生成最終回復
    ├─ AI 生成內容
    ├─ 上下文關聯
    └─ 自然度優化
    ↓
SessionPool 發送回復
    ↓
MonitorService 記錄事件
```

### 5.2 紅包處理流程

```
Telegram 紅包消息
    ↓
RedpacketHandler 檢測紅包
    ├─ 解析紅包信息
    └─ 提取金額、數量等
    ↓
RedpacketHandler 評估策略
    ├─ 檢查參與條件
    ├─ 計算參與概率
    └─ 決定是否參與
    ↓
[參與] → SessionPool 執行搶紅包
    ↓
RedpacketHandler 記錄結果
    ↓
MonitorService 更新統計
```

### 5.3 賬號管理流程

```
批量導入 .session 文件
    ↓
AccountManager 解析文件
    ├─ 驗證文件有效性
    ├─ 提取賬號信息
    └─ 創建 AccountInstance
    ↓
AccountManager 初始化會話
    ├─ 加載 Pyrogram Client
    ├─ 註冊消息處理器
    └─ 連接 Telegram API
    ↓
AccountManager 啟動賬號
    ├─ 加載劇本配置
    ├─ 初始化對話上下文
    └─ 開始監聽群組
    ↓
MonitorService 開始監控
```

---

## 實施計劃

### 階段 1: 基礎架構搭建 (Week 1-2)

#### 任務 1.1: 賬號管理模塊
- [ ] 設計 `AccountManager` 類結構
- [ ] 實現批量加載 `.session` 文件功能
- [ ] 實現賬號動態添加/移除
- [ ] 實現賬號狀態管理
- [ ] 實現異常處理和重連機制

**交付物**:
- `group_ai_service/account_manager.py`
- `group_ai_service/models/account.py`
- 單元測試

#### 任務 1.2: 會話池擴展
- [ ] 擴展 `SessionPool` 支持多賬號
- [ ] 實現賬號隔離機制
- [ ] 實現消息路由邏輯
- [ ] 優化資源管理（內存、連接）

**交付物**:
- `group_ai_service/session_pool.py` (擴展)
- 性能測試報告

#### 任務 1.3: 數據庫設計
- [ ] 設計賬號配置表
- [ ] 設計劇本配置表
- [ ] 設計對話歷史表
- [ ] 設計監控數據表
- [ ] 實現數據庫遷移

**交付物**:
- `group_ai_service/models/db_models.py`
- `migrations/group_ai_*.sql`

### 階段 2: 劇本引擎開發 (Week 3-4)

#### 任務 2.1: 劇本解析器
- [ ] 設計劇本 YAML 格式
- [ ] 實現劇本解析器
- [ ] 實現場景狀態機
- [ ] 實現變量替換機制

**交付物**:
- `group_ai_service/script_engine.py`
- `group_ai_service/script_parser.py`
- 劇本示例文件

#### 任務 2.2: 劇本執行引擎
- [ ] 實現場景匹配邏輯
- [ ] 實現條件分支處理
- [ ] 實現場景切換機制
- [ ] 實現劇本版本管理

**交付物**:
- `group_ai_service/script_executor.py`
- 集成測試

#### 任務 2.3: 劇本管理 API
- [ ] 實現劇本 CRUD API
- [ ] 實現劇本預覽功能
- [ ] 實現劇本測試工具

**交付物**:
- `admin-backend/app/api/group_ai/scripts.py`
- API 文檔

### 階段 3: 智能對話系統 (Week 5-6)

#### 任務 3.1: 對話管理器
- [ ] 實現消息理解模塊
- [ ] 實現上下文管理
- [ ] 實現多輪對話追蹤
- [ ] 實現重複檢測機制

**交付物**:
- `group_ai_service/dialogue_manager.py`
- `group_ai_service/context_manager.py`

#### 任務 3.2: AI 生成模塊
- [ ] 集成 OpenAI API
- [ ] 實現提示詞構建
- [ ] 實現上下文注入
- [ ] 實現回復優化

**交付物**:
- `group_ai_service/ai_generator.py`
- 性能優化報告

#### 任務 3.3: 自然度優化
- [ ] 實現回復多樣化
- [ ] 實現時機控制（避免過於頻繁）
- [ ] 實現情感分析
- [ ] 實現話題引導

**交付物**:
- `group_ai_service/naturalness_optimizer.py`
- A/B 測試結果

### 階段 4: 紅包遊戲功能 (Week 7)

#### 任務 4.1: 紅包檢測
- [ ] 實現紅包消息識別
- [ ] 解析紅包信息（金額、數量、類型）
- [ ] 實現紅包狀態追蹤

**交付物**:
- `group_ai_service/redpacket_handler.py` (檢測部分)
- 測試用例

#### 任務 4.2: 參與策略
- [ ] 實現多種參與策略
- [ ] 實現策略配置接口
- [ ] 實現參與概率計算

**交付物**:
- `group_ai_service/redpacket_strategies.py`
- 策略文檔

#### 任務 4.3: 執行與記錄
- [ ] 實現搶紅包操作
- [ ] 實現結果記錄
- [ ] 實現統計分析

**交付物**:
- `group_ai_service/redpacket_handler.py` (完整)
- 統計報表

### 階段 5: 監控與調控系統 (Week 8)

#### 任務 5.1: 監控服務
- [ ] 實現指標收集
- [ ] 實現實時監控
- [ ] 實現告警機制
- [ ] 實現數據可視化

**交付物**:
- `group_ai_service/monitor_service.py`
- `admin-backend/app/api/group_ai/monitor.py`
- 監控儀表板

#### 任務 5.2: 調控接口
- [ ] 實現參數調整 API
- [ ] 實現批量操作接口
- [ ] 實現實時生效機制

**交付物**:
- `admin-backend/app/api/group_ai/control.py`
- API 文檔

#### 任務 5.3: Web 管理界面
- [ ] 賬號管理界面
- [ ] 劇本配置界面
- [ ] 監控儀表板
- [ ] 調控面板

**交付物**:
- `saas-demo/src/app/group-ai/` 頁面
- 用戶手冊

### 階段 6: 測試與優化 (Week 9-10)

#### 任務 6.1: 功能測試
- [ ] 單賬號功能測試
- [ ] 多賬號並行測試
- [ ] 劇本執行測試
- [ ] 紅包功能測試

**交付物**:
- 測試報告
- Bug 修復記錄

#### 任務 6.2: 性能測試
- [ ] 10 賬號並行測試
- [ ] 50 賬號並行測試
- [ ] 100 賬號並行測試
- [ ] 壓力測試

**交付物**:
- 性能測試報告
- 優化建議

#### 任務 6.3: 穩定性測試
- [ ] 長時間運行測試（24h+）
- [ ] 異常恢復測試
- [ ] 網絡斷線測試

**交付物**:
- 穩定性報告
- 改進方案

---

## 技術規格

### 6.1 技術棧

| 組件 | 技術選型 | 版本要求 |
|------|---------|---------|
| Python | Python 3.11+ | 3.11+ |
| Telegram 客戶端 | Pyrogram | 2.0+ |
| AI 服務 | OpenAI API | - |
| 數據庫 | PostgreSQL / SQLite | - |
| 後端框架 | FastAPI | 0.115+ |
| 前端框架 | Next.js | 16+ |
| 消息隊列 | Redis / RabbitMQ (可選) | - |
| 監控 | Prometheus (可選) | - |

### 6.2 數據庫設計

#### 表 1: group_ai_accounts

| 字段 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| account_id | VARCHAR(100) | 賬號 ID（唯一） |
| session_file | VARCHAR(500) | Session 文件路徑 |
| script_id | VARCHAR(100) | 關聯劇本 ID |
| group_ids | JSON | 監聽的群組 ID 列表 |
| active | BOOLEAN | 是否啟用 |
| reply_rate | FLOAT | 回復頻率 (0-1) |
| redpacket_enabled | BOOLEAN | 是否啟用紅包 |
| config | JSON | 自定義配置 |
| created_at | TIMESTAMP | 創建時間 |
| updated_at | TIMESTAMP | 更新時間 |

#### 表 2: group_ai_scripts

| 字段 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| script_id | VARCHAR(100) | 劇本 ID（唯一） |
| name | VARCHAR(200) | 劇本名稱 |
| version | VARCHAR(20) | 版本號 |
| content | TEXT | 劇本內容 (YAML) |
| description | TEXT | 描述 |
| created_at | TIMESTAMP | 創建時間 |
| updated_at | TIMESTAMP | 更新時間 |

#### 表 3: group_ai_dialogue_history

| 字段 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| account_id | VARCHAR(100) | 賬號 ID |
| group_id | BIGINT | 群組 ID |
| message_id | BIGINT | 消息 ID |
| user_id | BIGINT | 用戶 ID |
| message_text | TEXT | 消息內容 |
| reply_text | TEXT | AI 回復內容 |
| timestamp | TIMESTAMP | 時間戳 |
| context_snapshot | JSON | 上下文快照 |

#### 表 4: group_ai_redpacket_logs

| 字段 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| account_id | VARCHAR(100) | 賬號 ID |
| group_id | BIGINT | 群組 ID |
| redpacket_id | VARCHAR(100) | 紅包 ID |
| amount | DECIMAL | 金額 |
| success | BOOLEAN | 是否成功 |
| timestamp | TIMESTAMP | 時間戳 |

#### 表 5: group_ai_metrics

| 字段 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| account_id | VARCHAR(100) | 賬號 ID |
| metric_type | VARCHAR(50) | 指標類型 |
| metric_value | FLOAT | 指標值 |
| timestamp | TIMESTAMP | 時間戳 |

### 6.3 API 設計

#### 賬號管理 API

```
POST   /api/v1/group-ai/accounts              # 創建賬號
GET    /api/v1/group-ai/accounts              # 列出所有賬號
GET    /api/v1/group-ai/accounts/{id}          # 獲取賬號詳情
PUT    /api/v1/group-ai/accounts/{id}          # 更新賬號配置
DELETE /api/v1/group-ai/accounts/{id}          # 刪除賬號
POST   /api/v1/group-ai/accounts/batch-import  # 批量導入
POST   /api/v1/group-ai/accounts/{id}/start    # 啟動賬號
POST   /api/v1/group-ai/accounts/{id}/stop     # 停止賬號
GET    /api/v1/group-ai/accounts/{id}/status  # 獲取賬號狀態
```

#### 劇本管理 API

```
POST   /api/v1/group-ai/scripts               # 創建劇本
GET    /api/v1/group-ai/scripts                # 列出所有劇本
GET    /api/v1/group-ai/scripts/{id}          # 獲取劇本詳情
PUT    /api/v1/group-ai/scripts/{id}          # 更新劇本
DELETE /api/v1/group-ai/scripts/{id}          # 刪除劇本
POST   /api/v1/group-ai/scripts/{id}/test     # 測試劇本
POST   /api/v1/group-ai/scripts/{id}/deploy   # 部署劇本
```

#### 監控 API

```
GET    /api/v1/group-ai/monitor/accounts       # 獲取所有賬號監控數據
GET    /api/v1/group-ai/monitor/accounts/{id}  # 獲取單個賬號監控數據
GET    /api/v1/group-ai/monitor/system        # 獲取系統監控數據
GET    /api/v1/group-ai/monitor/metrics       # 獲取指標數據
GET    /api/v1/group-ai/monitor/alerts        # 獲取告警列表
```

#### 調控 API

```
POST   /api/v1/group-ai/control/accounts/{id}/params  # 調整賬號參數
POST   /api/v1/group-ai/control/batch-update          # 批量更新
POST   /api/v1/group-ai/control/accounts/{id}/script # 切換劇本
POST   /api/v1/group-ai/control/accounts/{id}/rate   # 調整回復頻率
```

---

## 監控與調控系統

### 7.1 監控指標

#### 賬號級指標

| 指標 | 說明 | 閾值 |
|------|------|------|
| `account_online` | 賬號在線狀態 | - |
| `message_received_count` | 接收消息數 | - |
| `message_sent_count` | 發送消息數 | - |
| `reply_rate` | 回復率 | > 20% |
| `avg_reply_time` | 平均回復時間 | < 2s |
| `error_count` | 錯誤次數 | < 10/小時 |
| `redpacket_participation_rate` | 紅包參與率 | - |
| `redpacket_success_rate` | 紅包成功率 | > 50% |

#### 系統級指標

| 指標 | 說明 | 閾值 |
|------|------|------|
| `total_accounts` | 總賬號數 | - |
| `active_accounts` | 活躍賬號數 | - |
| `system_cpu_usage` | CPU 使用率 | < 80% |
| `system_memory_usage` | 內存使用率 | < 70% |
| `total_messages_per_minute` | 每分鐘消息數 | - |
| `api_error_rate` | API 錯誤率 | < 1% |

### 7.2 告警規則

| 告警類型 | 觸發條件 | 級別 |
|----------|---------|------|
| 賬號離線 | 賬號連續 5 分鐘無響應 | Warning |
| 錯誤率過高 | 錯誤次數 > 10/小時 | Warning |
| 回復率過低 | 回復率 < 10% | Info |
| 系統資源告急 | CPU > 90% 或 Memory > 85% | Critical |
| 大量賬號異常 | 超過 10% 賬號異常 | Critical |

### 7.3 調控參數

#### 可調控參數列表

| 參數 | 類型 | 範圍 | 說明 |
|------|------|------|------|
| `reply_rate` | float | 0.0 - 1.0 | 回復頻率 |
| `redpacket_probability` | float | 0.0 - 1.0 | 紅包參與概率 |
| `max_replies_per_hour` | int | 1 - 100 | 每小時最大回復數 |
| `min_reply_interval` | int | 1 - 300 | 最小回復間隔（秒） |
| `ai_temperature` | float | 0.0 - 2.0 | AI 生成溫度 |
| `context_window` | int | 5 - 50 | 上下文窗口大小 |

---

## 測試策略

### 8.1 單元測試

- **賬號管理模塊**: 測試賬號加載、啟動、停止
- **劇本引擎**: 測試劇本解析、場景切換
- **對話管理器**: 測試消息理解、回復生成
- **紅包處理器**: 測試檢測、策略、執行

### 8.2 集成測試

- **多賬號並行**: 測試 10/50/100 賬號同時運行
- **劇本執行**: 測試完整對話流程
- **紅包參與**: 測試紅包檢測和參與
- **異常恢復**: 測試斷線重連、錯誤處理

### 8.3 性能測試

- **並發能力**: 測試最大支持賬號數
- **響應時間**: 測試消息處理延遲
- **資源使用**: 測試 CPU、內存佔用
- **穩定性**: 測試長時間運行（24h+）

### 8.4 用戶體驗測試

- **對話自然度**: 人工評估對話質量
- **紅包參與真實感**: 評估參與行為真實性
- **系統易用性**: 評估管理界面易用性

---

## 風險與緩解

### 9.1 技術風險

| 風險 | 影響 | 概率 | 緩解措施 |
|------|------|------|---------|
| Telegram API 限流 | 高 | 中 | 實現請求節流和重試機制 |
| 多賬號資源消耗 | 高 | 高 | 優化資源管理，支持分佈式部署 |
| 劇本執行錯誤 | 中 | 中 | 完善的錯誤處理和日誌記錄 |
| AI 生成質量 | 中 | 低 | 多種提示詞策略，人工審核 |

### 9.2 運營風險

| 風險 | 影響 | 概率 | 緩解措施 |
|------|------|------|---------|
| 賬號被封禁 | 高 | 中 | 嚴格遵守 Telegram 規則，行為模擬真實用戶 |
| 劇本泄露 | 中 | 低 | 劇本加密存儲，訪問控制 |
| 數據丟失 | 高 | 低 | 定期備份，數據持久化 |

---

## 後續優化方向

1. **分佈式部署**: 支持多服務器部署，提高擴展性
2. **機器學習優化**: 使用 ML 模型優化回復質量和參與策略
3. **A/B 測試**: 支持劇本和策略的 A/B 測試
4. **自動化運營**: 自動調整參數，優化運營效果
5. **多平台支持**: 擴展到其他即時通訊平台

---

**文檔版本**: v1.0  
**最後更新**: 2024-12-19

