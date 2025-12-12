# master_config.json 字段详细说明

## 📝 配置文件结构

```json
{
  "servers": {
    "节点ID": { ... },
    "los-angeles": { ... },
    "manila": { ... }
  },
  "allocation": { ... }
}
```

---

## 🔑 字段作用详解

### 1. `"los-angeles"` 和 `"manila"` 的作用

#### 什么是节点ID？

`"los-angeles"` 和 `"manila"` 是**工作节点的唯一标识符（Node ID）**。

**作用：**
- ✅ **唯一标识**：区分不同的工作节点
- ✅ **数据库关联**：账号记录中会存储 `server_id`，指向这个节点ID
- ✅ **前端显示**：在Web界面中显示节点名称
- ✅ **API调用**：通过节点ID操作特定节点（启动、停止、查看状态）

**示例：**
```json
{
  "los-angeles": {  // ← 这是节点ID
    "host": "165.154.235.170",
    "node_id": "los-angeles",  // ← 内部也存储节点ID
    ...
  }
}
```

**使用场景：**
- 前端显示："账号已分配到 los-angeles 节点"
- API调用：`GET /api/v1/group-ai/servers/los-angeles` 获取该节点状态
- 数据库：`account.server_id = "los-angeles"` 记录账号所属节点

---

### 2. `"location"` 字段的作用

#### 什么是地理位置？

`"location"` 是**服务器的地理位置标识**，用于**地理位置分配策略**。

**作用：**
- ✅ **地理位置策略**：优先将账号分配到相同地理位置的服务器
- ✅ **延迟优化**：选择地理位置相近的服务器，降低延迟
- ✅ **合规性**：某些地区可能有合规要求，需要特定地理位置

**示例：**
```json
{
  "los-angeles": {
    "location": "LosAngeles",  // ← 地理位置：洛杉矶
    ...
  },
  "manila": {
    "location": "Manila",      // ← 地理位置：马尼拉
    ...
  }
}
```

**分配策略示例：**
```
场景：注册一个账号，指定 account_location = "LosAngeles"

系统行为：
1. 查找所有 location = "LosAngeles" 的服务器
2. 在这些服务器中选择负载最轻的
3. 如果没有相同位置的，则使用负载均衡策略
```

**代码中的使用：**
```python
# admin-backend/app/core/load_balancer.py
def _select_by_location(self, servers, account_location):
    # 优先选择相同位置的服务器
    same_location_servers = [s for s in servers if s.location == account_location]
    if same_location_servers:
        return self._select_by_load_balance(same_location_servers)
```

---

### 3. `"allocation"` 的作用

#### 什么是分配策略配置？

`"allocation"` 定义了**账号如何分配到工作节点的策略和参数**。

**作用：**
- ✅ **默认策略**：定义默认的分配算法
- ✅ **健康检查**：定义多久检查一次服务器状态
- ✅ **故障恢复**：定义故障检测和恢复机制
- ✅ **账号类型策略**：不同类型的账号使用不同的分配策略

**配置结构：**
```json
{
  "allocation": {
    "default_strategy": "load_balance",      // 默认分配策略
    "rebalance_threshold": 30.0,             // 重新平衡阈值
    "health_check_interval": 60,             // 健康检查间隔（秒）
    "max_retry_count": 3,                    // 最大重试次数
    "retry_delay": 5,                        // 重试延迟（秒）
    "fault_recovery": {                      // 故障恢复配置
      "enabled": true,
      "check_interval": 300,                 // 检查间隔（秒）
      "failure_threshold": 3                 // 故障阈值
    },
    "account_type_strategies": {            // 账号类型策略
      "default": "load_balance",             // 默认策略
      "high_priority": "location",           // 高优先级账号使用地理位置策略
      "batch": "affinity"                    // 批量账号使用亲和性策略
    }
  }
}
```

#### 字段详解

##### `default_strategy`
**可选值：**
- `"load_balance"`：负载均衡（默认）- 选择负载最轻的服务器
- `"location"`：地理位置策略 - 优先选择相同地理位置的服务器
- `"affinity"`：亲和性策略 - 优先选择已有相同剧本的服务器
- `"isolation"`：隔离策略 - 每个账号独立服务器

**示例：**
```json
"default_strategy": "load_balance"
```
→ 新账号默认使用负载均衡策略分配

