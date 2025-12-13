# 修复 502 错误和 Worker 节点问题

## 诊断结果分析

根据诊断结果，发现以下问题：

1. **502 Bad Gateway 错误** - HTTP 和健康检查端点返回 502
2. **心跳端点正常** - 返回 200，说明后端服务部分可用
3. **Worker 节点未运行** - 未找到 Worker 进程
4. **Windows 防火墙已开启** - 可能阻止出站连接

## 问题 1: 502 Bad Gateway 错误

### 原因
502 错误通常表示 Nginx 无法连接到后端服务（端口 8000）。

### 解决方案

#### 在服务器上执行：

```bash
# 1. 检查后端服务状态
sudo systemctl status luckyred-api
# 或
sudo systemctl status telegram-backend

# 2. 如果服务未运行，启动服务
sudo systemctl start luckyred-api

# 3. 检查端口 8000 是否监听
sudo ss -tlnp | grep 8000

# 4. 如果端口未监听，检查服务日志
sudo journalctl -u luckyred-api -n 50 --no-pager

# 5. 测试本地健康检查
curl http://localhost:8000/health

# 6. 如果本地健康检查失败，修复后端服务
sudo bash scripts/server/fix-502-bad-gateway-complete.sh

# 7. 重新加载 Nginx
sudo systemctl reload nginx

# 8. 验证修复
curl https://aikz.usdt2026.cc/health
```

#### 快速修复脚本：

```bash
# 在服务器上运行
cd /home/ubuntu/telegram-ai-system
bash scripts/server/fix-502-bad-gateway-complete.sh
```

## 问题 2: Worker 节点未运行

### 原因
Worker 节点进程未启动，无法接收启动命令。

### 解决方案

#### 在 Worker 节点上执行：

```bash
# 1. 进入项目目录（根据实际路径调整）
cd /path/to/telegram-ai-system

# 2. 检查 Worker 配置文件
ls -la worker_config.py config.py

# 3. 检查 Worker 启动脚本
ls -la worker.py worker_node.py start_worker.sh

# 4. 启动 Worker 节点（根据实际脚本调整）
# 方式 1: 直接运行
python worker.py

# 方式 2: 使用启动脚本
bash start_worker.sh

# 方式 3: 使用 systemd 服务（如果已配置）
sudo systemctl start telegram-worker
sudo systemctl enable telegram-worker  # 设置开机自启

# 5. 检查 Worker 进程
ps aux | grep worker

# 6. 检查 Worker 日志
tail -f logs/worker.log
# 或
journalctl -u telegram-worker -f
```

#### Windows Worker 节点：

```cmd
REM 1. 进入项目目录
cd D:\telegram-ai-system

REM 2. 检查配置文件
dir worker_config.py config.py

REM 3. 启动 Worker 节点
python worker.py

REM 4. 检查进程
tasklist | findstr python
```

## 问题 3: 在服务器上获取诊断脚本

### 解决方案

```bash
# 1. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 2. 拉取最新代码
git pull origin main

# 3. 确保脚本有执行权限
chmod +x scripts/server/*.sh

# 4. 运行诊断脚本
bash scripts/server/diagnose-worker-complete.sh
```

## 问题 4: Windows 防火墙

### 解决方案

虽然 Windows 防火墙已开启，但通常不会阻止出站 HTTPS 连接。如果确实需要配置：

```cmd
REM 允许出站 HTTPS 连接（通常不需要，因为默认允许出站）
netsh advfirewall firewall add rule name="Allow HTTPS Outbound" dir=out action=allow protocol=TCP localport=443
```

## 完整修复流程

### 步骤 1: 修复后端服务（在服务器上）

```bash
# SSH 连接到服务器
ssh ubuntu@165.154.235.170

# 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 拉取最新代码
git pull origin main

# 修复 502 错误
sudo bash scripts/server/fix-502-bad-gateway-complete.sh

# 验证后端服务
curl http://localhost:8000/health
curl https://aikz.usdt2026.cc/health
```

### 步骤 2: 启动 Worker 节点

#### 在 Windows Worker 节点上：

```cmd
cd D:\telegram-ai-system
python worker.py
```

#### 在 Linux Worker 节点上：

```bash
cd /path/to/telegram-ai-system
python worker.py
# 或使用 systemd 服务
sudo systemctl start telegram-worker
```

### 步骤 3: 验证修复

```bash
# 1. 检查后端服务
curl https://aikz.usdt2026.cc/health
curl https://aikz.usdt2026.cc/api/v1/workers/heartbeat -X POST \
  -H "Content-Type: application/json" \
  -d '{"node_id":"test","status":"online","account_count":0,"accounts":[]}'

# 2. 检查 Worker 节点
# 在 Worker 节点上检查进程
ps aux | grep worker

# 3. 在前端测试
# 点击"一键启动所有账号"，查看是否还有错误
```

## 常见问题

### Q: 为什么心跳端点返回 200，但健康检查返回 502？

A: 这可能是因为：
- 健康检查端点路径不同（`/health` vs `/api/v1/workers/heartbeat`）
- Nginx 配置中健康检查的代理设置有问题
- 后端服务部分功能正常，但健康检查端点有问题

**解决方案：**
```bash
# 检查 Nginx 配置
sudo nginx -t
cat /etc/nginx/sites-available/aikz.conf | grep -A 5 "location /health"

# 检查后端服务日志
sudo journalctl -u luckyred-api -n 100 --no-pager | grep -i health
```

### Q: Worker 节点启动后立即退出？

A: 检查以下内容：
1. 配置文件是否正确
2. 服务器 URL 是否可访问
3. 日志中的错误信息

**解决方案：**
```bash
# 查看 Worker 日志
tail -f logs/worker.log

# 检查配置文件
cat worker_config.py | grep SERVER_URL

# 测试服务器连接
curl https://aikz.usdt2026.cc/api/v1/workers/heartbeat
```

### Q: 如何让 Worker 节点在后台运行？

**Linux:**
```bash
# 使用 nohup
nohup python worker.py > logs/worker.log 2>&1 &

# 或使用 systemd 服务
sudo systemctl start telegram-worker
sudo systemctl enable telegram-worker
```

**Windows:**
```cmd
REM 使用 start 命令在后台运行
start /B python worker.py > logs\worker.log 2>&1
```

## 验证清单

修复完成后，请确认：

- [ ] 后端服务正在运行（`systemctl status luckyred-api`）
- [ ] 端口 8000 正在监听（`ss -tlnp | grep 8000`）
- [ ] 本地健康检查成功（`curl http://localhost:8000/health`）
- [ ] 公共健康检查成功（`curl https://aikz.usdt2026.cc/health`）
- [ ] 心跳端点可访问（返回 200 或 401/403）
- [ ] Worker 节点进程正在运行（`ps aux | grep worker`）
- [ ] Worker 节点能发送心跳（查看后端日志）
- [ ] 前端"一键启动所有账号"功能正常

## 相关文档

- [Worker 连接诊断指南](./WORKER_CONNECTION_TROUBLESHOOTING.md)
- [502 错误修复指南](./QUICK_FIX_BACKEND_CONNECTION.md)
- [部署步骤](./DEPLOYMENT_STEPS.md)

