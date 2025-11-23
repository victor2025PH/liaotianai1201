# 智能分配Session帐号至服务器系统设计文档

## 1. 系统架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     主控制节点 (Master Node)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  前端管理界面 │  │  后端API服务 │  │  智能分配引擎 │      │
│  │  (Next.js)   │  │  (FastAPI)   │  │ (Allocator)   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  数据库 (SQLite) │                        │
│                    │  - 账号信息      │                        │
│                    │  - 服务器状态    │                        │
│                    │  - 分配记录      │                        │
│                    └─────────────────┘                        │
└────────────────────────────┬─────────────────────────────────┘
                              │
                              │ SSH/SFTP
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌──────▼────────┐
│  工作节点 1    │   │   工作节点 2     │   │   工作节点 3   │
│ (worker-01)   │   │  (los-angeles)   │   │   (manila)     │
│               │   │                  │   │                │
│ ┌──────────┐ │   │ ┌──────────┐    │   │ ┌──────────┐  │
│ │Session文件│ │   │ │Session文件│    │   │ │Session文件│  │
│ │ 存储目录  │ │   │ │ 存储目录  │    │   │ │ 存储目录  │  │
│ └────┬─────┘ │   │ └────┬─────┘    │   │ └────┬─────┘  │
│      │       │   │      │          │   │      │        │
│ ┌────▼─────┐ │   │ ┌────▼─────┐    │   │ ┌────▼─────┐  │
│ │账号实例  │ │   │ │账号实例   │    │   │ │账号实例   │  │
│ │- Telegram│ │   │ │- Telegram │    │   │ │- Telegram │  │
│ │- 剧本引擎│ │   │ │- 剧本引擎 │    │   │ │- 剧本引擎 │  │
│ │- 对话管理│ │   │ │- 对话管理 │    │   │ │- 对话管理 │  │
│ └──────────┘ │   │ └──────────┘    │   │ └──────────┘  │
│               │   │                  │   │                │
│ 最大账号数: 5 │   │ 最大账号数: 5    │   │ 最大账号数: 5  │
└───────────────┘   └──────────────────┘   └────────────────┘
```

### 1.2 核心组件

#### 1.2.1 智能分配引擎 (Intelligent Allocator)

**位置**: `admin-backend/app/core/intelligent_allocator.py`

**职责**:
- 实时监控所有服务器状态（CPU、内存、磁盘、账号数量）
- 计算服务器负载分数
- 执行智能分配算法
- 记录分配历史，支持重新分配

**核心类**:
```python
class IntelligentAllocator:
    """智能分配引擎"""
    
    def __init__(self):
        self.server_monitor = ServerMonitor()
        self.allocation_history = AllocationHistory()
        self.load_balancer = LoadBalancer()
    
    async def allocate_account(
        self, 
        account_id: str, 
        session_file: str,
        script_id: Optional[str] = None
    ) -> AllocationResult:
        """分配账号到最优服务器"""
        pass
    
    async def rebalance_accounts(self) -> RebalanceResult:
        """重新平衡账号分布"""
        pass
```

#### 1.2.2 服务器监控器 (Server Monitor)

**位置**: `admin-backend/app/core/server_monitor.py`

**职责**:
- 定期检查服务器健康状态
- 收集服务器资源使用情况
- 检测服务器故障并触发告警
- 维护服务器状态缓存

**监控指标**:
- CPU使用率
- 内存使用率
- 磁盘使用率
- 网络延迟
- 账号数量
- 服务状态（systemd）

#### 1.2.3 负载均衡器 (Load Balancer)

**位置**: `admin-backend/app/core/load_balancer.py`

**职责**:
- 计算服务器负载分数
- 实现多种负载均衡策略
- 支持权重配置
- 处理服务器故障转移

**负载计算算法**:
```python
def calculate_load_score(server: ServerNode) -> float:
    """计算服务器负载分数（0-100，越低越好）"""
    cpu_weight = 0.3
    memory_weight = 0.3
    account_weight = 0.3
    disk_weight = 0.1
    
    cpu_score = server.cpu_usage
    memory_score = server.memory_usage
    account_score = (server.current_accounts / server.max_accounts) * 100
    disk_score = server.disk_usage
    
    total_score = (
        cpu_score * cpu_weight +
        memory_score * memory_weight +
        account_score * account_weight +
        disk_score * disk_weight
    )
    
    return total_score
