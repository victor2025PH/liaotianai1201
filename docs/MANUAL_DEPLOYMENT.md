# 手动部署命令

## 完整部署流程

### 1. 进入项目目录
```bash
cd /home/ubuntu/telegram-ai-system
```

### 2. 拉取最新代码
```bash
git pull origin main
```

### 3. 构建前端
```bash
cd saas-demo
npm install --prefer-offline --no-audit --no-fund
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
cd ..
```

### 4. 安装后端依赖
```bash
cd admin-backend
source venv/bin/activate
pip install -r requirements.txt --quiet
cd ..
```

### 5. 重启服务
```bash
sudo systemctl restart luckyred-api
sudo systemctl restart liaotian-frontend
sudo systemctl restart nginx
```

### 6. 等待服务启动
```bash
sleep 5
```

### 7. 验证服务（可选）
```bash
# 检查后端服务状态
sudo systemctl status luckyred-api

# 检查前端服务状态
sudo systemctl status liaotian-frontend

# 检查 Nginx 状态
sudo systemctl status nginx

# 测试 HTTPS 访问
curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/login
curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/api/v1/health
```

---

## 一键执行脚本

将以下命令复制粘贴到终端一次性执行：

```bash
cd /home/ubuntu/telegram-ai-system && \
git pull origin main && \
cd saas-demo && \
npm install --prefer-offline --no-audit --no-fund && \
export NODE_OPTIONS="--max-old-space-size=4096" && \
npm run build && \
cd ../admin-backend && \
source venv/bin/activate && \
pip install -r requirements.txt --quiet && \
cd .. && \
sudo systemctl restart luckyred-api && \
sudo systemctl restart liaotian-frontend && \
sudo systemctl restart nginx && \
echo "✅ 部署完成，等待服务启动..." && \
sleep 5 && \
echo "✅ 服务已重启"
```

---

## 分步骤执行（推荐）

### 步骤 1: 拉取代码
```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
```

### 步骤 2: 构建前端
```bash
cd saas-demo
npm install --prefer-offline --no-audit --no-fund
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
cd ..
```

**注意：** 如果构建卡死，按 `Ctrl+C` 中断，然后检查是否有构建产物：
```bash
ls -la saas-demo/.next/standalone/server.js
```
如果文件存在，可以跳过构建步骤。

### 步骤 3: 安装后端依赖
```bash
cd admin-backend
source venv/bin/activate
pip install -r requirements.txt --quiet
cd ..
```

### 步骤 4: 重启服务
```bash
sudo systemctl restart luckyred-api
sudo systemctl restart liaotian-frontend
sudo systemctl restart nginx
```

### 步骤 5: 验证部署
```bash
# 等待 5 秒
sleep 5

# 检查服务状态
sudo systemctl status luckyred-api --no-pager | head -10
sudo systemctl status liaotian-frontend --no-pager | head -10
```

---

## 快速命令（仅重启服务，不构建）

如果代码没有变化，只需要重启服务：

```bash
sudo systemctl restart luckyred-api liaotian-frontend nginx
```

---

## 故障排查

### 如果前端构建失败
```bash
# 查看构建日志
cd /home/ubuntu/telegram-ai-system/saas-demo
npm run build 2>&1 | tee build.log

# 检查内存使用
free -h

# 检查磁盘空间
df -h
```

### 如果服务启动失败
```bash
# 查看后端日志
sudo journalctl -u luckyred-api -n 50 --no-pager

# 查看前端日志（重要：如果前端服务未运行）
sudo journalctl -u liaotian-frontend -n 50 --no-pager -l

# 查看前端服务详细状态
sudo systemctl status liaotian-frontend --no-pager -l

# 查看 Nginx 日志
sudo tail -50 /var/log/nginx/error.log

# 如果前端服务卡在 activating 状态
sudo systemctl stop liaotian-frontend
sleep 3
sudo systemctl start liaotian-frontend
sudo systemctl status liaotian-frontend --no-pager
```

### 如果端口被占用
```bash
# 检查端口 8000（后端）
sudo lsof -i :8000

# 检查端口 3000（前端）
sudo lsof -i :3000

# 杀死占用端口的进程
sudo kill -9 <PID>
```

