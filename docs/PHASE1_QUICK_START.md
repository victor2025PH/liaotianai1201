# Phase 1 快速开始指南

> **当前进度**: Step 1 已完成 ✅  
> **下一步**: Step 2 - Agent 端 WebSocket Client

---

## ✅ Step 1 已完成：后端 WebSocket Manager

### 已创建的文件

```
admin-backend/app/
  websocket/
    __init__.py          # 模块导出
    manager.py           # WebSocket 管理器（核心）
    connection.py        # Agent 连接对象
    message_handler.py   # 消息处理器
  api/
    agents.py            # Agent API（WebSocket + REST）
```

### 功能特性

1. **WebSocket 端点**: `/api/v1/agents/ws/{agent_id}`
2. **Agent 注册**: 自动注册和认证
3. **心跳机制**: 30秒检查，60秒超时
4. **消息类型**: REGISTER, STATUS, HEARTBEAT, RESULT, COMMAND, CONFIG, ACK
5. **REST API**: 获取 Agent 列表、发送指令、广播指令

### 测试方法

1. **启动后端**:
```bash
cd admin-backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

2. **检查 WebSocket Manager 是否启动**:
查看日志，应该看到：
```
WebSocket Manager 已啟動（Agent 通信）
```

3. **测试 REST API**:
```bash
# 获取 Agent 列表（需要认证）
curl -X GET http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取统计信息
curl -X GET http://localhost:8000/api/v1/agents/statistics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ⏳ Step 2: Agent 端 WebSocket Client（下一步）

### 需要创建的文件

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

### 功能要求

1. **连接到 Server**: `ws://localhost:8000/api/v1/agents/ws/{agent_id}`
2. **自动注册**: 连接后发送注册消息
3. **心跳机制**: 每30秒发送心跳
4. **断线重连**: 自动重连机制
5. **状态上报**: 定期上报 Agent 状态

### 开始实施

准备好后，告诉我开始 Step 2，我将创建 Agent 端的 WebSocket Client。

---

## 📋 完整任务清单

- [x] Step 1: 后端 WebSocket Manager ✅
- [ ] Step 2: Agent 端 WebSocket Client
- [ ] Step 3: 前端通用 CRUD Hook
- [ ] Step 4: 前端通用表格组件
- [ ] Step 5: 前端 WebSocket Hook
- [ ] Step 6: 重写节点管理页面

---

**最后更新**: 2025-12-22
