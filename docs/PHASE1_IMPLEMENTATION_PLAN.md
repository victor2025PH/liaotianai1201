# Phase 1: 基础设施与节点管理 - 详细实施计划

> **版本**: v1.0  
> **状态**: 进行中  
> **开始日期**: 2025-12-22

---

## 📋 Phase 1 目标

1. **打通 WebSocket 通信**: Server 和 Agent 可以稳定通信
2. **重写节点管理页面**: 使用通用组件，减少代码重复
3. **实时状态展示**: 前端实时显示 Agent 在线状态

---

## 🎯 任务清单

### Step 1: 后端 WebSocket Manager (3天) ⏳ 当前任务

**目标**: 创建统一的 Agent WebSocket 管理器

**文件结构**:
```
admin-backend/
  app/
    websocket/
      __init__.py
      manager.py          # WebSocket 管理器
      connection.py       # 连接管理
      message_handler.py # 消息处理
    api/
      agents.py           # Agent API 接口
```

**功能要求**:
- Agent 注册和认证
- 心跳机制（30秒）
- 连接状态管理
- 消息广播和单播
- 断线重连支持

---

### Step 2: Agent 端 WebSocket Client (2天)

**目标**: 创建 Python Agent 客户端

**文件结构**:
```
agent/
  __init__.py
  websocket/
    __init__.py
    client.py            # WebSocket 客户端
    message_handler.py   # 消息处理
  config.py              # 配置文件
  main.py                # 入口文件
```

**功能要求**:
- 连接到 Server WebSocket
- 自动注册 Agent ID
- 心跳机制
- 断线自动重连
- 状态上报

---

### Step 3: 前端通用 CRUD Hook (3天)

**目标**: 创建可复用的 CRUD Hook

**文件结构**:
```
saas-demo/
  src/
    hooks/
      useCrud.ts         # 通用 CRUD Hook
```

**功能要求**:
- 统一的状态管理（items, loading, error）
- 统一的 CRUD 操作（create, update, delete, list）
- 统一的错误处理
- 统一的搜索和过滤
- 统一的分页

---

### Step 4: 前端通用表格组件 (3天)

**目标**: 创建可复用的表格组件

**文件结构**:
```
saas-demo/
  src/
    components/
      crud/
        DataTable.tsx    # 通用表格组件
        CrudDialog.tsx   # 通用对话框组件
```

**功能要求**:
- 表格渲染
- 搜索和过滤
- 分页
- 批量操作
- 排序

---

### Step 5: 前端 WebSocket Hook (2天)

**目标**: 创建 WebSocket 连接 Hook

**文件结构**:
```
saas-demo/
  src/
    hooks/
      useWebSocket.ts    # WebSocket Hook
      useAgentStatus.ts  # Agent 状态 Hook
```

**功能要求**:
- WebSocket 连接管理
- 自动重连
- 消息发送和接收
- 状态订阅

---

### Step 6: 重写节点管理页面 (5天)

**目标**: 使用通用组件重写节点管理页面

**文件结构**:
```
saas-demo/
  src/
    app/
      group-ai/
        nodes/
          page.tsx       # 重写的节点管理页面
```

**功能要求**:
- 使用 useCrud Hook
- 使用 DataTable 组件
- 实时显示 Agent 在线状态（绿灯/红灯）
- 显示延迟信息
- 支持发送指令

---

## 📊 实施顺序

**推荐顺序**:
1. ✅ Step 1: 后端 WebSocket Manager（当前）
2. ⏳ Step 2: Agent 端 WebSocket Client
3. ⏳ Step 3: 前端通用 CRUD Hook
4. ⏳ Step 4: 前端通用表格组件
5. ⏳ Step 5: 前端 WebSocket Hook
6. ⏳ Step 6: 重写节点管理页面

**原因**:
- 先搭建通信基础（后端 + Agent）
- 再创建通用组件（为页面重构做准备）
- 最后整合（重写页面）

---

## 🔧 技术细节

### WebSocket 消息格式

```typescript
// Server -> Agent
interface ServerCommand {
  type: 'register' | 'command' | 'heartbeat'
  action: string
  payload: any
  timestamp: number
}

// Agent -> Server
interface AgentMessage {
  type: 'register' | 'status' | 'heartbeat' | 'result'
  agent_id: string
  payload: any
  timestamp: number
}
```

### Agent 状态模型

```typescript
interface AgentStatus {
  agent_id: string
  status: 'online' | 'offline' | 'busy' | 'error'
  last_heartbeat: string
  latency?: number
  accounts: AccountStatus[]
  metrics: {
    tasks_completed: number
    tasks_failed: number
  }
}
```

---

## ✅ 验收标准

### Step 1 验收标准
- ✅ WebSocket Manager 可以接受 Agent 连接
- ✅ Agent 可以成功注册
- ✅ 心跳机制正常工作
- ✅ 可以发送和接收消息

### Phase 1 整体验收标准
- ✅ Server 和 Agent 可以稳定通信
- ✅ 节点管理页面代码量减少 40%+
- ✅ 实时显示 Agent 在线状态
- ✅ 所有新代码遵循"高内聚、低耦合"原则

---

**最后更新**: 2025-12-22
