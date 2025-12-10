# 服务器端部署命令清单

## 🚀 快速部署（推荐）

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/deploy-frontend-standalone.sh
```

## 📋 手动部署步骤

### 步骤 1：进入项目目录

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo
```

### 步骤 2：安装依赖并构建

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20.19.6
npm install --production=false
npm run build
```

### 步骤 3：检查构建结果

```bash
# 检查 standalone 文件
ls -la .next/standalone/server.js

# 检查 static 文件
ls -la .next/static/chunks | head -5

# 如果 standalone 中没有 static，复制过去
if [ ! -d ".next/standalone/.next/static" ]; then
  cp -r .next/static .next/standalone/.next/
fi
```

### 步骤 4：安装 systemd 服务

```bash
# 停止现有服务
sudo systemctl stop liaotian-frontend.service 2>/dev/null || true

# 复制服务文件
cd /home/ubuntu/telegram-ai-system
sudo cp deploy/systemd/liaotian-frontend.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable liaotian-frontend.service

# 启动服务
sudo systemctl start liaotian-frontend.service

# 等待启动
sleep 5

# 检查状态
sudo systemctl status liaotian-frontend.service --no-pager -l | head -30
```

### 步骤 5：验证部署

```bash
# 检查端口
ss -tlnp | grep :3000

# 检查进程
ps aux | grep -E "node.*server.js" | grep -v grep

# 测试 HTTP
curl -I http://127.0.0.1:3000/

# 测试静态资源
cd /home/ubuntu/telegram-ai-system/saas-demo
one_file=$(ls .next/static/chunks 2>/dev/null | head -n 1)
echo "测试文件: $one_file"
curl -I "http://127.0.0.1:3000/_next/static/chunks/$one_file"
```

## 🔍 排查 OOM 问题

如果服务被 Killed（status=9/KILL），执行：

```bash
# 查看 OOM 日志
dmesg --ctime | grep -i -E 'killed process|out of memory' | tail -n 20

# 或
journalctl -k -n 50 | grep -i -E 'killed process|out of memory'

# 查看内存使用
free -h
ps aux --sort=-%mem | head -10
```

如果确认是 OOM，编辑服务文件：

```bash
sudo nano /etc/systemd/system/liaotian-frontend.service
```

修改 `Environment=NODE_OPTIONS=--max-old-space-size=1024`（如果还没有）

然后：

```bash
sudo systemctl daemon-reload
sudo systemctl restart liaotian-frontend.service
```

## 📝 查看日志

```bash
# 实时查看日志
sudo journalctl -u liaotian-frontend.service -f

# 查看最近 50 条
sudo journalctl -u liaotian-frontend.service -n 50 --no-pager
```

## 🔄 重新部署

```bash
# 停止服务
sudo systemctl stop liaotian-frontend.service

# 进入项目目录
cd /home/ubuntu/telegram-ai-system/saas-demo

# 拉取最新代码（如果使用 Git）
git pull origin main

# 重新构建
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20.19.6
npm install --production=false
npm run build

# 复制 static 文件
if [ ! -d ".next/standalone/.next/static" ]; then
  cp -r .next/static .next/standalone/.next/
fi

# 启动服务
sudo systemctl start liaotian-frontend.service

# 检查状态
sudo systemctl status liaotian-frontend.service --no-pager -l
```

