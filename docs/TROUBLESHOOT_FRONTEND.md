# 前端服务故障排查

## 问题诊断

如果前端服务状态显示 `activating` 或未运行，请按以下步骤排查：

### 1. 检查服务状态和日志

```bash
# 查看详细服务状态
sudo systemctl status liaotian-frontend --no-pager -l

# 查看最近 50 行日志
sudo journalctl -u liaotian-frontend -n 50 --no-pager

# 实时查看日志
sudo journalctl -u liaotian-frontend -f
```

### 2. 检查前端构建产物

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

# 检查 standalone 目录是否存在
ls -la .next/standalone/

# 检查 server.js 是否存在
ls -la .next/standalone/server.js

# 检查 static 目录
ls -la .next/static/
```

### 3. 检查端口占用

```bash
# 检查端口 3000 是否被占用
sudo lsof -i :3000

# 或使用 ss 命令
sudo ss -tlnp | grep :3000
```

### 4. 手动启动前端（测试）

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

# 检查 standalone 目录
if [ -d ".next/standalone" ]; then
  cd .next/standalone
  node server.js
else
  echo "❌ 构建产物不存在，需要重新构建"
fi
```

### 5. 常见问题和解决方案

#### 问题 1: 构建产物不存在
```bash
# 重新构建前端
cd /home/ubuntu/telegram-ai-system/saas-demo
npm run build
```

#### 问题 2: 端口被占用
```bash
# 查找占用端口的进程
sudo lsof -i :3000

# 杀死进程（替换 <PID> 为实际进程 ID）
sudo kill -9 <PID>

# 重启服务
sudo systemctl restart liaotian-frontend
```

#### 问题 3: 内存不足
```bash
# 检查内存使用
free -h

# 如果内存不足，增加 Swap 或清理内存
```

#### 问题 4: 权限问题
```bash
# 检查文件权限
ls -la /home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/

# 修复权限（如果需要）
sudo chown -R ubuntu:ubuntu /home/ubuntu/telegram-ai-system/saas-demo/.next
```

### 6. 重启前端服务

```bash
# 停止服务
sudo systemctl stop liaotian-frontend

# 等待 3 秒
sleep 3

# 启动服务
sudo systemctl start liaotian-frontend

# 检查状态
sudo systemctl status liaotian-frontend --no-pager
```

### 7. 检查 Systemd 服务配置

```bash
# 查看服务配置
sudo systemctl cat liaotian-frontend

# 检查服务文件路径
cat /etc/systemd/system/liaotian-frontend.service
```

### 8. 完整修复流程

如果以上步骤都无法解决问题，执行完整修复：

```bash
cd /home/ubuntu/telegram-ai-system

# 1. 停止服务
sudo systemctl stop liaotian-frontend

# 2. 检查并重新构建（如果需要）
cd saas-demo
if [ ! -f ".next/standalone/server.js" ]; then
  echo "重新构建前端..."
  npm run build
fi
cd ..

# 3. 检查服务配置
sudo systemctl cat liaotian-frontend | grep -E "WorkingDirectory|ExecStart"

# 4. 重启服务
sudo systemctl restart liaotian-frontend

# 5. 等待并检查
sleep 5
sudo systemctl status liaotian-frontend --no-pager | head -20
```