```

## 2. 智能分配策略

### 2.1 分配算法

#### 2.1.1 多因子评分算法

**评分因子**:
1. **负载因子** (40%): CPU、内存、磁盘使用率
2. **容量因子** (30%): 当前账号数 / 最大账号数
3. **响应因子** (20%): 网络延迟、SSH连接速度
4. **稳定性因子** (10%): 历史故障率、运行时长

**算法流程**:
```
1. 获取所有可用服务器列表
2. 过滤掉不可用服务器（状态 != active）
3. 过滤掉已满服务器（current_accounts >= max_accounts）
4. 对每个服务器计算综合评分
5. 选择评分最低（负载最轻）的服务器
6. 执行分配操作（上传Session文件）
7. 更新服务器状态和分配记录
```

#### 2.1.2 分配策略类型

**策略1: 负载均衡策略（默认）**
- 优先选择负载最轻的服务器
- 确保所有服务器负载均匀分布
- 适用于大多数场景

**策略2: 地理位置策略**
- 根据账号的地理位置选择最近的服务器
- 降低网络延迟
- 适用于对延迟敏感的场景

**策略3: 剧本亲和性策略**
- 相同剧本的账号尽量分配到同一服务器
- 减少剧本文件重复加载
- 适用于剧本数量较少的场景

**策略4: 故障隔离策略**
- 避免将新账号分配到最近故障的服务器
- 提高系统稳定性
- 适用于高可用性要求

### 2.2 重新分配机制

#### 2.2.1 自动重新分配触发条件

1. **服务器故障**: 服务器连续3次健康检查失败
2. **负载不均衡**: 服务器间负载差异超过30%
3. **容量超限**: 服务器账号数超过最大限制
4. **性能下降**: 服务器响应时间超过阈值（2秒）

#### 2.2.2 重新分配流程

```
1. 检测触发条件
2. 识别需要迁移的账号
3. 选择目标服务器
4. 执行迁移操作：
   - 停止账号服务
   - 上传Session文件到新服务器
   - 更新数据库记录
   - 在新服务器启动账号
5. 验证迁移结果
6. 记录迁移日志
```

## 3. 剧本聊天功能实现

### 3.1 账号启动流程

```
┌─────────────────┐
│  创建账号请求   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 智能分配引擎     │
│ 选择最优服务器   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 上传Session文件  │
│ 到目标服务器     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 初始化账号服务   │
│ - 加载剧本       │
│ - 初始化剧本引擎 │
│ - 初始化对话管理 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 启动Telegram连接│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 启动消息监听     │
│ 开始剧本聊天     │
└─────────────────┘
```

### 3.2 剧本加载机制

**位置**: `group_ai_service/service_manager.py`

**流程**:
1. 从数据库获取剧本YAML内容
2. 使用`ScriptParser`解析YAML
3. 创建`ScriptEngine`实例
4. 为账号创建剧本状态（`ScriptState`）
5. 注册场景触发器和响应处理器

**代码示例**:
```python
async def initialize_account_services(
    self,
    account_id: str,
    account_config: AccountConfig,
    script_yaml_content: Optional[str] = None
) -> bool:
    """初始化账号服务（剧本引擎和对话管理器）"""
    # 1. 获取剧本
    script = await self.get_script(
        account_config.script_id,
        script_yaml_content
    )
    if not script:
        return False
    
    # 2. 创建剧本引擎
    script_engine = ScriptEngine(script)
    script_state = script_engine.create_state(account_id)
    
    # 3. 创建对话管理器
    dialogue_manager = DialogueManager(
        script_engine=script_engine,
        script_state=script_state
    )
    
    # 4. 注册到账号实例
    account = self.account_manager.accounts[account_id]
    account.script_engine = script_engine
    account.dialogue_manager = dialogue_manager
    
    return True
