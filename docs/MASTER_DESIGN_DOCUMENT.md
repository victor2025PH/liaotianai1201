# 项目重构与升级核心设计书 (Master Design Document)

> **创建日期**: 2025-12-22  
> **版本**: v1.0  
> **状态**: Phase 1 准备阶段

---

## 1. 核心目标

我们将现有的 Next.js + FastAPI 系统升级为 **分布式Telegram智能指挥中心**。

### 1.1 架构升级目标
- **从单体架构升级为分布式架构**：Server/Agent 分离
- **解决代码重复问题**：在开发新模块时遵循"高内聚、低耦合"原则
- **提升系统性能**：高频任务下沉到 Agent 端执行，降低延迟
- **增强系统扩展性**：支持多 Agent 协同工作

### 1.2 代码质量目标
- **减少代码重复**：通过通用组件和 Hook 减少 30-40% 代码量
- **统一开发规范**：所有新功能必须使用通用 CRUD Hook 和表格组件
- **提高可维护性**：降低维护成本 50-60%

---

## 2. 架构变更 (C/S 架构)

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Server 端 (admin-backend)              │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FastAPI (策略制定、账号管理、指令下发)            │   │
│  │  - WebSocket Server                              │   │
│  │  - 策略配置管理                                   │   │
│  │  - 时间轴调度器                                   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        ↕ WebSocket
┌─────────────────────────────────────────────────────────┐
│                    Agent 端 (agent)                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Python 独立进程 (本地/VPS)                       │   │
│  │  - WebSocket Client                               │   │
│  │  - TG Session 管理                                │   │
│  │  - 高频任务执行 (抢红包、炒群)                     │   │
│  │  - 设备指纹伪装                                   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 2.2 组件职责划分

#### Server 端 (`/admin-backend`)
- **策略制定**: 创建和管理业务策略（红包策略、炒群策略等）
- **账号管理**: 统一管理所有 Telegram 账号
- **指令下发**: 通过 WebSocket 向 Agent 发送执行指令
- **状态监控**: 实时监控所有 Agent 和账号状态
- **数据聚合**: 收集和汇总 Agent 上报的数据

#### Agent 端 (`/agent`)
- **任务执行**: 执行高频任务（抢红包、炒群、消息发送等）
- **Session 管理**: 持有和管理 Telegram Session 文件
- **状态上报**: 实时向 Server 上报执行状态和结果
- **设备伪装**: 实现设备指纹伪装和 IP 绑定检测
- **本地缓存**: 缓存常用数据，减少网络请求

### 2.3 通信协议

#### WebSocket 消息格式
```typescript
// Server -> Agent (指令)
interface ServerCommand {
  type: 'redpacket' | 'chat' | 'monitor' | 'config'
  action: string
  payload: any
  timestamp: number
}

// Agent -> Server (状态上报)
interface AgentStatus {
  agent_id: string
  status: 'online' | 'offline' | 'busy' | 'error'
  accounts: AccountStatus[]
  metrics: {
    tasks_completed: number
    tasks_failed: number
    last_activity: string
  }
}
```

---

## 3. 实施路线图 (Roadmap)

### Phase 1: 通信基石与节点管理重构 ⏳ 当前阶段

**目标**: 搭建 Server 与 Agent 的 WebSocket 通信，重构节点管理页面

**后端任务**:
1. ✅ 设计 WebSocket 通信协议
2. ⏳ 实现 Server 端 WebSocket 服务
3. ⏳ 实现 Agent 端 WebSocket 客户端
4. ⏳ 实现 Agent 注册和心跳机制
5. ⏳ 实现 Agent 状态上报接口

**前端任务**:
1. ⏳ 创建通用 CRUD Hook (`hooks/useCrud.ts`)
2. ⏳ 创建通用表格组件 (`components/crud/DataTable.tsx`)
3. ⏳ 重写"节点管理"页面，使用通用组件
4. ⏳ 实现 WebSocket 客户端连接
5. ⏳ 实现实时状态展示（Agent 在线/离线状态）

**预期成果**:
- Server 和 Agent 可以稳定通信
- 节点管理页面代码量减少 40%
- 实时显示所有 Agent 在线状态
- 为后续 Phase 奠定基础

**时间估算**: 2-3 周

---

