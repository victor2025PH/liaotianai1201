# 修复前端 502 Bad Gateway 错误

## 问题诊断

如果访问 `https://aikz.usdt2026.cc/login` 返回 502 Bad Gateway，通常是前端服务未运行。

### 1. 检查服务状态

```bash
# 检查前端服务状态
sudo systemctl status liaotian-frontend --no-pager -l

# 检查服务是否激活
sudo systemctl is-active liaotian-frontend
```

### 2. 查看服务日志

```bash
# 查看最近 50 行日志
sudo journalctl -u liaotian-frontend -n 50 --no-pager -l

# 实时查看日志
sudo journalctl -u liaotian-frontend -f
```

### 3. 检查构建产物

```bash
# 检查 server.js 是否存在
ls -la /home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/server.js

# 检查 standalone 目录结构
ls -la /home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/
```

### 4. 检查端口监听

```bash
# 检查端口 3000 是否被监听
sudo ss -tlnp | grep :3000

# 或使用 lsof
sudo lsof -i :3000
```

## 快速修复

### 方法 1: 重启服务

```bash
sudo systemctl restart liaotian-frontend
sleep 5
sudo systemctl status liaotian-frontend --no-pager | head -20
```

### 方法 2: 检查并修复服务配置

```bash
# 查看服务配置
sudo systemctl cat liaotian-frontend

# 检查关键配置项
sudo systemctl cat liaotian-frontend | grep -E "WorkingDirectory|ExecStart|User"
```

### 方法 3: 手动测试启动

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo/.next/standalone

# 手动启动测试
node server.js
```

如果手动启动成功，说明问题在 systemd 配置。

## 完整修复流程

```bash
# 1. 停止服务
sudo systemctl stop liaotian-frontend

# 2. 检查并清理端口
sudo lsof -i :3000 | grep -v COMMAND | awk '{print $2}' | xargs -r sudo kill -9

# 3. 检查构建产物
cd /home/ubuntu/telegram-ai-system/saas-demo
if [ ! -f ".next/standalone/server.js" ]; then
  echo "构建产物不存在，重新构建..."
  export NODE_OPTIONS="--max-old-space-size=4096"
  npm run build
fi

# 4. 检查文件权限
ls -la .next/standalone/server.js
sudo chown -R ubuntu:ubuntu .next/ 2>/dev/null || true

# 5. 检查服务配置
sudo systemctl cat liaotian-frontend | grep ExecStart

# 6. 启动服务
sudo systemctl start liaotian-frontend

# 7. 等待并检查
sleep 5
sudo systemctl status liaotian-frontend --no-pager | head -20

# 8. 检查端口
sudo ss -tlnp | grep :3000

# 9. 测试本地访问
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:3000
```

## 常见错误和解决方案

### 错误 1: server.js 不存在

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

### 错误 2: 权限问题

```bash
sudo chown -R ubuntu:ubuntu /home/ubuntu/telegram-ai-system/saas-demo/.next
```

### 错误 3: 端口被占用

```bash
# 查找占用端口的进程
sudo lsof -i :3000

# 杀死进程
sudo kill -9 <PID>
```

### 错误 4: Node.js 路径错误

检查服务配置中的 Node.js 路径：
```bash
which node
# 应该是 /usr/bin/node 或 /usr/local/bin/node

# 检查服务配置
sudo systemctl cat liaotian-frontend | grep ExecStart
```

### 错误 5: 工作目录错误

确保服务配置中的 WorkingDirectory 正确：
```bash
sudo systemctl cat liaotian-frontend | grep WorkingDirectory
# 应该是 /home/ubuntu/telegram-ai-system/saas-demo/.next/standalone
```

## 验证修复

```bash
# 1. 检查服务状态
sudo systemctl is-active liaotian-frontend && echo "✅ 服务运行中" || echo "❌ 服务未运行"

# 2. 检查端口监听
sudo ss -tlnp | grep :3000 && echo "✅ 端口 3000 已监听" || echo "❌ 端口 3000 未监听"

# 3. 测试本地访问
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:3000
# 应该返回 HTTP 200 或 302

# 4. 测试 HTTPS 访问
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://aikz.usdt2026.cc/login
# 应该返回 HTTP 200 或 302，不再是 502
```

