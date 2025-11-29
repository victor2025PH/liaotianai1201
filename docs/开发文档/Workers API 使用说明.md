# Workers API 使用说明

## 概述

Workers API 是一个分布式节点管理系统，用于管理多个 Worker 节点（本地电脑和远程服务器）。每个节点可以运行多个 Telegram 账号，主节点通过此 API 统一监控和控制所有 Worker 节点。

## API 端点

### 1. Worker 节点心跳

**端点**: `POST /api/v1/workers/heartbeat`

**描述**: Worker 节点应每 30 秒调用一次此端点来报告状态

**请求体**:
```json
{
  "node_id": "computer_001",
  "status": "online",
  "account_count": 3,
  "accounts": [
    {
      "phone": "+1234567890",
      "first_name": "账号1",
      "status": "online",
      "role_name": "角色1"
    }
  ],
  "metadata": {
    "cpu_usage": 45.2,
    "memory_usage": 2.1
  }
}
```

**响应**:
```json
{
  "success": true,
  "node_id": "computer_001",
  "pending_commands": [
    {
      "action": "start_auto_chat",
      "params": { "group_id": 0 },
      "timestamp": "2025-11-28T10:00:00Z"
    }
  ],
  "message": "心跳已接收"
}
```

### 2. 获取所有 Worker 节点列表

**端点**: `GET /api/v1/workers/`

**描述**: 获取所有 Worker 节点的状态列表

**响应**:
```json
{
  "workers": {
    "computer_001": {
      "node_id": "computer_001",
      "status": "online",
      "account_count": 3,
      "last_heartbeat": "2025-11-28T10:00:00Z",
      "accounts": [...],
      "metadata": {}
    },
    "computer_002": {
      "node_id": "computer_002",
      "status": "online",
      "account_count": 2,
      "last_heartbeat": "2025-11-28T10:00:15Z",
      "accounts": [...],
      "metadata": {}
    }
  }
}
```

### 3. 获取节点的待执行命令

**端点**: `GET /api/v1/workers/{node_id}/commands`

**描述**: Worker 节点调用此端点获取待执行的命令

**响应**:
```json
{
  "success": true,
  "node_id": "computer_001",
  "commands": [
    {
      "action": "start_auto_chat",
      "params": { "group_id": 0 },
      "timestamp": "2025-11-28T10:00:00Z",
      "from": "master"
    }
  ]
}
```

### 4. 向特定节点发送命令

**端点**: `POST /api/v1/workers/{node_id}/commands`

**描述**: 主节点向特定 Worker 节点发送命令

**请求体**:
```json
{
  "action": "start_auto_chat",
  "params": {
    "group_id": 0
  }
}
```

**响应**:
```json
{
  "success": true,
  "node_id": "computer_001",
  "action": "start_auto_chat",
  "message": "命令已发送到节点 computer_001"
}
```

### 5. 广播命令到所有节点

**端点**: `POST /api/v1/workers/broadcast`

**描述**: 向所有在线 Worker 节点广播命令

**请求体**:
```json
{
  "action": "set_config",
  "params": {
    "chat_interval_min": 30,
    "chat_interval_max": 120,
    "auto_chat_enabled": true,
    "redpacket_enabled": true,
    "redpacket_interval": 300
  }
}
```

**响应**:
```json
{
  "success": true,
  "action": "set_config",
  "nodes_count": 2,
  "nodes": ["computer_001", "computer_002"],
  "message": "命令已广播到 2 个节点"
}
```

### 6. 清除节点的命令队列

**端点**: `DELETE /api/v1/workers/{node_id}/commands`

**描述**: Worker 节点执行完命令后调用此端点清除命令队列

**响应**:
```json
{
  "success": true,
  "node_id": "computer_001",
  "message": "命令队列已清除"
}
```

## Worker 节点实现示例

### Python 示例