### Phase 2: 边缘红包引擎 (Edge RedPacket)

**目标**: 将抢红包逻辑下沉到 Agent 本地执行，降低延迟

**后端任务**:
1. 设计红包策略 JSON 格式
2. 实现策略下发接口
3. 实现红包结果上报接口
4. 实现策略模板管理

**前端任务**:
1. 创建"策略配置"页面（使用通用 CRUD Hook）
2. 实现策略 JSON 编辑器
3. 实现策略下发功能
4. 实现红包结果统计展示

**业务逻辑**:
- Server 端：策略配置、下发、结果统计
- Agent 端：接收策略、执行抢红包、上报结果

**预期成果**:
- 抢红包延迟降低 50-80%
- 支持多 Agent 并发抢红包
- 策略配置可视化界面

**时间估算**: 2-3 周

---

### Phase 3: 智能剧场与多号协同 (Theater Mode)

**目标**: Server 端实现时间轴调度器，指挥多个 Agent 协同发言（炒群）

**后端任务**:
1. 设计时间轴调度器
2. 整合现有"剧本管理"功能
3. 整合现有"自动化任务"功能
4. 实现多 Agent 协同调度算法
5. 实现发言时间轴管理

**前端任务**:
1. 创建"剧场模式"页面
2. 整合"剧本管理"到新页面（使用通用组件）
3. 整合"自动化任务"到新页面（使用通用组件）
4. 实现时间轴可视化
5. 实现协同效果监控

**业务逻辑**:
- Server 端：时间轴调度、剧本管理、任务编排
- Agent 端：接收发言指令、执行发言、上报状态

**预期成果**:
- 实现多 Agent 协同炒群
- 整合原有剧本和任务功能
- 减少功能重复，统一管理界面

**时间估算**: 3-4 周

---

### Phase 4: 风控加固 (Security)

**目标**: Agent 端实现设备指纹伪装和 IP 绑定检测

**后端任务**:
1. 设计设备指纹规则
2. 实现指纹验证接口
3. 实现 IP 绑定检测接口
4. 实现风控规则管理

**前端任务**:
1. 创建"风控配置"页面（使用通用 CRUD Hook）
2. 实现设备指纹配置界面
3. 实现 IP 绑定管理界面
4. 实现风控日志展示

**业务逻辑**:
- Server 端：风控规则配置、检测结果统计
- Agent 端：设备指纹伪装、IP 检测、规则执行

**预期成果**:
- 降低账号被封风险
- 支持设备指纹伪装
- 支持 IP 绑定检测

**时间估算**: 2-3 周

---

## 4. 代码规范与最佳实践

### 4.1 前端开发规范

#### 4.1.1 必须使用通用组件
**所有新页面必须使用以下通用组件**：

```typescript
// ✅ 正确：使用通用 CRUD Hook
import { useCrud } from '@/hooks/useCrud'

const MyPage = () => {
  const {
    items,
    loading,
    error,
    handleCreate,
    handleUpdate,
    handleDelete,
    handleEdit,
    searchFilters,
    setSearchFilters
  } = useCrud({
    listApi: getMyItems,
    createApi: createMyItem,
    updateApi: updateMyItem,
    deleteApi: deleteMyItem
  })
  
  // ...
}

// ❌ 错误：重复实现 CRUD 逻辑
const MyPage = () => {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  // ... 大量重复代码
}
```

#### 4.1.2 必须使用通用表格组件
```typescript
// ✅ 正确：使用通用表格组件
import { DataTable } from '@/components/crud/DataTable'

<DataTable
  data={items}
  columns={columns}
  onEdit={handleEdit}
  onDelete={handleDelete}
  searchable
  filterable
  pagination
/>

// ❌ 错误：重复实现表格逻辑
// 自己实现表格、搜索、分页等
```

#### 4.1.3 高内聚、低耦合原则
- **高内聚**: 相关功能放在同一个组件/Hook 中
- **低耦合**: 组件之间通过 Props 和事件通信，避免直接依赖

```typescript
// ✅ 正确：高内聚
// hooks/useAgentStatus.ts - 所有 Agent 状态相关逻辑集中
export function useAgentStatus(agentId: string) {
  // WebSocket 连接
  // 状态订阅
  // 状态更新
  // 错误处理
  // 全部集中在一个 Hook 中
}

// ❌ 错误：低内聚
// 状态管理分散在多个地方
const [status, setStatus] = useState() // 在组件中
const ws = useWebSocket() // 在另一个 Hook 中
const handleError = () => {} // 在工具函数中
```