```

### 3.3 群组消息处理流程

```
┌─────────────────┐
│ 接收群组消息     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 检查是否在监听   │
│ 的群组列表中     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 对话管理器处理   │
│ - 匹配场景触发器 │
│ - 选择响应模板   │
│ - 生成回复内容   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 发送回复消息     │
└─────────────────┘
```

### 3.4 对话管理器实现

**位置**: `group_ai_service/dialogue_manager.py`

**核心功能**:
- 场景匹配: 根据消息内容匹配剧本场景
- 角色选择: 根据场景配置选择发言角色
- 模板渲染: 使用模板引擎生成回复内容
- 状态管理: 维护对话上下文和状态

## 4. 技术实现细节

### 4.1 数据库设计

#### 4.1.1 账号表 (GroupAIAccount)

```sql
CREATE TABLE group_ai_accounts (
    account_id VARCHAR(255) PRIMARY KEY,
    session_file VARCHAR(500) NOT NULL,
    script_id VARCHAR(255),
    server_id VARCHAR(255),  -- 分配的服务器ID
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    -- 索引
    INDEX idx_server_id (server_id),
    INDEX idx_script_id (script_id),
    INDEX idx_status (status)
);
```

#### 4.1.2 服务器状态表 (ServerStatus)

```sql
CREATE TABLE server_status (
    node_id VARCHAR(255) PRIMARY KEY,
    host VARCHAR(255),
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    accounts_count INT,
    max_accounts INT,
    last_heartbeat TIMESTAMP,
    status VARCHAR(50),
    -- 索引
    INDEX idx_status (status),
    INDEX idx_last_heartbeat (last_heartbeat)
);
```

#### 4.1.3 分配记录表 (AllocationHistory)

```sql
CREATE TABLE allocation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id VARCHAR(255),
    server_id VARCHAR(255),
    allocation_type VARCHAR(50),  -- initial, rebalance, manual
    load_score FLOAT,
    created_at TIMESTAMP,
    -- 索引
    INDEX idx_account_id (account_id),
    INDEX idx_server_id (server_id),
    INDEX idx_created_at (created_at)
);
```

### 4.2 API接口设计

#### 4.2.1 账号分配接口

**POST** `/api/v1/group-ai/accounts/allocate`

**请求体**:
```json
{
    "account_id": "639277356598",
    "session_file": "sessions/639277356598.session",
    "script_id": "000新人欢迎剧本",
    "allocation_strategy": "load_balance"  // load_balance, location, affinity, isolation
}
```

**响应**:
```json
{
    "success": true,
    "server_id": "worker-01",
    "remote_path": "/home/ubuntu/sessions/639277356598.session",
    "load_score": 45.2,
    "message": "账号已成功分配到服务器 worker-01"
}
```

#### 4.2.2 重新分配接口

**POST** `/api/v1/group-ai/accounts/rebalance`

**请求体**:
```json
{
    "account_id": "639277356598",
    "target_server_id": "los-angeles",  // 可选，不指定则自动选择
    "reason": "server_overload"
}
```

#### 4.2.3 服务器状态查询接口

**GET** `/api/v1/group-ai/servers/{node_id}/status`

**响应**:
```json
{
    "node_id": "worker-01",
    "host": "165.154.254.99",
    "status": "online",
    "cpu_usage": 35.5,
    "memory_usage": 62.3,
    "disk_usage": 45.8,
    "accounts_count": 3,
    "max_accounts": 5,
    "load_score": 48.2,
    "last_heartbeat": "2025-01-20T10:30:00Z"
}
```

### 4.3 配置文件结构

#### 4.3.1 主配置文件 (master_config.json)

```json
{
    "servers": {
        "worker-01": {
            "host": "165.154.254.99",
            "user": "ubuntu",
            "password": "***",
            "node_id": "worker-01",
            "deploy_dir": "/home/ubuntu",
            "max_accounts": 5,
            "location": "LosAngeles",
            "weight": 1.0,
            "allocation_strategy": "load_balance",
            "health_check_interval": 60,
            "status": "active"
        }
    },
    "allocation": {
        "default_strategy": "load_balance",
        "rebalance_threshold": 30.0,
        "health_check_interval": 60,
        "max_retry_count": 3,
        "retry_delay": 5
    }
}
```

## 5. 测试方案

### 5.1 单元测试

#### 5.1.1 智能分配算法测试

**测试文件**: `admin-backend/tests/core/test_intelligent_allocator.py`

**测试用例**:
1. 测试负载均衡分配
2. 测试服务器容量限制
3. 测试故障服务器过滤
4. 测试重新分配逻辑
5. 测试负载分数计算

#### 5.1.2 服务器监控测试

**测试文件**: `admin-backend/tests/core/test_server_monitor.py`

**测试用例**:
1. 测试服务器健康检查
2. 测试资源使用率收集
3. 测试故障检测
4. 测试状态缓存更新

### 5.2 集成测试

#### 5.2.1 端到端分配测试

**测试场景**:
1. 创建新账号并自动分配
2. 验证Session文件上传
3. 验证账号启动
4. 验证剧本加载
5. 验证群组消息处理

**测试脚本**: `scripts/test_allocation_flow.py`

```python
async def test_complete_allocation_flow():
    """测试完整的分配流程"""
    # 1. 创建账号
    account = await create_account(
        account_id="test_001",
        session_file="sessions/test_001.session",
        script_id="000新人欢迎剧本"
    )
    
    # 2. 验证分配结果
    assert account.server_id is not None
    assert account.status == "offline"
    
    # 3. 验证Session文件上传
    server = get_server(account.server_id)
    assert session_file_exists(server, account.session_file)
    
    # 4. 启动账号
    success = await start_account(account.account_id)
    assert success == True
    
    # 5. 验证账号状态
    account = await get_account(account.account_id)
    assert account.status == "online"
    
    # 6. 验证剧本加载
    script_engine = get_script_engine(account.account_id)
    assert script_engine is not None
