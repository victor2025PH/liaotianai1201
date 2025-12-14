# Worker 节点部署修复指南

## 问题描述

"一键启动所有账号"失败，错误信息显示：
- `账号未在 AccountManager 中`
- Windows Worker 节点无法连接到后端服务器
- 健康检查端点和心跳端点不可访问（状态码 000）

## 问题分析

### 1. 账号未在 AccountManager 中的原因

从代码 `admin-backend/app/api/group_ai/chat_features.py` 第615-626行可以看到：

```python
if account_id not in service_manager.account_manager.accounts:
    # 如果不在內存中，嘗試啟動賬號
    logger.info(f"賬號 {account_id} 不在內存中，嘗試啟動...")
    try:
        success = await service_manager.start_account(account_id)
        if not success:
            if not account:
                error_details.append("賬號未在 AccountManager 中")
```

**原因：**
- 账号需要先被添加到 `AccountManager` 中
- `AccountManager` 需要从 session 文件加载账号
- 如果 session 文件不存在或路径不对，账号就无法加载
- Worker 节点没有正确上报账号信息到后端

### 2. Worker 节点连接问题

从诊断脚本输出看：
- **健康检查端点不可访问**（状态码 000）
- **心跳端点不可访问**（状态码 000）
- **未找到 Worker 配置文件**
- **未找到 Worker 进程**

这说明：
1. Worker 节点可能没有运行
2. Worker 节点无法连接到后端服务器 `https://aikz.usdt2026.cc`
3. Worker 节点代码可能需要更新

## 解决方案

### 步骤 1: 检查 Worker 节点代码

检查本地 Windows 电脑上的 Worker 节点代码是否存在且最新：

```bash
# 在 Windows 电脑上检查
cd D:\telegram-ai-system  # 或你的项目路径

# 检查是否有 Worker 节点代码
dir /s /b *worker*.py
dir /s /b *worker*.bat
```

### 步骤 2: 更新 Worker 节点代码

如果代码不存在或需要更新，需要：

1. **从服务器拉取最新代码**（如果本地是 Git 仓库）：
   ```bash
   git pull origin main
   ```

2. **或者从服务器下载 Worker 节点代码**：
   - Worker 节点应该能够：
     - 连接到 `https://aikz.usdt2026.cc/api/v1/workers/heartbeat`
     - 每30秒发送一次心跳
     - 上报账号列表

### 步骤 3: 检查 Worker 节点配置

Worker 节点需要配置：

1. **服务器 URL**：
   ```
   SERVER_URL=https://aikz.usdt2026.cc
   ```

2. **节点 ID**：
   ```
   NODE_ID=pc-001  # 或 pc-002
   ```

3. **Session 文件路径**：
   ```
   SESSION_DIR=./sessions
   ```

### 步骤 4: 启动 Worker 节点

在 Windows 电脑上启动 Worker 节点：

```bash
# 方法 1: 如果有启动脚本
python worker_node.py

# 方法 2: 如果有批处理文件
worker_start.bat

# 方法 3: 直接运行 Python 脚本
python -m group_ai_service.worker_node
```

### 步骤 5: 验证 Worker 节点连接

1. **检查 Worker 节点是否在运行**：
   ```bash
   # Windows
   tasklist | findstr python
   
   # 或检查进程
   Get-Process | Where-Object {$_.ProcessName -like "*python*"}
   ```

2. **检查 Worker 节点日志**：
   - 查看是否有连接错误
   - 查看是否有心跳发送成功的消息

3. **检查后端是否收到心跳**：
   ```bash
   # 在服务器上
   curl https://aikz.usdt2026.cc/api/v1/workers/ | python3 -m json.tool
   ```

### 步骤 6: 检查账号 Session 文件

确保账号的 session 文件存在且路径正确：

```bash
# 在 Windows 电脑上
dir sessions\*.session

# 检查文件是否完整
# session 文件应该以账号 ID 命名，如：639952948592.session
```

### 步骤 7: 重新部署 Worker 节点（如果需要）

如果 Worker 节点代码不存在或需要更新：

1. **创建 Worker 节点脚本**（如果不存在）：
   - 参考 `admin-backend/legacy_workers/worker_client_example.py`
   - 或使用现有的 Worker 节点代码

2. **配置 Worker 节点**：
   - 设置服务器 URL
   - 设置节点 ID
   - 设置 Session 文件路径

3. **启动 Worker 节点**：
   - 确保能够连接到后端服务器
   - 确保能够发送心跳
   - 确保能够上报账号列表

## 快速修复步骤

### 在 Windows 电脑上执行：

1. **检查代码是否需要更新**：
   ```bash
   cd D:\telegram-ai-system
   git pull origin main
   ```

2. **检查 Worker 节点是否运行**：
   ```bash
   tasklist | findstr python
   ```

3. **如果 Worker 节点未运行，启动它**：
   ```bash
   # 查找启动脚本
   dir /s /b *worker*.bat
   dir /s /b *worker*.py
   
   # 运行启动脚本
   python worker_node.py
   ```

4. **检查连接**：
   ```bash
   # 测试后端连接
   curl https://aikz.usdt2026.cc/api/v1/health
   
   # 测试心跳端点
   curl -X POST https://aikz.usdt2026.cc/api/v1/workers/heartbeat ^
        -H "Content-Type: application/json" ^
        -d "{\"node_id\":\"pc-001\",\"status\":\"online\",\"account_count\":0}"
   ```

## 常见问题

### Q1: Worker 节点代码在哪里？

**A:** Worker 节点代码可能在以下位置：
- `admin-backend/legacy_workers/worker_client_example.py`
- `group_ai_service/` 目录下
- 或者需要从服务器下载

### Q2: 如何知道 Worker 节点是否在运行？

**A:** 
- 检查进程：`tasklist | findstr python`
- 检查日志文件
- 检查后端是否收到心跳

### Q3: Worker 节点无法连接到服务器？

**A:** 检查：
1. 网络连接是否正常
2. 防火墙是否允许出站 HTTPS 连接（端口 443）
3. 服务器 URL 是否正确：`https://aikz.usdt2026.cc`
4. SSL 证书是否有效

### Q4: 账号未在 AccountManager 中？

**A:** 需要：
1. Worker 节点正确上报账号信息
2. Session 文件存在且路径正确
3. 账号已添加到数据库并标记为活跃

## 验证清单

- [ ] Worker 节点代码已更新到最新版本
- [ ] Worker 节点正在运行
- [ ] Worker 节点能够连接到后端服务器
- [ ] Worker 节点能够发送心跳
- [ ] Worker 节点能够上报账号列表
- [ ] Session 文件存在且路径正确
- [ ] 账号已在数据库中标记为活跃
- [ ] 后端能够收到 Worker 节点的心跳
- [ ] "一键启动所有账号"功能正常工作

## 下一步

修复后，再次尝试"一键启动所有账号"，应该能够：
1. 找到所有在线账号
2. 成功启动账号
3. 显示详细的成功/失败信息