### 4.2 后端开发规范

#### 4.2.1 WebSocket 通信规范
```python
# ✅ 正确：统一的 WebSocket 消息格式
class WebSocketMessage(BaseModel):
    type: str
    action: str
    payload: dict
    timestamp: int

# ✅ 正确：统一的错误响应
class WebSocketError(BaseModel):
    error_code: str
    error_message: str
    timestamp: int
```

#### 4.2.2 API 设计规范
- 所有 API 必须遵循 RESTful 规范
- 统一错误响应格式
- 统一分页格式
- 统一认证机制

---

## 5. 与现有优化方案的融合

### 5.1 代码优化方案整合

**Phase 1 正好对应之前优化方案的第一阶段**：

| 优化方案 | Phase 1 实施 |
|---------|-------------|
| 创建通用CRUD Hook | ✅ Phase 1 前端任务 1 |
| 创建通用表格组件 | ✅ Phase 1 前端任务 2 |
| 重构核心页面 | ✅ Phase 1 前端任务 3（节点管理页面） |

**收益叠加**：
- Phase 1 重构节点管理页面 → 减少代码重复
- 同时引入 WebSocket 实时通信 → 新功能
- 为后续 Phase 奠定通用组件基础 → 加速开发

### 5.2 功能整合方案

**Phase 3 整合现有功能**：

| 现有功能 | Phase 3 整合方案 |
|---------|----------------|
| 剧本管理 | 整合到"剧场模式"页面 |
| 自动化任务 | 整合到"剧场模式"页面 |
| 角色分配 | 整合到"剧场模式"页面 |

**收益**：
- 减少功能重复
- 统一管理界面
- 提升用户体验

---

## 6. Phase 1 详细实施计划

### 6.1 后端实施步骤

#### Step 1: WebSocket 服务搭建 (3天)
```python
# admin-backend/app/websocket/server.py
class WebSocketServer:
    def __init__(self):
        self.agents: Dict[str, WebSocket] = {}
        self.agent_status: Dict[str, AgentStatus] = {}
    
    async def register_agent(self, agent_id: str, websocket: WebSocket):
        """注册 Agent"""
        pass
    
    async def broadcast_command(self, command: ServerCommand):
        """向所有 Agent 广播指令"""
        pass
    
    async def handle_agent_status(self, agent_id: str, status: AgentStatus):
        """处理 Agent 状态上报"""
        pass
```

#### Step 2: Agent 注册和心跳机制 (2天)
- Agent 连接时自动注册
- 实现心跳机制（每30秒）
- 实现断线重连机制
- 实现状态持久化

#### Step 3: API 接口开发 (2天)
```python
# GET /api/v1/agents - 获取所有 Agent 列表
# GET /api/v1/agents/{agent_id} - 获取 Agent 详情
# GET /api/v1/agents/{agent_id}/status - 获取 Agent 实时状态
# POST /api/v1/agents/{agent_id}/command - 向 Agent 发送指令
```

### 6.2 前端实施步骤

#### Step 1: 创建通用 CRUD Hook (3天)
```typescript
// hooks/useCrud.ts
export function useCrud<T, CreateT, UpdateT>({
  listApi,
  getApi,
  createApi,
  updateApi,
  deleteApi,
  initialFilters
}) {
  // 统一的状态管理
  // 统一的 CRUD 操作
  // 统一的错误处理
  // 统一的加载状态
}
```

#### Step 2: 创建通用表格组件 (3天)
```typescript
// components/crud/DataTable.tsx
export function DataTable<T>({
  data,
  columns,
  onEdit,
  onDelete,
  searchable,
  filterable,
  pagination
}: DataTableProps<T>) {
  // 统一的表格渲染
  // 统一的搜索过滤
  // 统一的分页
  // 统一的批量操作
}
```

#### Step 3: 创建 WebSocket Hook (2天)
```typescript
// hooks/useWebSocket.ts
export function useWebSocket(url: string) {
  // WebSocket 连接管理
  // 消息发送和接收
  // 自动重连
  // 状态管理
}
```