```python
import requests
import time
import json
from typing import List, Dict, Any

class WorkerClient:
    def __init__(self, node_id: str, master_url: str = "http://aikz.usdt2026.cc"):
        self.node_id = node_id
        self.master_url = master_url
        self.api_base = f"{master_url}/api/v1/workers"
        self.accounts = []  # 存储账号列表
        
    def send_heartbeat(self, accounts: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """发送心跳"""
        try:
            response = requests.post(
                f"{self.api_base}/heartbeat",
                json={
                    "node_id": self.node_id,
                    "status": "online",
                    "account_count": len(accounts),
                    "accounts": accounts,
                    "metadata": metadata or {}
                },
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            # 检查是否有待执行的命令
            if data.get("pending_commands"):
                return data["pending_commands"]
            return []
        except Exception as e:
            print(f"发送心跳失败: {e}")
            return []
    
    def get_commands(self) -> List[Dict[str, Any]]:
        """获取待执行的命令"""
        try:
            response = requests.get(
                f"{self.api_base}/{self.node_id}/commands",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return data.get("commands", [])
        except Exception as e:
            print(f"获取命令失败: {e}")
            return []
    
    def clear_commands(self):
        """清除命令队列"""
        try:
            requests.delete(
                f"{self.api_base}/{self.node_id}/commands",
                timeout=5
            )
        except Exception as e:
            print(f"清除命令队列失败: {e}")
    
    def execute_command(self, command: Dict[str, Any]):
        """执行命令"""
        action = command.get("action")
        params = command.get("params", {})
        
        print(f"执行命令: {action}, 参数: {params}")
        
        if action == "start_auto_chat":
            # 启动自动聊天
            self.start_auto_chat(params)
        elif action == "stop_auto_chat":
            # 停止自动聊天
            self.stop_auto_chat()
        elif action == "set_config":
            # 设置配置
            self.set_config(params)
        elif action == "create_group":
            # 创建群组
            self.create_group(params)
        else:
            print(f"未知命令: {action}")
    
    def start_auto_chat(self, params: Dict[str, Any]):
        """启动自动聊天"""
        print("启动自动聊天...")
        # 实现启动自动聊天的逻辑
        
    def stop_auto_chat(self):
        """停止自动聊天"""
        print("停止自动聊天...")
        # 实现停止自动聊天的逻辑
        
    def set_config(self, config: Dict[str, Any]):
        """设置配置"""
        print(f"设置配置: {config}")
        # 实现设置配置的逻辑
        
    def create_group(self, params: Dict[str, Any]):
        """创建群组"""
        print(f"创建群组: {params}")
        # 实现创建群组的逻辑
    
    def run(self):
        """运行 Worker 节点主循环"""
        print(f"Worker 节点 {self.node_id} 启动...")
        
        while True:
            try:
                # 1. 发送心跳
                commands = self.send_heartbeat(self.accounts)
                
                # 2. 执行收到的命令
                for command in commands:
                    self.execute_command(command)
                
                # 3. 清除命令队列（如果执行了命令）
                if commands:
                    self.clear_commands()
                
                # 4. 等待 30 秒后再次发送心跳
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("Worker 节点停止...")
                break
            except Exception as e:
                print(f"Worker 节点错误: {e}")
                time.sleep(30)


# 使用示例
if __name__ == "__main__":
    # 创建 Worker 客户端
    worker = WorkerClient(
        node_id="computer_001",
        master_url="http://aikz.usdt2026.cc"
    )
    
    # 设置账号列表（从本地数据库或配置文件读取）
    worker.accounts = [
        {
            "phone": "+1234567890",
            "first_name": "账号1",
            "status": "online",
            "role_name": "角色1"
        }
    ]
    
    # 运行 Worker
    worker.run()
```

## 支持的命令

### 1. `start_auto_chat`
启动自动聊天

**参数**:
```json
{
  "group_id": 0  // 0 表示所有群组
}
```

### 2. `stop_auto_chat`
停止自动聊天

**参数**: 无

### 3. `set_config`
设置自动化配置

**参数**:
```json
{
  "chat_interval_min": 30,
  "chat_interval_max": 120,
  "auto_chat_enabled": true,
  "redpacket_enabled": true,
  "redpacket_interval": 300
}
```

### 4. `create_group`
创建群组

**参数**:
```json
{
  "creator_phone": "+1234567890",
  "title": "群组名称",
  "description": "群组描述"
}
```

## 节点状态管理

- **在线状态**: 节点在 120 秒内有心跳，状态为 `online`
- **离线状态**: 节点超过 120 秒没有心跳，状态自动变为 `offline`
- **心跳间隔**: 建议每 30 秒发送一次心跳

## 存储机制

- **Redis 优先**: 如果配置了 Redis，使用 Redis 存储节点状态和命令队列
- **内存降级**: 如果 Redis 不可用，自动降级到内存存储
- **数据过期**: 节点状态 TTL 为 120 秒，命令队列 TTL 为 5 分钟

## 注意事项

1. Worker 节点应定期发送心跳（建议 30 秒一次）
2. Worker 节点应在发送心跳后检查并执行待执行的命令
3. 执行完命令后应清除命令队列
4. 节点 ID 应唯一，建议使用 `computer_001`, `computer_002` 等格式
5. 账号列表应包含账号的基本信息（phone, first_name, status, role_name 等）

