# Session 文件管理功能排查指南

## 问题排查步骤

### 1. 检查后端日志

#### 查看后端服务日志（Systemd）

```bash
# 查看最近的日志（最后 100 行）
sudo journalctl -u luckyred-api -n 100 --no-pager

# 实时跟踪日志
sudo journalctl -u luckyred-api -f

# 查看特定时间段的日志
sudo journalctl -u luckyred-api --since "2025-12-16 10:00:00" --until "2025-12-16 11:00:00"

# 过滤包含 "sessions" 或 "worker" 的日志
sudo journalctl -u luckyred-api -n 200 --no-pager | grep -i "session\|worker"
```

#### 查看后端 API 请求日志

```bash
# 查看包含 Session 相关 API 的日志
sudo journalctl -u luckyred-api -n 500 --no-pager | grep -E "sessions|list_sessions|upload_session|download_session|delete_session"

# 查看包含特定 Worker ID 的日志
sudo journalctl -u luckyred-api -n 500 --no-pager | grep "PC-001"

# 查看错误日志
sudo journalctl -u luckyred-api -n 200 --no-pager | grep -i "error\|exception\|traceback"
```

#### 检查后端服务状态

```bash
# 检查服务是否运行
sudo systemctl status luckyred-api

# 检查端口是否监听
sudo ss -tlnp | grep :8000

# 测试本地 API 访问
curl -v http://127.0.0.1:8000/api/v1/workers/
```

### 2. 检查 Redis 队列

#### 检查 Redis 服务状态

```bash
# 检查 Redis 是否运行
sudo systemctl status redis-server

# 检查 Redis 端口
sudo ss -tlnp | grep :6379

# 测试 Redis 连接
redis-cli ping
# 应该返回: PONG
```

#### 查看命令队列内容

```bash
# 进入 Redis CLI
redis-cli

# 查看所有 Worker 节点
SMEMBERS worker:nodes:all

# 查看特定节点的命令队列（例如：PC-001）
LRANGE worker:commands:PC-001 0 -1

# 查看命令队列长度
LLEN worker:commands:PC-001

# 查看节点的响应存储（需要知道 command_id）
# 格式：worker:response:{node_id}:{command_id}
KEYS worker:response:PC-001:*

# 查看特定响应
GET worker:response:PC-001:{command_id}

# 查看所有 Worker 节点状态
KEYS worker:node:*

# 查看特定节点状态
GET worker:node:PC-001
```

#### 监控 Redis 命令队列（实时）

```bash
# 监控所有 Redis 命令
redis-cli MONITOR

# 或者只监控特定键的操作
redis-cli --scan --pattern "worker:commands:*" | while read key; do
  echo "Queue: $key"
  redis-cli LRANGE "$key" 0 -1
done
```

#### 清理测试数据（如果需要）

```bash
# 清空特定节点的命令队列
redis-cli DEL worker:commands:PC-001

# 清空所有响应存储
redis-cli --scan --pattern "worker:response:*" | xargs redis-cli DEL

# 清空所有 Worker 节点状态（谨慎使用）
redis-cli --scan --pattern "worker:node:*" | xargs redis-cli DEL
redis-cli DEL worker:nodes:all
```

### 3. 检查 Worker 节点日志

#### 查看 Worker 节点程序日志

如果 Worker 节点是作为系统服务运行的：

```bash
# 查看服务日志（假设服务名为 worker-node）
sudo journalctl -u worker-node -n 100 --no-pager

# 实时跟踪日志
sudo journalctl -u worker-node -f
```

如果 Worker 节点是直接运行的 Python 脚本：

```bash
# 查看日志文件（如果输出到文件）
tail -f /path/to/worker.log

# 或者查看标准输出/错误
# 如果使用 nohup
tail -f nohup.out
```

#### 检查 Worker 节点心跳

```bash
# 查看 Worker 节点是否正常发送心跳
# 在后端日志中查找
sudo journalctl -u luckyred-api -n 200 --no-pager | grep "heartbeat\|心跳"

# 检查心跳频率（应该每 30 秒一次）
sudo journalctl -u luckyred-api -n 500 --no-pager | grep "PC-001" | grep "心跳"
```

#### 检查 Worker 节点命令处理

```bash
# 在 Worker 节点日志中查找命令处理记录
# 查找 "list_sessions"、"upload_session" 等关键词
grep -i "list_sessions\|upload_session\|download_session\|delete_session" /path/to/worker.log

# 查找命令处理结果
grep -i "command_id\|处理命令\|命令执行" /path/to/worker.log
```

### 4. 前端调试

#### 检查浏览器控制台

1. 打开浏览器开发者工具（F12）
2. 查看 Console 标签页的错误信息
3. 查看 Network 标签页的 API 请求：
   - 请求 URL
   - 请求状态码
   - 请求/响应内容

#### 测试 API 端点（使用 curl）

```bash
# 测试获取 Session 列表
curl -X GET "https://aikz.usdt2026.cc/api/v1/workers/PC-001/sessions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -v

# 测试上传 Session 文件
curl -X POST "https://aikz.usdt2026.cc/api/v1/workers/PC-001/sessions/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/test.session" \
  -v

# 测试下载 Session 文件
curl -X GET "https://aikz.usdt2026.cc/api/v1/workers/PC-001/sessions/test.session/download" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -v

# 测试删除 Session 文件
curl -X DELETE "https://aikz.usdt2026.cc/api/v1/workers/PC-001/sessions/test.session" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -v
```