#### Step 4: 重写节点管理页面 (5天)
```typescript
// app/group-ai/nodes/page.tsx
export default function NodesPage() {
  // 使用 useCrud Hook
  const crud = useCrud({...})
  
  // 使用 WebSocket Hook 获取实时状态
  const { agents, status } = useAgentStatus()
  
  // 使用通用表格组件
  return (
    <DataTable
      data={agents}
      columns={agentColumns}
      onEdit={crud.handleEdit}
      onDelete={crud.handleDelete}
    />
  )
}
```

### 6.3 Agent 端实施步骤

#### Step 1: WebSocket 客户端实现 (2天)
```python
# agent/websocket/client.py
class WebSocketClient:
    def __init__(self, server_url: str, agent_id: str):
        self.server_url = server_url
        self.agent_id = agent_id
        self.ws = None
    
    async def connect(self):
        """连接到 Server"""
        pass
    
    async def send_status(self, status: AgentStatus):
        """发送状态到 Server"""
        pass
    
    async def handle_command(self, command: ServerCommand):
        """处理 Server 指令"""
        pass
```

#### Step 2: Agent 注册和心跳 (1天)
- 实现 Agent ID 生成
- 实现自动注册
- 实现心跳机制

---

## 7. 技术栈

### 7.1 Server 端
- **框架**: FastAPI
- **WebSocket**: `fastapi[websockets]` 或 `python-socketio`
- **数据库**: PostgreSQL (现有)
- **缓存**: Redis (现有)

### 7.2 Agent 端
- **语言**: Python 3.10+
- **WebSocket**: `websockets` 或 `python-socketio`
- **TG 客户端**: `pyrogram` (现有)
- **配置**: YAML/JSON

### 7.3 前端
- **框架**: Next.js 14
- **状态管理**: React Hooks
- **WebSocket**: `useWebSocket` Hook (自定义)
- **UI 组件**: shadcn/ui (现有)
- **通用组件**: 新建 `components/crud/`

---

## 8. 关键决策点

### 8.1 已确认
- ✅ 采用 Server/Agent 分离架构
- ✅ Phase 1 从节点管理页面重构开始
- ✅ 必须使用通用 CRUD Hook 和表格组件
- ✅ 遵循"高内聚、低耦合"原则

### 8.2 待确认
- ⏳ WebSocket 库选择（FastAPI WebSocket vs Socket.IO）
- ⏳ Agent 端 Python 版本要求
- ⏳ 是否需要 Agent 端配置管理界面
- ⏳ 是否需要 Agent 端日志上报

---

## 9. 成功标准

### Phase 1 成功标准
- ✅ Server 和 Agent 可以稳定建立 WebSocket 连接
- ✅ Agent 可以成功注册并上报状态
- ✅ 节点管理页面代码量减少 40%+
- ✅ 节点管理页面实时显示 Agent 在线状态
- ✅ 所有新代码遵循"高内聚、低耦合"原则
- ✅ 通用 CRUD Hook 和表格组件可以复用

---

## 10. 风险评估与应对

### 10.1 技术风险
- **WebSocket 连接不稳定**: 
  - 风险：网络波动导致连接断开
  - 应对：实现自动重连机制、心跳检测
  
- **Agent 状态同步延迟**:
  - 风险：状态更新不及时
  - 应对：使用 WebSocket 实时推送，减少轮询

### 10.2 开发风险
- **通用组件不够灵活**:
  - 风险：某些特殊需求无法满足
  - 应对：设计可扩展的组件 API，支持自定义

- **代码迁移成本高**:
  - 风险：现有页面迁移到新组件耗时
  - 应对：分阶段迁移，先迁移新页面，再逐步迁移旧页面

---

## 11. 下一步行动

### 立即开始（本周）
1. ✅ 确认设计文档（本文档）
2. ⏳ 创建 Phase 1 详细任务清单
3. ⏳ 搭建开发环境
4. ⏳ 开始实施 Step 1（后端 WebSocket 服务）

### 本周目标
- 完成后端 WebSocket 服务基础框架
- 完成通用 CRUD Hook 设计
- 完成通用表格组件设计

---

**文档版本**: v1.0  
**最后更新**: 2025-12-22  
**维护者**: Development Team  
**状态**: Phase 1 准备阶段
