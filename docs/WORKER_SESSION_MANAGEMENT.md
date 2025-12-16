# Worker 节点 Session 文件管理架构

## 概述

本系统实现了在网页端（Admin）管理分布在不同 Worker 节点（本地电脑/服务器）上的 Telegram Session 文件的功能。

## 架构设计

### 1. 通信机制

- **命令队列**：使用 Redis List 或内存存储作为命令队列
- **响应存储**：使用 Redis Key-Value 或内存存储保存 Worker 节点的响应结果
- **心跳机制**：Worker 节点通过心跳获取命令并返回执行结果

### 2. 工作流程

#### 获取 Session 列表

```
网页端 → GET /api/v1/workers/{worker_id}/sessions
  ↓
后端生成命令 ID
  ↓
通过命令队列发送 "list_sessions" 命令
  ↓
Worker 节点心跳时获取命令
  ↓
Worker 节点扫描本地 /sessions 文件夹
  ↓
Worker 节点通过心跳返回结果（command_responses）
  ↓
后端轮询响应存储，获取结果
  ↓
返回 Session 文件列表给网页端
```

#### 上传 Session 文件

```
网页端 → POST /api/v1/workers/{worker_id}/sessions/upload
  ↓
后端验证文件格式和大小
  ↓
读取文件内容，编码为 base64
  ↓
生成命令 ID
  ↓
通过命令队列发送 "upload_session" 命令（包含文件内容）
  ↓
Worker 节点心跳时获取命令
  ↓
Worker 节点解码 base64，保存到本地 /sessions 文件夹
  ↓
Worker 节点通过心跳返回结果
  ↓
后端轮询响应存储，获取结果
  ↓
返回上传结果给网页端
```

## API 接口

### 1. 获取 Session 列表

**端点：** `GET /api/v1/workers/{worker_id}/sessions`

**参数：**
- `worker_id` (path): Worker 节点 ID
- `timeout` (query, 可选): 超时时间（秒），默认 30

**响应：**
```json
{
  "success": true,
  "node_id": "PC-001",
  "sessions": [
    {
      "filename": "account1.session",
      "size": 1024,
      "modified_time": "2025-12-16T10:00:00",
      "path": "/sessions/account1.session"
    }
  ],
  "total": 1,
  "message": "成功获取 1 个 Session 文件"
}
```

### 2. 上传 Session 文件

**端点：** `POST /api/v1/workers/{worker_id}/sessions/upload`

**参数：**
- `worker_id` (path): Worker 节点 ID
- `file` (form-data): Session 文件（.session 格式）
- `timeout` (query, 可选): 超时时间（秒），默认 60

**响应：**
```json
{
  "success": true,
  "node_id": "PC-001",
  "filename": "account1.session",
  "message": "Session 文件已成功上传到节点 PC-001"
}
```

## Worker 节点实现

### 命令格式

#### list_sessions 命令

```json
{
  "action": "list_sessions",
  "params": {},
  "command_id": "uuid-string",
  "timestamp": "2025-12-16T10:00:00",
  "from": "master"
}
```

**Worker 节点响应格式：**
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

#### upload_session 命令

```json
{
  "action": "upload_session",
  "params": {
    "filename": "account1.session",
    "file_content": "base64-encoded-content",
    "file_size": 1024
  },
  "command_id": "uuid-string",
  "timestamp": "2025-12-16T10:00:00",
  "from": "master"
}
```

**Worker 节点响应格式：**
```json
{
  "command_id": "uuid-string",
  "success": true,
  "data": {
    "filename": "account1.session",
    "path": "/sessions/account1.session"
  }
}
```

### Worker 节点示例代码

