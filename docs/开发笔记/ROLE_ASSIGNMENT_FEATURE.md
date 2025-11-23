# 劇本角色與帳號自動分配管理功能

> **更新日期**: 2025-01-07  
> **狀態**: ✅ 已完成

---

## 功能概述

實現了劇本角色與帳號的自動分配管理功能，支持：
- 自動從劇本中提取角色列表
- 統計每個角色的台詞數量和工作負載
- 智能分配算法（支持角色數≤帳號數和角色數>帳號數兩種情況）
- 手動分配功能，支持管理員調整分配方案
- 分配方案驗證和摘要

---

## 核心功能

### 1. 角色提取 (RoleExtractor)

**文件**: `group_ai_service/role_assigner.py`

**功能**:
- 從劇本的 `metadata.roles` 中提取角色定義
- 從場景的 `metadata.role` 中提取角色
- 從回復的 `metadata.role` 中提取角色
- 統計每個角色的台詞數量和權重

**角色定義格式**:

在劇本的 YAML 文件中，可以通過以下方式定義角色：

```yaml
script_id: multi_role_script
version: 1.0

metadata:
  roles:
    - id: role_1
      name: "角色1"
    - id: role_2
      name: "角色2"

scenes:
  - id: scene_1
    metadata:
      role: role_1  # 場景級別的角色
    responses:
      - template: "這是角色1的台詞"
        metadata:
          role: role_1  # 回復級別的角色
```

### 2. 自動分配算法 (RoleAssigner)

**分配策略**:

#### 情況1: 角色數 ≤ 帳號數
- 一對一分配：每個角色分配給一個帳號
- 按台詞權重排序，權重大的角色優先分配

#### 情況2: 角色數 > 帳號數
- 負載均衡分配：按台詞權重將角色分配給帳號
- 計算總權重和每個帳號的平均負載
- 確保負載盡可能均衡

**權重計算**:
- 普通回復：權重 = 1.0
- AI 生成回復：權重 = 1.5（因為需要更多計算資源）

### 3. 手動分配

支持管理員手動指定角色與帳號的對應關係：
- 部分角色手動分配，剩餘角色自動分配
- 完全手動分配

### 4. 分配方案驗證

驗證分配方案的完整性：
- 檢查是否有角色未分配
- 檢查負載是否均衡（差異不超過50%）

---

## API 端點

### 1. 提取角色

```http
POST /api/v1/group-ai/role-assignments/extract-roles
Content-Type: application/json

{
  "script_id": "daily_chat"
}
```

**響應**:
```json
{
  "script_id": "daily_chat",
  "roles": [
    {
      "role_id": "role_1",
      "role_name": "角色1",
      "dialogue_count": 10,
      "dialogue_weight": 12.5,
      "metadata": {}
    }
  ],
  "total_roles": 1
}
```

### 2. 創建分配方案

```http
POST /api/v1/group-ai/role-assignments/create-assignment
Content-Type: application/json

{
  "script_id": "daily_chat",
  "account_ids": ["account_001", "account_002"],
  "mode": "auto",  // 或 "manual"
  "manual_assignments": {  // 僅在 mode="manual" 時需要
    "role_1": "account_001"
  }
}
```

**響應**:
```json
{
  "script_id": "daily_chat",
  "assignments": [
    {
      "role_id": "role_1",
      "account_id": "account_001",
      "weight": 12.5,
      "role_name": "角色1"
    }
  ],
  "summary": {
    "script_id": "daily_chat",
    "total_roles": 1,
    "total_accounts": 2,
    "assignment_mode": "auto",
    "account_assignments": {
      "account_001": {
        "roles": [
          {
            "role_id": "role_1",
            "role_name": "角色1",
            "weight": 12.5
          }
        ],
        "total_weight": 12.5
      }
    },
    "role_statistics": {
      "role_1": {
        "name": "角色1",
        "dialogue_count": 10,
        "weight": 12.5
      }
    }
  },
  "validation": {
    "is_valid": true,
    "errors": []
  }
}
```

### 3. 應用分配方案

```http
POST /api/v1/group-ai/role-assignments/apply-assignment?script_id=daily_chat
Content-Type: application/json

{
  "role_1": "account_001",
  "role_2": "account_002"
}
```

**響應**:
```json
{
  "message": "成功應用分配方案，已更新 2 個帳號",
  "applied_count": 2
}
```

---

## 使用示例

### 示例1: 5個角色，10個帳號

```python
# 自動分配：一對一分配
assignments = {
    "role_1": "account_001",
    "role_2": "account_002",
    "role_3": "account_003",
    "role_4": "account_004",
    "role_5": "account_005"
}
# 剩餘5個帳號未使用
```

### 示例2: 5個角色，3個帳號

```python
# 自動分配：負載均衡
assignments = {
    "role_1": "account_001",  # 負載: 4.0
    "role_2": "account_001",  # 負載: 4.0
    "role_3": "account_002",  # 負載: 4.0
    "role_4": "account_002",  # 負載: 4.0
    "role_5": "account_003"   # 負載: 4.0
}
# 每個帳號承擔約 1.67 個角色的負載
```

---

## 劇本格式擴展

為了支持角色分配，劇本格式可以擴展為：

```yaml
script_id: multi_role_script
version: 1.0
description: 多角色劇本示例

metadata:
  roles:
    - id: narrator
      name: "旁白"
      description: "負責敘述和引導"
    - id: character_a
      name: "角色A"
      description: "主要角色之一"
    - id: character_b
      name: "角色B"
      description: "主要角色之一"

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

---

## 相關文件

- `group_ai_service/role_assigner.py` - 角色分配器核心實現
- `admin-backend/app/api/group_ai/role_assignments.py` - 角色分配 API
- `docs/ROLE_ASSIGNMENT_FEATURE.md` - 本文檔

---

## 後續改進建議

1. **前端界面**: 創建可視化的角色分配管理界面
2. **負載監控**: 實時監控每個帳號的實際負載
3. **動態調整**: 支持運行時動態調整角色分配
4. **角色優先級**: 支持為角色設置優先級
5. **分配歷史**: 記錄分配方案的歷史記錄
6. **批量操作**: 支持批量應用分配方案

---

**最後更新**: 2025-01-07

