# 階段 2: 變量替換和 AI 生成集成

> **更新日期**: 2024-12-19  
> **狀態**: 已完成

---

## 完成功能

### ✅ 變量解析器 (VariableResolver)

**文件**: `group_ai_service/variable_resolver.py`

**功能**:
1. **基礎變量替換**
   - `{{user_name}}` - 用戶名稱
   - `{{user_id}}` - 用戶 ID
   - `{{chat_id}}` - 聊天 ID
   - `{{message_text}}` - 消息文本
   - `{{message_length}}` - 消息長度

2. **函數調用支持**
   - `{{extract_name()}}` - 提取用戶名
   - `{{detect_topic()}}` - 檢測話題
   - `{{current_time()}}` - 當前時間
   - `{{random_emoji()}}` - 隨機表情
   - `{{upper(text)}}` - 轉大寫
   - `{{lower(text)}}` - 轉小寫

3. **上下文變量**
   - 從 `context` 字典中讀取變量
   - 從 `state` 字典中讀取變量

4. **自定義函數註冊**
   - 支持註冊自定義函數
   - 函數簽名: `func(message, context, state, *args) -> str`

### ✅ AI 生成器 (AIGenerator)

**文件**: `group_ai_service/ai_generator.py`

**功能**:
1. **多提供商支持**
   - OpenAI (GPT-3.5/GPT-4)
   - Mock 模式（用於測試）

2. **上下文管理**
   - 構建上下文消息列表
   - 支持系統提示詞
   - 可配置溫度、最大 token 數

3. **錯誤處理**
   - API 調用失敗時自動降級到 Mock 模式
   - 完善的日誌記錄

### ✅ 劇本引擎集成

**更新**: `group_ai_service/script_engine.py`

**改進**:
1. 集成 `VariableResolver` 進行變量替換
2. 集成 `AIGenerator` 進行 AI 回復生成
3. 支持上下文消息構建
4. 當 `response.ai_generate = true` 時自動調用 AI 生成

---

## 使用示例

### 變量替換

```python
from group_ai_service import VariableResolver
from pyrogram.types import Message

resolver = VariableResolver()
message = ...  # Message 對象

# 基礎變量
template = "你好，{{user_name}}！"
result = resolver.resolve(template, message)
# 結果: "你好，張三！"

# 函數調用
template = "話題: {{detect_topic()}}"
result = resolver.resolve(template, message)
# 結果: "話題: 天氣" (如果消息包含天氣相關關鍵詞)
```

### AI 生成

```python
from group_ai_service import get_ai_generator

ai_generator = get_ai_generator()

# 生成回復
reply = await ai_generator.generate_reply(
    message=message,
    context_messages=[...],
    temperature=0.7,
    max_tokens=150
)
```

### 劇本中使用

```yaml
scenes:
  - id: conversation
    triggers:
      - type: message
        min_length: 5
    responses:
      - template: "你是一個友好的助手"
        ai_generate: true
        context_window: 10
        temperature: 0.7
```

---

## 配置

### 環境變量

```bash
# AI 提供商 (openai, mock)
AI_PROVIDER=mock

# OpenAI API Key (如果使用 OpenAI)
AI_API_KEY=sk-...
```

### 代碼配置

```python
from group_ai_service import AIGenerator

# 創建自定義生成器
generator = AIGenerator(provider="openai", api_key="sk-...")

# 或使用全局實例
from group_ai_service import get_ai_generator
generator = get_ai_generator()
```

---

## 測試

### 變量解析器測試

```bash
py scripts/test_variable_resolver.py
```

**測試覆蓋**:
- ✅ 基礎變量替換
- ✅ 函數調用
- ✅ 嵌套變量
- ✅ 上下文變量

### 劇本引擎測試

```bash
py scripts/test_script_engine.py
```

**測試覆蓋**:
- ✅ 變量替換集成
- ✅ AI 生成集成（Mock 模式）

---

## 下一步

1. **完善 AI 生成**
   - 支持更多 AI 提供商（Claude, Gemini 等）
   - 實現上下文緩存
   - 優化提示詞構建

2. **增強變量系統**
   - 支持更複雜的表達式
   - 支持條件判斷
   - 支持循環和迭代

3. **性能優化**
   - 變量解析緩存
   - AI 生成批處理
   - 異步優化

---

**狀態**: ✅ 基礎功能完成，可擴展