```python
import os
import base64
import json
from pathlib import Path
from datetime import datetime

# Session 文件夹路径
SESSIONS_DIR = Path("/sessions")  # 或从配置读取

def handle_list_sessions_command(params: dict) -> dict:
    """处理 list_sessions 命令"""
    sessions = []
    
    if SESSIONS_DIR.exists():
        for session_file in SESSIONS_DIR.glob("*.session"):
            stat = session_file.stat()
            sessions.append({
                "filename": session_file.name,
                "size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(session_file)
            })
    
    return {
        "success": True,
        "data": {
            "sessions": sessions
        }
    }


def handle_upload_session_command(params: dict) -> dict:
    """处理 upload_session 命令"""
    filename = params.get("filename")
    file_content_b64 = params.get("file_content")
    file_size = params.get("file_size")
    
    if not filename or not file_content_b64:
        return {
            "success": False,
            "error": "缺少文件名或文件内容"
        }
    
    try:
        # 确保目录存在
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 解码 base64
        file_content = base64.b64decode(file_content_b64)
        
        # 保存文件
        file_path = SESSIONS_DIR / filename
        
        # 如果文件已存在，添加后缀
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            file_path = SESSIONS_DIR / f"{stem}_{counter}.session"
            counter += 1
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return {
            "success": True,
            "data": {
                "filename": file_path.name,
                "path": str(file_path)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def process_command(command: dict) -> dict:
    """处理命令并返回结果"""
    action = command.get("action")
    params = command.get("params", {})
    command_id = command.get("command_id")
    
    if action == "list_sessions":
        result = handle_list_sessions_command(params)
    elif action == "upload_session":
        result = handle_upload_session_command(params)
    else:
        result = {
            "success": False,
            "error": f"未知命令: {action}"
        }
    
    # 添加 command_id 以便后端识别
    if command_id:
        result["command_id"] = command_id
    
    return result


# Worker 节点心跳循环示例
def worker_heartbeat_loop():
    """Worker 节点心跳循环"""
    import requests
    
    SERVER_URL = "https://aikz.usdt2026.cc"  # 从配置读取
    NODE_ID = "PC-001"  # 从配置读取
    
    while True:
        try:
            # 获取待执行的命令
            commands_response = requests.get(
                f"{SERVER_URL}/api/v1/workers/{NODE_ID}/commands",
                timeout=10
            )
            
            if commands_response.ok:
                commands_data = commands_response.json()
                commands = commands_data.get("commands", [])
                
                # 处理命令并收集响应
                command_responses = {}
                for command in commands:
                    result = process_command(command)
                    command_id = command.get("command_id")
                    if command_id:
                        command_responses[command_id] = result
            
            # 发送心跳（包含命令响应）
            heartbeat_data = {
                "node_id": NODE_ID,
                "status": "online",
                "account_count": 0,
                "accounts": [],
                "command_responses": command_responses if command_responses else None
            }
            
            heartbeat_response = requests.post(
                f"{SERVER_URL}/api/v1/workers/heartbeat",
                json=heartbeat_data,
                timeout=10
            )
            
            if heartbeat_response.ok:
                logger.info(f"心跳成功: {NODE_ID}")
            
        except Exception as e:
            logger.error(f"心跳失败: {e}")
        
        # 等待 30 秒后再次心跳
        time.sleep(30)
```

## 使用示例

### 1. 获取 Session 列表

```bash
curl -X GET "https://aikz.usdt2026.cc/api/v1/workers/PC-001/sessions?timeout=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. 上传 Session 文件

```bash
curl -X POST "https://aikz.usdt2026.cc/api/v1/workers/PC-001/sessions/upload?timeout=60" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/account1.session"
```

## 注意事项

1. **超时设置**：根据网络延迟和文件大小调整超时时间
2. **文件大小限制**：当前限制为 10MB，可根据需要调整
3. **错误处理**：Worker 节点应妥善处理各种异常情况
4. **安全性**：确保 Session 文件传输和存储的安全性
5. **并发处理**：Worker 节点应支持并发处理多个命令

## 后续优化

1. 使用 Redis Pub/Sub 实现实时通信（替代轮询）
2. 支持文件分块上传（大文件）
3. 支持 Session 文件下载
4. 支持 Session 文件删除
5. 支持批量操作

