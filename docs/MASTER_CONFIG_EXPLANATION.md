# master_config.json 详细说明

## 📋 文件作用概述

`data/master_config.json` 是**主节点（Master Node）管理多个工作节点（Worker Nodes）的核心配置文件**。

这个文件定义了：
- 所有工作节点的连接信息（IP、用户名、密码）
- 每个节点的容量限制（最多运行多少个Telegram账号）
- 账号分配策略（如何将账号分配到不同节点）

---

## 🏗️ 系统架构

### 主从架构（Master-Worker）

```
┌─────────────────────────────────────────────────┐
│           主节点 (Master Node)                    │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  后端 API    │  │   前端 UI    │            │
│  │  (FastAPI)   │  │  (Next.js)   │            │
│  └──────────────┘  └──────────────┘            │
│                                                  │
│  管理所有账号、分配任务、监控状态                  │
│  ┌──────────────────────────────────────┐      │
│  │   master_config.json                  │      │
│  │   (配置文件，定义所有工作节点)          │      │
│  └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────┘
                    │
                    │ SSH连接
                    │ 分配账号
                    │ 监控状态
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│ Worker-01 │ │LosAngeles │ │  Manila   │
│           │ │           │ │           │
│ 运行账号1 │ │ 运行账号2 │ │ 运行账号3 │
│ 运行账号2 │ │ 运行账号3 │ │ 运行账号4 │
│ 运行账号3 │ │ 运行账号4 │ │ 运行账号5 │
│ ...       │ │ ...       │ │ ...       │
│ (最多5个) │ │ (最多5个) │ │ (最多5个) │
└───────────┘ └───────────┘ └───────────┘
```

---

## 🎯 为什么需要配置其他机器的IP？

### 1. **分布式运行 Telegram 账号**

**问题：** 如果所有账号都在一台服务器上运行：
- ❌ 容易被Telegram检测（同一IP大量账号）
- ❌ 单点故障（服务器挂了所有账号都停）
- ❌ 资源限制（一台服务器性能有限）

**解决方案：** 将账号分散到多台服务器：
- ✅ 不同IP地址，降低被检测风险
- ✅ 负载均衡，单台服务器故障不影响全部
- ✅ 可以扩展到更多服务器

### 2. **主节点需要连接工作节点**

主节点需要：
- **上传 Session 文件**：当你注册新账号后，主节点通过SSH将`.session`文件上传到工作节点
- **启动/停止账号**：通过SSH在工作节点上启动或停止Telegram账号进程
- **监控状态**：定期检查工作节点上的账号是否正常运行
- **查看日志**：获取工作节点的运行日志

**所有这些操作都需要SSH连接到工作节点，所以必须知道工作节点的IP地址！**

---

## 📝 配置文件结构详解

```json
{
  "servers": {
    "worker-01": {                    // 节点ID（唯一标识）
      "host": "165.154.254.99",      // ⚠️ 工作节点的IP地址（必须正确！）
      "user": "ubuntu",               // SSH用户名
      "password": "Along2025!!!",     // SSH密码
      "node_id": "worker-01",        // 节点ID（与key相同）
      "deploy_dir": "/home/ubuntu",  // 工作节点上的项目目录
      "max_accounts": 5,             // 该节点最多运行5个账号
      "location": "LosAngeles",      // 地理位置（用于分配策略）
      "telegram_api_id": "",          // Telegram API ID（可选）
      "telegram_api_hash": "",        // Telegram API Hash（可选）
      "openai_api_key": ""            // OpenAI API Key（可选）
    },
    "los-angeles": { ... },          // 第二个工作节点
    "manila": { ... }                // 第三个工作节点
  },
  "allocation": {                     // 账号分配策略配置
    "default_strategy": "load_balance",  // 默认策略：负载均衡
    "rebalance_threshold": 30.0,         // 重新平衡阈值（%）
    "health_check_interval": 60,         // 健康检查间隔（秒）
    "max_retry_count": 3,                // 最大重试次数
    "retry_delay": 5                     // 重试延迟（秒）
  }
}
```

---

## 🔄 工作流程示例

### 场景：注册新账号并分配到工作节点

1. **用户在Web界面注册账号**
   ```
   用户在前端输入手机号 → 后端API接收请求
   ```

2. **后端查找可用工作节点**
   ```
   读取 master_config.json
   → 检查每个节点的当前账号数
   → 选择账号数 < max_accounts 的节点
   → 使用负载均衡算法选择最优节点
   ```

3. **上传Session文件到工作节点**
   ```
   主节点通过SSH连接到工作节点（使用配置的IP、用户名、密码）
   → 上传 .session 文件到工作节点的 deploy_dir/sessions/
   ```