---

##### `rebalance_threshold`
**作用：** 当服务器负载差异超过这个百分比时，触发重新平衡

**示例：**
```json
"rebalance_threshold": 30.0
```
→ 如果服务器A负载80%，服务器B负载50%，差异30%，触发重新平衡

---

##### `health_check_interval`
**作用：** 每隔多少秒检查一次服务器健康状态

**示例：**
```json
"health_check_interval": 60
```
→ 每60秒检查一次服务器是否在线、账号是否正常运行

---

##### `max_retry_count` 和 `retry_delay`
**作用：** 分配失败时的重试机制

**示例：**
```json
"max_retry_count": 3,
"retry_delay": 5
```
→ 如果分配失败，最多重试3次，每次间隔5秒

---

##### `fault_recovery`
**作用：** 故障检测和自动恢复配置

**示例：**
```json
"fault_recovery": {
  "enabled": true,
  "check_interval": 300,      // 每5分钟检查一次
  "failure_threshold": 3       // 连续失败3次判定为故障
}
```
→ 如果服务器连续3次健康检查失败，标记为故障，自动迁移账号

---

##### `account_type_strategies`
**作用：** 不同类型的账号使用不同的分配策略

**示例：**
```json
"account_type_strategies": {
  "default": "load_balance",        // 普通账号：负载均衡
  "high_priority": "location",      // 高优先级账号：地理位置策略
  "batch": "affinity"               // 批量账号：亲和性策略（相同剧本放一起）
}
```

**使用场景：**
- **高优先级账号**：使用地理位置策略，选择最近的服务器，降低延迟
- **批量账号**：使用亲和性策略，相同剧本的账号放在同一服务器，便于管理

---

## 🎯 实际应用示例

### 示例1：注册新账号

```json
配置：
{
  "allocation": {
    "default_strategy": "load_balance"
  }
}

流程：
1. 用户注册账号
2. 系统读取 default_strategy = "load_balance"
3. 检查所有服务器负载
4. 选择负载最轻的服务器（例如：los-angeles）
5. 将账号分配到 los-angeles 节点
```

---

### 示例2：高优先级账号

```json
配置：
{
  "allocation": {
    "account_type_strategies": {
      "high_priority": "location"
    }
  }
}

流程：
1. 用户注册账号，标记为 high_priority
2. 系统读取 high_priority 策略 = "location"
3. 查找 location = "LosAngeles" 的服务器
4. 在这些服务器中选择负载最轻的
5. 分配到对应节点
```

---

### 示例3：故障恢复

```json
配置：
{
  "allocation": {
    "fault_recovery": {
      "enabled": true,
      "check_interval": 300,
      "failure_threshold": 3
    }
  }
}

流程：
1. 系统每5分钟检查一次服务器健康状态
2. 如果 los-angeles 节点连续3次检查失败
3. 标记为故障节点
4. 自动将该节点上的账号迁移到其他正常节点
```

---

## 📊 总结对比

| 字段 | 作用 | 示例值 | 是否必需 |
|------|------|--------|----------|
| **节点ID** (`"los-angeles"`) | 唯一标识工作节点 | `"los-angeles"`, `"manila"` | ✅ 必需 |
| **location** | 地理位置，用于分配策略 | `"LosAngeles"`, `"Manila"` | ⚠️ 可选（地理位置策略需要） |
| **allocation** | 分配策略配置 | 见上方配置 | ✅ 必需 |

---

## 🔧 如何修改

### 修改节点ID
```json
// 将 "los-angeles" 改为 "la-node-01"
"la-node-01": {
  "node_id": "la-node-01",  // 同时修改这里
  ...
}
```

### 修改地理位置
```json
"los-angeles": {
  "location": "LosAngeles",  // 改为 "NewYork" 或其他
  ...
}
```

### 修改分配策略
```json
"allocation": {
  "default_strategy": "location",  // 改为 "affinity" 或其他
  ...
}
```

---

## ⚠️ 注意事项

1. **节点ID必须唯一**：不能有两个节点使用相同的ID
2. **location可以重复**：多个节点可以有相同的地理位置
3. **allocation是全局配置**：影响所有账号的分配行为
4. **修改后需要重启服务**：某些配置修改后需要重启后端服务才能生效

