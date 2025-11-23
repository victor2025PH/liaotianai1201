# 階段 3: 對話管理器實現

> **更新日期**: 2024-12-19  
> **狀態**: 進行中

---

## 完成功能

### ✅ 對話管理器 (DialogueManager)

**文件**: `group_ai_service/dialogue_manager.py`

**功能**:
1. **對話上下文管理**
   - 為每個賬號-群組對維護獨立的上下文
   - 歷史消息管理（最近 50 條）
   - 每日回復計數
   - 回復時間追蹤

2. **消息處理流程**
   - 接收群組消息
   - 判斷是否需要回復
   - 調用劇本引擎生成回復
   - 更新上下文

3. **回復控制**
   - 回復頻率控制（reply_rate）
   - 每日回復上限（max_replies_per_hour）
   - 最小回復間隔（min_reply_interval）
   - 賬號激活狀態檢查

4. **上下文檢測**
   - 新成員檢測（待實現）
   - 紅包消息檢測（基礎實現）

### ✅ 會話池集成

**更新**: `group_ai_service/session_pool.py`

**改進**:
1. 集成 `DialogueManager`
2. 自動設置消息處理器
3. 消息路由到對話管理器
4. 自動發送回復

---

## 使用示例

### 初始化對話管理器

```python
from group_ai_service import DialogueManager, ScriptEngine, ScriptParser

# 創建對話管理器
dialogue_manager = DialogueManager()

# 加載劇本
parser = ScriptParser()
script = parser.load_script("ai_models/group_scripts/daily_chat.yaml")

# 創建劇本引擎
script_engine = ScriptEngine()
script_engine.initialize_account("account_1", script)

# 初始化對話管理器
dialogue_manager.initialize_account(
    account_id="account_1",
    script_engine=script_engine,
    group_ids=[-1001234567890, -1001234567891]
)
```

### 處理消息

```python
# 在消息處理器中
reply = await dialogue_manager.process_message(
    account_id="account_1",
    group_id=-1001234567890,
    message=message,
    account_config=config
)

if reply:
    await message.reply_text(reply)
```

---

## 架構設計

### 數據流

```
Telegram 群組消息
    ↓
ExtendedSessionPool (消息接收)
    ↓
DialogueManager.process_message()
    ↓
檢查回復條件 (reply_rate, interval, limit)
    ↓
ScriptEngine.process_message()
    ↓
生成回復
    ↓
更新上下文
    ↓
發送回復
```

### 上下文結構

```python
class DialogueContext:
    account_id: str
    group_id: int
    history: deque  # 最近 50 條消息
    last_reply_time: datetime
    reply_count_today: int
    current_topic: str
    mentioned_users: set
```

---

## 測試

### 測試腳本

```bash
py scripts/test_dialogue_manager.py
```

**測試覆蓋**:
- ✅ 對話管理器初始化
- ✅ 消息處理
- ✅ 上下文管理
- ✅ 回復頻率控制

---

## 待完善功能

1. **新成員檢測**
   - 實現 `_check_new_member` 方法
   - 檢測新成員加入事件

2. **紅包檢測增強**
   - 完善 `_check_redpacket` 方法
   - 支持更多紅包類型

3. **話題追蹤**
   - 實現話題檢測和追蹤
   - 話題切換邏輯

4. **用戶提及**
   - 追蹤 @ 提及
   - 個性化回復

---

## 下一步

1. **完善檢測功能**
   - 新成員檢測
   - 紅包檢測增強

2. **開始階段 4**
   - 紅包處理器開發

3. **性能優化**
   - 上下文緩存
   - 批量處理

---

**狀態**: ✅ 基礎功能完成，待完善檢測功能

