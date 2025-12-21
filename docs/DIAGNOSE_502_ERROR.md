# 502 Bad Gateway 诊断和修复指南

## 🔍 诊断命令（请在服务器上执行）

### 1. 检查应用是否在运行

```bash
# 检查端口 3000 是否被占用
sudo lsof -i :3000

# 或者使用 ss 命令
sudo ss -tlnp | grep :3000

# 检查进程
ps aux | grep -E "node.*server.js|npm.*start|next" | grep -v grep
```

### 2. 检查 PM2 状态

```bash
# 查看 PM2 进程列表
pm2 list

# 查看 PM2 日志
pm2 logs frontend --lines 50

# 查看 PM2 详细信息
pm2 describe frontend
```

### 3. 检查构建输出

```bash
cd /home/ubuntu/aizkw20251219

# 检查 .next 目录
ls -la .next/

# 检查 standalone 输出
ls -la .next/standalone/ 2>/dev/null || echo "standalone 目录不存在"

# 检查 server.js
find .next -name "server.js" -type f 2>/dev/null

# 检查 package.json
cat package.json | grep -A 5 "scripts"
```

### 4. 检查 Nginx 配置和日志

```bash
# 检查 Nginx 配置
sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc | grep -A 10 "location /"

# 检查 Nginx 错误日志
sudo tail -50 /var/log/nginx/error.log

# 检查 Nginx 访问日志
sudo tail -20 /var/log/nginx/access.log

# 测试 Nginx 配置
sudo nginx -t
```

### 5. 测试应用连接

```bash
# 测试本地应用是否响应
curl -I http://127.0.0.1:3000

# 测试完整响应
curl -v http://127.0.0.1:3000/login 2>&1 | head -30

# 检查应用日志（如果存在）
tail -50 /home/ubuntu/aizkw20251219/logs/frontend-error.log 2>/dev/null || echo "日志文件不存在"
```

### 6. 检查系统服务

```bash
# 检查 systemd 服务（如果有）
sudo systemctl status liaotian-frontend.service 2>/dev/null || echo "服务不存在"

# 检查所有相关服务
sudo systemctl list-units | grep -E "frontend|next|node"
```

## 📋 一键诊断脚本

将以下命令保存为 `diagnose.sh` 并执行：

```bash
#!/bin/bash
echo "=========================================="
echo "502 错误诊断报告"
echo "时间: $(date)"
echo "=========================================="
echo ""

echo "[1] 检查端口 3000..."
sudo lsof -i :3000 || echo "端口 3000 未被占用"
echo ""

echo "[2] 检查 PM2 状态..."
pm2 list 2>/dev/null || echo "PM2 未安装或未运行"
echo ""

echo "[3] 检查构建输出..."
cd /home/ubuntu/aizkw20251219
if [ -d ".next" ]; then
  echo "✅ .next 目录存在"
  ls -la .next/ | head -10
  if [ -f ".next/standalone/server.js" ]; then
    echo "✅ standalone/server.js 存在"
  else
    echo "❌ standalone/server.js 不存在"
    find .next -name "server.js" 2>/dev/null || echo "未找到 server.js"
  fi
else
  echo "❌ .next 目录不存在"
fi
echo ""

echo "[4] 检查应用进程..."
ps aux | grep -E "node.*server.js|npm.*start" | grep -v grep || echo "未找到应用进程"
echo ""

echo "[5] 测试本地连接..."
curl -s -o /dev/null -w "HTTP 状态码: %{http_code}\n" http://127.0.0.1:3000 || echo "无法连接到 127.0.0.1:3000"
echo ""

echo "[6] 检查 Nginx 配置..."
sudo grep -A 5 "location /" /etc/nginx/sites-available/aikz.usdt2026.cc | head -10
echo ""

echo "[7] 检查 Nginx 错误日志（最近 10 行）..."
sudo tail -10 /var/log/nginx/error.log
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
```

执行：
```bash
chmod +x diagnose.sh
./diagnose.sh
```

## 🚀 手动部署命令

### 方法 1：使用 PM2（推荐）

