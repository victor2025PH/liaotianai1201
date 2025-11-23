# 劇本 YAML 格式說明

## 標準格式

劇本必須使用以下 YAML 格式：

```yaml
script_id: 劇本ID
version: 1.0
description: 劇本描述（可選）

scenes:
  - id: 場景ID
    triggers:
      - type: keyword
        keywords: ["關鍵詞1", "關鍵詞2"]
      - type: message
        min_length: 5
    responses:
      - template: "回復內容"
      - template: "{{contextual_reply}}"
        ai_generate: true
        context_window: 10
    next_scene: 下一個場景ID（可選）

variables:
  變量名: "變量值"

metadata:
  元數據鍵: 元數據值
```

## 示例

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
        temperature: 0.7
    next_scene: conversation

variables:
  user_name: "{{extract_name}}"
  conversation_topic: "{{detect_topic}}"

metadata:
  author: "System"
  created_at: "2024-12-19"
```

## 觸發類型

- `keyword`: 關鍵詞觸發
- `message`: 消息觸發（可設置 min_length, max_length）
- `new_member`: 新成員加入
- `redpacket`: 紅包檢測
- `pattern`: 正則表達式匹配

## 回復模板

- `template`: 回復模板文本
- `ai_generate`: 是否使用 AI 生成（true/false）
- `context_window`: 上下文窗口大小
- `temperature`: AI 生成溫度（0-1）

## 常見錯誤

### 錯誤 1: 缺少 script_id
```
劇本格式錯誤：缺少 script_id 字段
```
**解決方案**: 在 YAML 頂部添加 `script_id: 你的劇本ID`

### 錯誤 2: 場景缺少 id
```
劇本格式錯誤：場景缺少 id 字段
```
**解決方案**: 每個場景必須有唯一的 `id` 字段

### 錯誤 3: 格式不匹配
如果使用舊格式（`step`, `actor`, `action`），需要轉換為新格式。

## 格式轉換

如果您的劇本使用舊格式，需要手動轉換：

**舊格式**:
```yaml
- step: 9
  actor: siya
  action: speak
  lines:
    - 好的,那什么时候开始啊?
```

**新格式**:
```yaml
script_id: your_script_id
version: 1.0
scenes:
  - id: scene_9
    triggers:
      - type: message
    responses:
      - template: "好的,那什么时候开始啊?"
```

