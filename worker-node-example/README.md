# Worker 节点 Session 文件管理集成指南

## 概述

本目录包含 Worker 节点集成 Session 文件管理功能的示例代码。

## 文件说明

- `worker_session_handler.py`: Session 文件处理核心逻辑
- `worker_node_integration.py`: 完整的 Worker 节点集成示例

## 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置环境变量

```bash
export SERVER_URL="https://aikz.usdt2026.cc"
export NODE_ID="PC-001"
export SESSIONS_DIR="/sessions"
export HEARTBEAT_INTERVAL="30"
export API_TOKEN="your-token-if-needed"
```

### 3. 运行 Worker 节点

```bash
python3 worker_node_integration.py
```

## 集成到现有 Worker 节点

### 方法 1: 直接导入模块

```python
from worker_session_handler import process_command

# 在心跳循环中
commands = get_pending_commands()
command_responses = {}

for command in commands:
    result = process_command(command)
    command_id = command.get("command_id")
    if command_id:
        command_responses[command_id] = result

# 在心跳响应中包含 command_responses
send_heartbeat(command_responses=command_responses)
```

### 方法 2: 使用 WorkerNode 类

```python
from worker_node_integration import WorkerNode, CONFIG

worker = WorkerNode(CONFIG)
worker.heartbeat_loop()
```

## 支持的命令

### list_sessions

扫描本地 `/sessions` 文件夹，返回所有 `.session` 文件列表。

**命令格式：**
```json
{
  "action": "list_sessions",
  "params": {},
  "command_id": "uuid-string"
}
```

**响应格式：**
```json
{
  "command_id": "uuid-string",
  "success": true,
  "data": {
    "sessions": [
      {
        "filename": "account1.session",
        "size": 1024,
        "modified_time": "2025-12-16T10:00:00",
        "path": "/sessions/account1.session"
      }
    ]
  }
}
```

### upload_session

接收 base64 编码的文件内容，保存到本地 `/sessions` 文件夹。

**命令格式：**
```json
{
  "action": "upload_session",
  "params": {
    "filename": "account1.session",
    "file_content": "base64-encoded-content",
    "file_size": 1024
  },
  "command_id": "uuid-string"
}
```

**响应格式：**
```json
{
  "command_id": "uuid-string",
  "success": true,
  "data": {
    "filename": "account1.session",
    "path": "/sessions/account1.session",
    "size": 1024
  }
}
```

## 配置说明

### 环境变量

- `SERVER_URL`: 服务器地址（必需）
- `NODE_ID`: Worker 节点 ID（必需）
- `SESSIONS_DIR`: Session 文件目录（默认：`/sessions`）
- `HEARTBEAT_INTERVAL`: 心跳间隔（秒，默认：30）
- `API_TOKEN`: API 认证令牌（如果需要）

### 文件大小限制

默认最大文件大小为 10MB，可在 `worker_session_handler.py` 中修改 `MAX_FILE_SIZE` 常量。

## 错误处理

所有命令处理函数都会返回包含 `success` 字段的响应：

- `success: true`: 命令执行成功
- `success: false`: 命令执行失败，包含 `error` 字段说明错误原因

## 测试

### 测试 list_sessions

```python
from worker_session_handler import handle_list_sessions_command

result = handle_list_sessions_command({})
print(result)
```

### 测试 upload_session

```python
import base64
from worker_session_handler import handle_upload_session_command

# 准备测试数据
test_content = b"test session content"
params = {
    "filename": "test.session",
    "file_content": base64.b64encode(test_content).decode('utf-8'),
    "file_size": len(test_content)
}

result = handle_upload_session_command(params)
print(result)
```

## 注意事项

1. **文件权限**：上传的文件会自动设置为 `600`（仅所有者可读可写）
2. **文件冲突**：如果文件已存在，会自动添加后缀（`_1`, `_2`, ...）
3. **目录创建**：如果 Session 目录不存在，会自动创建
4. **错误日志**：所有错误都会记录到日志中，便于调试

## 故障排除

### 问题 1: 无法连接到服务器

- 检查 `SERVER_URL` 是否正确
- 检查网络连接
- 检查防火墙设置

### 问题 2: 命令未执行

- 检查 Worker 节点是否在线
- 检查心跳是否正常发送
- 查看日志中的错误信息

### 问题 3: 文件上传失败

- 检查文件大小是否超过限制
- 检查目录权限
- 检查磁盘空间

## 后续开发

可以扩展支持以下功能：

1. 文件下载：`download_session` 命令
2. 文件删除：`delete_session` 命令
3. 文件同步：`sync_sessions` 命令
4. 批量操作：支持批量上传/下载

