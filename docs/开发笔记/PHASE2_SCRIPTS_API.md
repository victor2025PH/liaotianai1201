# 階段 2: 劇本管理 API 實現

> **更新日期**: 2024-12-19  
> **狀態**: 已完成

---

## 完成功能

### ✅ 劇本管理 API

**文件**: `admin-backend/app/api/group_ai/scripts.py`

**端點列表**:

1. **POST `/api/v1/group-ai/scripts/`** - 創建劇本
   - 驗證 YAML 格式
   - 驗證劇本邏輯
   - 保存到數據庫

2. **GET `/api/v1/group-ai/scripts/`** - 列出所有劇本
   - 支持分頁（skip, limit）
   - 返回劇本基本信息

3. **GET `/api/v1/group-ai/scripts/{script_id}`** - 獲取劇本詳情
   - 返回完整 YAML 內容
   - 返回場景列表

4. **PUT `/api/v1/group-ai/scripts/{script_id}`** - 更新劇本
   - 支持部分更新
   - 更新時重新驗證

5. **DELETE `/api/v1/group-ai/scripts/{script_id}`** - 刪除劇本
   - 軟刪除（可選）

6. **POST `/api/v1/group-ai/scripts/{script_id}/test`** - 測試劇本
   - 模擬消息處理
   - 返回回復和場景狀態

7. **POST `/api/v1/group-ai/scripts/upload`** - 上傳劇本文件
   - 支持 YAML 文件上傳
   - 自動解析和驗證

---

## API 文檔

### 創建劇本

```http
POST /api/v1/group-ai/scripts/
Content-Type: application/json

{
  "script_id": "daily_chat",
  "name": "日常聊天",
  "version": "1.0",
  "description": "日常聊天劇本",
  "yaml_content": "..."
}
```

**響應**:
```json
{
  "script_id": "daily_chat",
  "name": "日常聊天",
  "version": "1.0",
  "description": "日常聊天劇本",
  "scene_count": 3,
  "created_at": "2024-12-19T10:00:00",
  "updated_at": "2024-12-19T10:00:00"
}
```

### 列出劇本

```http
GET /api/v1/group-ai/scripts/?skip=0&limit=100
```

**響應**:
```json
[
  {
    "script_id": "daily_chat",
    "name": "日常聊天",
    "version": "1.0",
    "description": "日常聊天劇本",
    "scene_count": 3,
    "created_at": "2024-12-19T10:00:00",
    "updated_at": "2024-12-19T10:00:00"
  }
]
```

### 獲取劇本詳情

```http
GET /api/v1/group-ai/scripts/daily_chat
```

**響應**:
```json
{
  "script_id": "daily_chat",
  "name": "日常聊天",
  "version": "1.0",
  "description": "日常聊天劇本",
  "scene_count": 3,
  "yaml_content": "...",
  "scenes": [
    {
      "id": "greeting",
      "triggers_count": 1,
      "responses_count": 3,
      "next_scene": "conversation"
    }
  ],
  "created_at": "2024-12-19T10:00:00",
  "updated_at": "2024-12-19T10:00:00"
}
```

### 測試劇本

```http
POST /api/v1/group-ai/scripts/daily_chat/test?test_message=你好
```

**響應**:
```json
{
  "script_id": "daily_chat",
  "test_message": "你好",
  "reply": "你好！很高興認識你 😊",
  "current_scene": "conversation"
}
```

### 上傳劇本文件

```http
POST /api/v1/group-ai/scripts/upload
Content-Type: multipart/form-data

file: <yaml_file>
```

---

## 數據驗證

### YAML 格式驗證
- 使用 `ScriptParser` 解析 YAML
- 檢查必需字段（script_id, scenes）
- 驗證場景引用

### 劇本邏輯驗證
- 檢查場景引用是否存在
- 驗證觸發條件格式
- 驗證回復模板格式

---

## 錯誤處理

### 常見錯誤

1. **400 Bad Request**
   - YAML 格式錯誤
   - 劇本驗證失敗
   - 劇本 ID 已存在

2. **404 Not Found**
   - 劇本不存在

3. **500 Internal Server Error**
   - 數據庫錯誤
   - 解析錯誤

---

## 測試

### 測試腳本

```bash
py scripts/test_scripts_api.py
```

**測試覆蓋**:
- ✅ 創建劇本
- ✅ 列出劇本
- ✅ 獲取詳情
- ✅ 測試劇本
- ✅ 更新劇本
- ✅ 刪除劇本

---

## 數據庫集成

### 模型

使用 `GroupAIScript` 模型（`admin-backend/app/models/group_ai.py`）:

```python
class GroupAIScript(Base):
    __tablename__ = "group_ai_scripts"
    
    script_id = Column(String, primary_key=True)
    name = Column(String)
    version = Column(String)
    description = Column(Text, nullable=True)
    yaml_content = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

---

## 下一步

1. **前端集成**
   - 連接真實 API
   - 實現劇本編輯器
   - 實現劇本測試界面

2. **功能增強**
   - 劇本版本管理
   - 劇本導入/導出
   - 劇本模板庫

3. **性能優化**
   - 劇本緩存
   - 批量操作
   - 異步處理

---

**狀態**: ✅ 完整實現，待測試