```

#### 5.2.2 负载均衡测试

**测试场景**:
1. 创建10个账号
2. 验证账号均匀分布到3个服务器
3. 验证每个服务器账号数不超过最大限制
4. 验证负载分数计算正确

### 5.3 性能测试

#### 5.3.1 分配性能测试

**指标**:
- 单次分配耗时: < 5秒
- 并发分配吞吐量: > 10账号/分钟
- 服务器状态查询延迟: < 1秒

**测试脚本**: `scripts/performance_test_allocation.py`

#### 5.3.2 剧本聊天性能测试

**指标**:
- 消息处理延迟: < 500ms
- 并发消息处理: > 100消息/秒
- 内存使用: < 500MB/账号

### 5.4 压力测试

#### 5.4.1 大规模分配测试

**场景**: 同时分配50个账号到3个服务器

**验证点**:
- 所有账号成功分配
- 服务器负载均衡
- 无资源泄漏
- 无死锁或竞态条件

#### 5.4.2 故障恢复测试

**场景**: 模拟服务器故障

**验证点**:
- 自动检测服务器故障
- 自动迁移账号到其他服务器
- 账号服务自动恢复
- 无数据丢失

## 6. 优化建议

### 6.1 性能优化

1. **缓存服务器状态**: 使用Redis缓存服务器状态，减少SSH查询
2. **异步分配**: 使用异步IO处理分配操作，提高并发性能
3. **批量分配**: 支持批量分配多个账号，减少网络往返
4. **连接池**: 使用SSH连接池，复用SSH连接

### 6.2 可靠性优化

1. **重试机制**: 分配失败时自动重试，最多3次
2. **故障转移**: 主服务器故障时自动切换到备用服务器
3. **数据备份**: 定期备份分配记录和服务器状态
4. **监控告警**: 集成告警系统，及时通知异常情况

### 6.3 扩展性优化

1. **插件化策略**: 支持自定义分配策略插件
2. **动态配置**: 支持动态添加/删除服务器，无需重启
3. **水平扩展**: 支持添加更多工作节点，自动纳入分配系统
4. **API版本控制**: 支持API版本管理，便于升级

## 7. 部署方案

### 7.1 主控制节点部署

**环境要求**:
- Python 3.9+
- FastAPI + Uvicorn
- SQLite/PostgreSQL
- Redis (可选，用于缓存)

**部署步骤**:
1. 安装依赖: `pip install -r requirements.txt`
2. 配置环境变量: 复制`.env.example`到`.env`
3. 初始化数据库: `python init_db.py`
4. 启动服务: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### 7.2 工作节点部署

**环境要求**:
- Python 3.9+
- Pyrogram
- 系统服务管理 (systemd)

**部署步骤**:
1. 上传部署包到服务器
2. 安装依赖: `pip install -r requirements.txt`
3. 配置systemd服务: `sudo systemctl enable group-ai-worker`
4. 启动服务: `sudo systemctl start group-ai-worker`

### 7.3 监控和日志

**监控指标**:
- 服务器CPU、内存、磁盘使用率
- 账号在线率
- 分配成功率
- 消息处理延迟

**日志管理**:
- 使用结构化日志 (JSON格式)
- 日志级别: DEBUG, INFO, WARNING, ERROR
- 日志轮转: 按天轮转，保留30天
- 集中日志收集: 可选集成ELK或类似系统

## 8. 安全考虑

### 8.1 认证和授权

- 使用JWT token进行API认证
- 基于角色的访问控制 (RBAC)
- 敏感操作需要管理员权限

### 8.2 数据安全

- Session文件加密存储
- SSH连接使用密钥认证（生产环境）
- 数据库连接使用SSL
- 敏感配置信息使用环境变量

### 8.3 网络安全

- API服务使用HTTPS
- 限制SSH访问IP白名单
- 使用VPN或专线连接工作节点
- 防火墙规则限制端口访问

## 9. 维护和运维

### 9.1 日常维护

1. **定期健康检查**: 每天检查所有服务器状态
2. **日志审查**: 每周审查错误日志，及时发现问题
3. **性能监控**: 监控系统性能指标，及时优化
4. **备份数据**: 每天备份数据库和配置文件

### 9.2 故障处理

1. **服务器故障**: 自动迁移账号到其他服务器
2. **账号故障**: 自动重启账号服务，最多3次
3. **网络故障**: 使用重试机制，等待网络恢复
4. **数据损坏**: 从备份恢复数据

### 9.3 升级流程

1. **测试环境验证**: 先在测试环境验证新版本
2. **灰度发布**: 先升级部分服务器，验证无问题后再全面升级
3. **回滚方案**: 准备回滚脚本，出现问题及时回滚
4. **版本管理**: 使用Git标签管理版本，便于追踪

## 10. 总结

本设计文档详细描述了智能分配Session帐号至服务器的完整系统架构和实现方案。系统采用主从架构，通过智能分配引擎实现账号的自动分配和负载均衡，支持剧本聊天功能的完整实现。

**核心特性**:
- ✅ 智能分配算法，支持多种分配策略
- ✅ 实时服务器监控和健康检查
- ✅ 自动负载均衡和故障转移
- ✅ 完整的剧本聊天功能
- ✅ 高可用性和可扩展性
- ✅ 完善的测试和监控方案

**技术栈**:
- 后端: FastAPI + SQLAlchemy + Paramiko
- 前端: Next.js + React
- 数据库: SQLite/PostgreSQL
- 缓存: Redis (可选)
- 部署: systemd + SSH/SFTP

**下一步行动**:
1. 实现智能分配引擎核心代码
2. 完善服务器监控功能
3. 编写单元测试和集成测试
4. 进行性能测试和优化
5. 部署到生产环境并持续监控

