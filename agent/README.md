# Agent - Telegram 智能执行端

Agent 是分布式 Telegram 智能指挥中心的执行端，运行在本地电脑或 VPS 上，通过 WebSocket 连接到 Server，执行高频任务。

## 功能特性

- ✅ WebSocket 连接管理
- ✅ 自动注册和认证
- ✅ 心跳机制（30秒）
- ✅ 断线自动重连
- ✅ 状态上报
- ✅ 指令接收和执行

## 安装

```bash
cd agent
pip install -r requirements.txt
```

## 配置

首次运行会自动生成 `config.json` 配置文件：

```json
{
  "agent_id": "自动生成的 UUID",
  "server_url": "ws://localhost:8000/api/v1/agents/ws",
  "heartbeat_interval": 30,
  "reconnect_interval": 30,
  "reconnect_max_attempts": -1,
  "metadata": {
    "version": "1.0.0",
    "platform": "Windows",
    "hostname": "your-hostname"
  }
}
```

### 配置说明

- `agent_id`: Agent 唯一标识（自动生成，不要手动修改）
- `server_url`: Server WebSocket 地址
- `heartbeat_interval`: 心跳间隔（秒）
- `reconnect_interval`: 重连间隔（秒）
- `reconnect_max_attempts`: 最大重连次数（-1 表示无限）

## 运行

```bash
python main.py
```

## 日志输出示例

```
[2025-12-22 10:00:00] [INFO] ============================================================
[2025-12-22 10:00:00] [INFO] Telegram Agent - 智能执行端
[2025-12-22 10:00:00] [INFO] ============================================================
[2025-12-22 10:00:00] [INFO] Agent ID: 123e4567-e89b-12d3-a456-426614174000
[2025-12-22 10:00:00] [INFO] Server URL: ws://localhost:8000/api/v1/agents/ws/123e4567-e89b-12d3-a456-426614174000
[2025-12-22 10:00:00] [INFO] ============================================================
[2025-12-22 10:00:00] [INFO] 
[2025-12-22 10:00:01] [INFO] [INFO] 正在连接服务器: ws://localhost:8000/api/v1/agents/ws/...
[2025-12-22 10:00:02] [INFO] [SUCCESS] 连接成功! Agent ID: 123e4567-e89b-12d3-a456-426614174000
[2025-12-22 10:00:02] [INFO] [REGISTER] 已发送注册消息
[2025-12-22 10:00:02] [INFO] [INFO] Agent 运行中，按 Ctrl+C 退出
[2025-12-22 10:00:32] [DEBUG] [HEARTBEAT] 心跳发送 (10:00:32)
[2025-12-22 10:01:02] [DEBUG] [HEARTBEAT] 心跳发送 (10:01:02)
```

## 开发

### 添加新的指令处理

在 `main.py` 的 `handle_command` 函数中添加新的 action 处理：

```python
async def handle_command(message: dict):
    payload = message.get("payload", {})
    action = payload.get("action")
    
    if action == "redpacket":
        # 处理抢红包指令
        await handle_redpacket(payload)
    elif action == "chat":
        # 处理聊天指令
        await handle_chat(payload)
    # ...
```

## 下一步

- [ ] 集成 Telethon/Pyrogram
- [ ] 实现抢红包功能
- [ ] 实现炒群功能
- [ ] 设备指纹伪装