```bash
# 1. 进入项目目录
cd /home/ubuntu/aizkw20251219

# 2. 停止旧进程
pm2 delete frontend 2>/dev/null || true
sudo lsof -ti :3000 | xargs sudo kill -9 2>/dev/null || true

# 3. 检查构建输出
if [ -f ".next/standalone/server.js" ]; then
  echo "使用 standalone 模式"
  START_CMD="node .next/standalone/server.js"
else
  echo "使用标准模式"
  START_CMD="npm start"
fi

# 4. 设置环境变量
export NODE_ENV=production
export PORT=3000
export NODE_OPTIONS="--max-old-space-size=3072"

# 5. 启动应用（使用 PM2）
pm2 start "$START_CMD" --name frontend -- \
  --port 3000 \
  --hostname 0.0.0.0

# 6. 保存 PM2 配置
pm2 save

# 7. 查看状态
pm2 list
pm2 logs frontend --lines 20

# 8. 等待几秒后测试
sleep 5
curl -I http://127.0.0.1:3000

# 9. 重载 Nginx
sudo systemctl reload nginx
```

### 方法 2：使用 nohup（如果 PM2 不可用）

```bash
# 1. 进入项目目录
cd /home/ubuntu/aizkw20251219

# 2. 停止旧进程
sudo lsof -ti :3000 | xargs sudo kill -9 2>/dev/null || true
sleep 2

# 3. 创建日志目录
mkdir -p logs

# 4. 设置环境变量
export NODE_ENV=production
export PORT=3000
export NODE_OPTIONS="--max-old-space-size=3072"

# 5. 检查并启动
if [ -f ".next/standalone/server.js" ]; then
  echo "使用 standalone 模式启动..."
  nohup node .next/standalone/server.js > logs/frontend-out.log 2> logs/frontend-error.log &
else
  echo "使用标准模式启动..."
  nohup npm start > logs/frontend-out.log 2> logs/frontend-error.log &
fi

# 6. 记录进程 ID
APP_PID=$!
echo "应用进程 ID: $APP_PID"

# 7. 等待启动
sleep 5

# 8. 检查进程
if ps -p $APP_PID > /dev/null 2>&1; then
  echo "✅ 应用正在运行（PID: $APP_PID）"
else
  echo "❌ 应用启动失败，查看日志:"
  tail -30 logs/frontend-error.log
  exit 1
fi

# 9. 检查端口
if sudo lsof -i :3000 >/dev/null 2>&1; then
  echo "✅ 端口 3000 正在监听"
else
  echo "❌ 端口 3000 未监听"
fi

# 10. 测试连接
curl -I http://127.0.0.1:3000

# 11. 重载 Nginx
sudo systemctl reload nginx
```

### 方法 3：使用 systemd（如果已配置）

```bash
# 1. 检查服务文件
sudo systemctl status liaotian-frontend.service

# 2. 如果服务存在，重启
sudo systemctl restart liaotian-frontend.service

# 3. 查看状态
sudo systemctl status liaotian-frontend.service --no-pager -l

# 4. 查看日志
sudo journalctl -u liaotian-frontend.service -n 50 --no-pager
```

## 📸 请提供以下截图或输出

1. **诊断脚本输出**：执行 `diagnose.sh` 的完整输出
2. **PM2 状态**：`pm2 list` 的输出
3. **应用日志**：`pm2 logs frontend --lines 50` 或 `tail -50 logs/frontend-error.log`
4. **端口检查**：`sudo lsof -i :3000` 的输出
5. **构建输出**：`ls -la .next/standalone/` 的输出（如果存在）

## 🔧 常见问题和解决方案

### 问题 1：端口 3000 未被占用
**原因**：应用未启动
**解决**：执行手动部署命令

### 问题 2：standalone/server.js 不存在
**原因**：构建未完成或配置错误
**解决**：
```bash
cd /home/ubuntu/aizkw20251219
npm run build
# 检查 .next/standalone/server.js 是否存在
```

### 问题 3：应用启动后立即退出
**原因**：启动命令错误或依赖缺失
**解决**：查看错误日志，检查 Node.js 版本和依赖

### 问题 4：Nginx 无法连接
**原因**：应用绑定到 127.0.0.1 而不是 0.0.0.0
**解决**：确保启动命令包含 `--hostname 0.0.0.0` 或环境变量 `HOSTNAME=0.0.0.0`
