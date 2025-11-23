# 功能測試指南

> **更新日期**: 2025-01-07

---

## 測試前準備

### 1. 環境檢查

確保以下服務已啟動：
- ✅ 後端服務：`http://localhost:8000`
- ✅ 前端服務：`http://localhost:3000`
- ✅ 數據庫：SQLite（默認）或 PostgreSQL

### 2. 配置檢查

**後端配置** (`admin-backend/.env`):
```env
DATABASE_URL=sqlite:///./group_ai.db
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
REDIS_URL=redis://localhost:6379
```

**前端配置** (`saas-demo/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 測試流程

### 階段 1: 劇本和帳號聊天功能測試

#### 1.1 創建劇本

**通過前端**:
1. 訪問 `http://localhost:3000/group-ai/scripts`
2. 點擊「創建劇本」
3. 填寫劇本信息：
   - 劇本 ID: `test_script`
   - 名稱: `測試劇本`
   - 版本: `1.0`
   - YAML 內容：
   ```yaml
   script_id: test_script
   version: 1.0
   description: 測試劇本
   
   scenes:
     - id: greeting
       triggers:
         - type: keyword
           keywords: ["你好", "hello", "hi"]
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
   ```
4. 點擊「保存」

**通過 API**:
```bash
curl -X POST http://localhost:8000/api/v1/group-ai/scripts/ \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test_script",
    "name": "測試劇本",
    "version": "1.0",
    "yaml_content": "script_id: test_script\nversion: 1.0\nscenes:\n  - id: greeting\n    triggers:\n      - type: keyword\n        keywords: [\"你好\", \"hello\"]\n    responses:\n      - template: \"你好！很高興認識你\""
  }'
```

#### 1.2 添加帳號

**前提**: 確保 `sessions/` 目錄下有有效的 `.session` 文件

**通過前端**:
1. 訪問 `http://localhost:3000/group-ai/accounts`
2. 點擊「添加賬號」
3. 填寫帳號信息：
   - 賬號 ID: `test_account_001`
   - Session 文件: `sessions/你的session文件名.session`
   - 劇本 ID: `test_script`
   - 群組 ID（可選）: `-1001234567890`
4. 點擊「保存」

**通過 API**:
```bash
curl -X POST http://localhost:8000/api/v1/group-ai/accounts/ \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "test_account_001",
    "session_file": "sessions/你的session文件名.session",
    "script_id": "test_script",
    "group_ids": [-1001234567890]
  }'
```

#### 1.3 啟動帳號

**通過前端**:
1. 在帳號列表中，找到 `test_account_001`
2. 點擊「啟動」按鈕
3. 等待幾秒鐘，狀態應該變為 `ONLINE`

**通過 API**:
```bash
curl -X POST http://localhost:8000/api/v1/group-ai/accounts/test_account_001/start
```

**驗證**:
- 檢查帳號狀態是否為 `ONLINE`
- 查看日誌確認劇本引擎和對話管理器已初始化
- 確認會話池已啟動消息監聽

#### 1.4 測試群組聊天

1. 在指定的 Telegram 群組中發送消息（例如："你好"）
2. 檢查帳號是否自動回復
3. 查看日誌確認消息處理流程：
   - 消息接收
   - 劇本匹配
   - 回復生成
   - 消息發送

---

### 階段 2: 角色分配功能測試

#### 2.1 創建多角色劇本

**通過前端**:
1. 訪問 `http://localhost:3000/group-ai/scripts`
2. 創建新劇本，YAML 內容包含角色定義：
   ```yaml
   script_id: multi_role_script
   version: 1.0
   description: 多角色劇本
   
   metadata:
     roles:
       - id: narrator
         name: "旁白"
       - id: character_a
         name: "角色A"
       - id: character_b
         name: "角色B"
   
   scenes:
     - id: opening
       metadata:
         role: narrator
       triggers:
         - type: message
       responses:
         - template: "歡迎來到這個故事..."
           metadata:
             role: narrator
     
     - id: dialogue_a
       metadata:
         role: character_a
       triggers:
         - type: keyword
           keywords: ["問題A"]
       responses:
         - template: "這是角色A的回答"
           metadata:
             role: character_a
     
     - id: dialogue_b
       metadata:
         role: character_b
       triggers:
         - type: keyword
           keywords: ["問題B"]
       responses:
         - template: "這是角色B的回答"
           metadata:
             role: character_b
   ```

#### 2.2 提取角色

**通過前端**:
1. 訪問 `http://localhost:3000/group-ai/role-assignments`
2. 在「提取角色」標籤頁：
   - 選擇劇本 `multi_role_script`
   - 點擊「提取角色」
3. 驗證：應該看到 3 個角色（narrator, character_a, character_b）

**通過 API**:
```bash
curl -X POST http://localhost:8000/api/v1/group-ai/role-assignments/extract-roles \
  -H "Content-Type: application/json" \
  -d '{"script_id": "multi_role_script"}'
```

#### 2.3 創建分配方案（自動分配）

**測試場景 1: 角色數 ≤ 帳號數（5個角色，10個帳號）**

**通過前端**:
1. 切換到「分配方案」標籤頁
2. 選擇 10 個帳號
3. 選擇「自動分配」模式
4. 點擊「創建分配方案」
5. 驗證：應該看到前 5 個帳號各分配 1 個角色

**通過 API**:
```bash
curl -X POST http://localhost:8000/api/v1/group-ai/role-assignments/create-assignment \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "multi_role_script",
    "account_ids": ["account_001", "account_002", "account_003", "account_004", "account_005", "account_006", "account_007", "account_008", "account_009", "account_010"],
    "mode": "auto"
  }'
```

**測試場景 2: 角色數 > 帳號數（5個角色，3個帳號）**

**通過前端**:
1. 選擇 3 個帳號
2. 選擇「自動分配」模式
3. 點擊「創建分配方案」
4. 驗證：應該看到負載均衡分配，每個帳號承擔約 1.67 個角色的負載

#### 2.4 創建分配方案（手動分配）

**通過前端**:
1. 選擇帳號
2. 選擇「手動分配」模式
3. 為每個角色手動選擇帳號
4. 點擊「創建分配方案」
5. 驗證：分配方案應該符合手動選擇

#### 2.5 審查並應用分配方案

**通過前端**:
1. 切換到「審查方案」標籤頁
2. 查看分配方案詳情：
   - 驗證結果（應該顯示「方案有效」）
   - 角色分配列表
   - 帳號負載統計
3. 點擊「應用分配方案」
4. 驗證：帳號配置應該已更新

**通過 API**:
```bash
curl -X POST "http://localhost:8000/api/v1/group-ai/role-assignments/apply-assignment?script_id=multi_role_script" \
  -H "Content-Type: application/json" \
  -d '{
    "narrator": "account_001",
    "character_a": "account_002",
    "character_b": "account_003"
  }'
```

---

## 測試檢查清單

### 劇本和帳號聊天功能
- [ ] 可以創建劇本
- [ ] 可以添加帳號
- [ ] 可以啟動帳號
- [ ] 帳號啟動時自動加載劇本
- [ ] 帳號啟動時自動初始化劇本引擎
- [ ] 帳號啟動時自動初始化對話管理器
- [ ] 會話池正確監聽群組消息
- [ ] 帳號能根據劇本自動回復群組消息

### 角色分配功能
- [ ] 可以從劇本中提取角色
- [ ] 角色統計正確（台詞數量、權重）
- [ ] 自動分配算法正確（角色數≤帳號數）
- [ ] 自動分配算法正確（角色數>帳號數）
- [ ] 手動分配功能正常
- [ ] 分配方案驗證正確
- [ ] 可以應用分配方案
- [ ] 帳號配置正確更新

---

## 常見問題排查

### 問題 1: 帳號無法啟動

**檢查**:
- Session 文件是否存在且有效
- API_ID 和 API_HASH 是否正確配置
- 查看後端日誌中的錯誤信息

### 問題 2: 帳號無法回復消息

**檢查**:
- 帳號是否已啟動（狀態為 ONLINE）
- 劇本是否正確加載
- 群組 ID 是否正確配置
- 查看對話管理器日誌

### 問題 3: 無法提取角色

**檢查**:
- 劇本是否包含角色定義（metadata.roles 或場景/回復的 metadata.role）
- 劇本格式是否正確
- 查看後端日誌中的錯誤信息

### 問題 4: 分配方案驗證失敗

**檢查**:
- 是否有角色未分配
- 負載是否過於不均衡
- 查看驗證錯誤信息

---

## 測試報告模板

```
測試日期: YYYY-MM-DD
測試人員: [姓名]

### 測試結果

#### 劇本和帳號聊天功能
- 創建劇本: ✅/❌
- 添加帳號: ✅/❌
- 啟動帳號: ✅/❌
- 自動回復: ✅/❌

#### 角色分配功能
- 提取角色: ✅/❌
- 自動分配: ✅/❌
- 手動分配: ✅/❌
- 應用方案: ✅/❌

### 發現的問題
1. [問題描述]
2. [問題描述]

### 建議改進
1. [改進建議]
2. [改進建議]
```

---

**最後更新**: 2025-01-07