4. **在工作节点上启动账号**
   ```
   主节点通过SSH执行命令
   → 在工作节点上启动Python进程运行Telegram账号
   ```

5. **持续监控**
   ```
   主节点定期通过SSH检查工作节点状态
   → 账号是否在运行？
   → 进程是否正常？
   → 是否需要重启？
   ```

---

## 🔍 代码中的使用位置

### 1. 服务器列表显示
**文件：** `admin-backend/app/api/group_ai/servers.py`
```python
def load_server_configs() -> Dict:
    """加载服务器配置"""
    config_path = get_master_config_path()  # 读取 master_config.json
    # ... 返回所有服务器配置
```

**用途：** 前端显示所有工作节点及其状态

### 2. 账号自动分配
**文件：** `admin-backend/app/core/intelligent_allocator.py`
```python
class IntelligentAllocator:
    def __init__(self, master_config_path: Optional[Path] = None):
        # 加载 master_config.json
        # 根据配置选择最优工作节点
```

**用途：** 创建新账号时，自动选择合适的工作节点

### 3. Session文件上传
**文件：** `admin-backend/app/api/group_ai/session_uploader.py`
```python
class SessionUploader:
    def __init__(self, master_config_path: Optional[Path] = None):
        # 加载 master_config.json
        # 通过SSH上传session文件到工作节点
```

**用途：** 将账号的session文件上传到对应的工作节点

### 4. 远程启动账号
**文件：** `admin-backend/app/api/group_ai/accounts.py`
```python
async def start_account_on_server(account_id: str, server_id: str, db: Session):
    # 从 master_config.json 读取服务器配置
    # 通过SSH连接到工作节点
    # 在工作节点上启动账号进程
```

**用途：** 在指定工作节点上启动Telegram账号

---

## ⚠️ 常见问题

### Q1: 为什么IP地址必须是正确的？

**A:** 如果IP错误，主节点无法连接到工作节点，导致：
- ❌ 无法上传session文件
- ❌ 无法启动账号
- ❌ 无法监控状态
- ❌ 前端显示"连接失败"

### Q2: 可以只配置一台工作节点吗？

**A:** 可以！但建议至少2-3台：
- 单台节点：所有账号都在一台服务器，风险较高
- 多台节点：负载分散，更安全稳定

### Q3: 工作节点需要安装什么？

**A:** 工作节点需要：
- Python 3.8+
- `group_ai_service` 代码（从主节点部署）
- 网络连接到Telegram服务器

### Q4: 主节点和工作节点可以是同一台服务器吗？

**A:** 可以！但建议分开：
- **同一台：** 适合测试或小规模使用
- **分开：** 适合生产环境，更安全稳定

---

## 📊 配置示例

### 单节点配置（测试用）
```json
{
  "servers": {
    "local": {
      "host": "127.0.0.1",
      "user": "ubuntu",
      "password": "your_password",
      "node_id": "local",
      "deploy_dir": "/home/ubuntu/telegram-ai-system",
      "max_accounts": 10,
      "location": "Local"
    }
  }
}
```

### 多节点配置（生产用）
```json
{
  "servers": {
    "worker-01": {
      "host": "10.11.75.103",      // ⚠️ 必须是实际IP
      "user": "ubuntu",
      "password": "password1",
      "max_accounts": 5,
      "location": "LosAngeles"
    },
    "worker-02": {
      "host": "10.11.75.104",      // ⚠️ 必须是实际IP
      "user": "ubuntu",
      "password": "password2",
      "max_accounts": 5,
      "location": "Manila"
    }
  }
}
```

---

## 🛠️ 如何更新配置

### 方法1: 直接编辑文件
```bash
# 编辑配置文件
nano data/master_config.json
# 或
vim data/master_config.json
```

### 方法2: 使用检测工具
```bash
# 自动检测IP并更新
python scripts/server/update-server-ips.py
```

### 方法3: 通过前端（如果实现了）
在Web界面的"节点管理"页面直接编辑

---

## ✅ 总结

**`master_config.json` 的作用：**
1. 📍 **定义工作节点位置**：告诉主节点有哪些工作节点，如何连接它们
2. 🔄 **账号分配依据**：根据节点容量和负载，智能分配账号
3. 🔌 **SSH连接凭证**：提供IP、用户名、密码，用于远程操作
4. 📊 **监控配置**：定义健康检查间隔、重试策略等

**为什么需要其他机器的IP：**
- 主节点需要通过SSH连接到工作节点
- 上传文件、启动进程、监控状态都需要网络连接
- IP错误 = 无法连接 = 系统无法工作

**关键点：**
- ✅ IP地址必须是**实际可访问**的IP
- ✅ 确保主节点可以SSH连接到工作节点
- ✅ 定期检查连接状态，及时更新错误的IP