### 5. 常见问题排查

#### 问题 1: 列表一直加载，没有数据

**可能原因：**
- Worker 节点不在线
- 命令队列未正确发送
- Worker 节点未处理命令
- 响应超时

**排查步骤：**
```bash
# 1. 检查 Worker 节点是否在线
curl -X GET "https://aikz.usdt2026.cc/api/v1/workers/" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '.workers.PC-001.status'

# 2. 检查命令是否进入队列
redis-cli LRANGE worker:commands:PC-001 0 -1

# 3. 检查 Worker 节点是否收到命令
# 查看 Worker 节点日志
grep "list_sessions" /path/to/worker.log

# 4. 检查响应是否返回
redis-cli KEYS "worker:response:PC-001:*"
```

#### 问题 2: 上传/下载/删除操作没反应

**可能原因：**
- 前端请求未发送
- 后端 API 错误
- Worker 节点未响应
- 超时设置过短

**排查步骤：**
```bash
# 1. 检查浏览器 Network 标签页，查看请求是否发送
# 2. 检查后端日志
sudo journalctl -u luckyred-api -n 50 --no-pager | grep "upload_session\|download_session\|delete_session"

# 3. 检查命令队列
redis-cli LRANGE worker:commands:PC-001 0 -1

# 4. 检查 Worker 节点日志
grep "upload_session\|download_session\|delete_session" /path/to/worker.log
```

#### 问题 3: 操作超时

**可能原因：**
- Worker 节点响应慢
- 网络延迟
- 超时设置过短

**排查步骤：**
```bash
# 1. 检查 Worker 节点心跳间隔
# 心跳间隔应该是 30 秒，如果 Worker 节点心跳间隔过长，会导致响应延迟

# 2. 增加超时时间（在前端或 API 调用中）
# 例如：?timeout=60

# 3. 检查 Worker 节点性能
# 查看 Worker 节点 CPU/内存使用情况
top -p $(pgrep -f worker_node)
```

### 6. 完整排查脚本

创建一个排查脚本 `check_session_management.sh`：

```bash
#!/bin/bash
# Session 文件管理功能排查脚本

WORKER_ID="${1:-PC-001}"
echo "=========================================="
echo "Session 文件管理功能排查"
echo "Worker ID: $WORKER_ID"
echo "=========================================="
echo ""

echo "[1/5] 检查后端服务状态"
echo "----------------------------------------"
sudo systemctl status luckyred-api --no-pager | head -10
echo ""

echo "[2/5] 检查后端日志（最近 20 行，包含 sessions）"
echo "----------------------------------------"
sudo journalctl -u luckyred-api -n 20 --no-pager | grep -i "session\|worker" || echo "未找到相关日志"
echo ""

echo "[3/5] 检查 Redis 服务状态"
echo "----------------------------------------"
sudo systemctl status redis-server --no-pager | head -5
redis-cli ping 2>/dev/null && echo "✅ Redis 连接正常" || echo "❌ Redis 连接失败"
echo ""

echo "[4/5] 检查 Worker 节点状态"
echo "----------------------------------------"
WORKER_STATUS=$(redis-cli GET "worker:node:$WORKER_ID" 2>/dev/null | jq -r '.status' 2>/dev/null || echo "unknown")
echo "Worker 状态: $WORKER_STATUS"
echo ""

echo "[5/5] 检查命令队列"
echo "----------------------------------------"
QUEUE_LEN=$(redis-cli LLEN "worker:commands:$WORKER_ID" 2>/dev/null || echo "0")
echo "命令队列长度: $QUEUE_LEN"
if [ "$QUEUE_LEN" -gt 0 ]; then
  echo "队列内容:"
  redis-cli LRANGE "worker:commands:$WORKER_ID" 0 -1 2>/dev/null | head -3
fi
echo ""

echo "=========================================="
echo "排查完成"
echo "=========================================="
```

使用方法：
```bash
chmod +x check_session_management.sh
./check_session_management.sh PC-001
```

### 7. 快速诊断命令

```bash
# 一键检查所有关键组件
echo "=== 后端服务 ===" && \
sudo systemctl is-active luckyred-api && \
echo "=== Redis 服务 ===" && \
redis-cli ping && \
echo "=== Worker 节点 ===" && \
redis-cli SMEMBERS worker:nodes:all && \
echo "=== 命令队列 ===" && \
redis-cli LLEN worker:commands:PC-001
```

## 日志关键词

在排查时，可以搜索以下关键词：

- **后端日志关键词：**
  - `list_sessions`
  - `upload_session`
  - `download_session`
  - `delete_session`
  - `command_id`
  - `等待 Worker 节点响应`
  - `命令已发送`

- **Worker 节点日志关键词：**
  - `处理命令`
  - `list_sessions`
  - `upload_session`
  - `download_session`
  - `delete_session`
  - `command_id`
  - `心跳`

- **Redis 键模式：**
  - `worker:node:*` - Worker 节点状态
  - `worker:commands:*` - 命令队列
  - `worker:response:*` - 响应存储
  - `worker:nodes:all` - 所有节点集合

## 联系支持

如果以上步骤都无法解决问题，请提供：
1. 后端日志（最近 100 行）
2. Worker 节点日志（最近 100 行）
3. Redis 命令队列内容
4. 浏览器控制台错误信息
5. Network 标签页的请求详情

