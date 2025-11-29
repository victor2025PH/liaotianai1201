# 修复 Worker 节点配置

## 问题

1. Worker 节点尝试连接到 `jblt.usdt2026.cc:8000`，但主节点应该是 `aikz.usdt2026.cc`
2. 心跳发送失败 422，可能是请求格式不对

## 解决方案

### 1. 检查 Worker 节点配置

在 `computer_001` 和 `computer_002` 上，检查配置文件中的主节点 URL：

```bash
# 查找配置文件
grep -r "jblt.usdt2026.cc" /path/to/worker/config
grep -r "MASTER" /path/to/worker/config
```

### 2. 修改主节点 URL

将主节点 URL 从 `jblt.usdt2026.cc` 改为 `aikz.usdt2026.cc`：

```python
# 在 Worker 节点的配置文件中
MASTER_URL = "http://aikz.usdt2026.cc"  # 或 "https://aikz.usdt2026.cc"
```

### 3. 检查心跳请求格式

Worker 节点应该发送以下格式的心跳请求：

```python
POST http://aikz.usdt2026.cc/api/v1/workers/heartbeat
Content-Type: application/json

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
  "metadata": {}
}
```

### 4. 验证修复

1. 修改配置后重启 Worker 节点
2. 检查日志，应该看到心跳成功
3. 在前端页面应该能看到节点在线

## 快速修复命令

在 Worker 节点上执行：

```bash
# 1. 查找配置文件
find . -name "*.py" -o -name "*.json" -o -name "*.env" | xargs grep -l "jblt.usdt2026.cc"

# 2. 替换主节点 URL
sed -i 's/jblt.usdt2026.cc/aikz.usdt2026.cc/g' /path/to/config/file

# 3. 重启 Worker 节点
# (根据实际启动方式)
```

