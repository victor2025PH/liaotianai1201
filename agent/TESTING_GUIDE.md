# Agent WebSocket Client 测试指南

## 快速测试步骤

### 1. 安装依赖

```bash
cd agent
pip install -r requirements.txt
```

### 2. 启动 Server（后端）

```bash
cd admin-backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

查看日志，确认看到：
```
WebSocket Manager 已啟動（Agent 通信）
```

### 3. 启动 Agent

```bash
cd agent
python main.py
```

### 4. 验证连接

**Agent 端日志应该显示**：
```
[INFO] 正在连接服务器: ws://localhost:8000/api/v1/agents/ws/{agent_id}
[SUCCESS] 连接成功! Agent ID: {agent_id}
[REGISTER] 已发送注册消息
[INFO] Agent 运行中，按 Ctrl+C 退出
[HEARTBEAT] 心跳发送 (每30秒)
```

**Server 端日志应该显示**：
```
Agent {agent_id} 连接已接受
Agent {agent_id} 已注册，当前连接数: 1
```

### 5. 测试 REST API（验证 Agent 已连接）

在另一个终端：

```bash
# 先登录获取 token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123"

# 使用返回的 token 获取 Agent 列表
curl -X GET http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取统计信息
curl -X GET http://localhost:8000/api/v1/agents/statistics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

应该看到你的 Agent 在列表中，状态为 `connected`。

### 6. 测试发送指令

```bash
# 向 Agent 发送测试指令
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/command \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test",
    "payload": {
      "message": "Hello from Server!"
    }
  }'
```

**Agent 端应该收到并打印**：
```
[COMMAND] 收到指令: test
[COMMAND] 指令内容: {'action': 'test', 'message': 'Hello from Server!'}
```

## 故障排查

### Agent 无法连接

1. **检查 Server 是否运行**：
   ```bash
   curl http://localhost:8000/health
   ```

2. **检查 WebSocket URL**：
   查看 `agent/config.json` 中的 `server_url` 是否正确

3. **检查防火墙**：
   确保端口 8000 没有被阻止

### 心跳失败

1. **检查网络连接**
2. **查看 Server 日志**，确认是否收到心跳
3. **检查 Agent 日志**，查看是否有错误信息

### 重连失败

1. **检查 Server 是否正常运行**
2. **查看 Agent 日志**，确认重连尝试
3. **检查 `reconnect_max_attempts` 配置**（-1 表示无限重试）

## 下一步

连接验证成功后，可以继续：
- Step 3: 创建前端通用 CRUD Hook
- Step 4: 创建前端通用表格组件
- Step 5: 创建前端 WebSocket Hook
- Step 6: 重写节点管理页面
