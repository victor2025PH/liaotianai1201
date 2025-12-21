# 快速修复命令（复制粘贴）

> **问题**: 端口 3001, 3002, 3003 无法连接，网站无法访问

---

## 🚀 立即修复（在服务器上执行）

```bash
# 1. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 2. 运行全面修复脚本（注意：是 scripts/server/comprehensive-fix.sh）
bash scripts/server/comprehensive-fix.sh
```

---

## 🔍 如果脚本不存在或失败，手动执行

### 步骤 1: 检查当前状态

```bash
# 检查 PM2 进程（应该看到三个新网站的服务）
pm2 list

# 检查端口（应该看到 3001, 3002, 3003 在监听）
sudo lsof -i :3001
sudo lsof -i :3002
sudo lsof -i :3003
```

### 步骤 2: 停止旧的 frontend 进程（如果需要）

```bash
# 如果旧的 frontend 占用了端口，停止它
pm2 delete frontend
pm2 save
```

### 步骤 3: 部署第一个网站 (tgmini)

```bash
cd /home/ubuntu/telegram-ai-system/tgmini20251220

# 清理
rm -rf node_modules/.cache dist

# 安装依赖
npm install --legacy-peer-deps

# 构建
export NODE_OPTIONS="--max-old-space-size=3072"
npm run build

# 停止旧进程
pm2 delete tgmini-frontend 2>/dev/null || true
sudo lsof -ti :3001 | xargs sudo kill -9 2>/dev/null || true

# 启动服务
pm2 start serve --name tgmini-frontend -- dist --listen 3001 --single
pm2 save

# 验证
sleep 3
curl http://127.0.0.1:3001
```

### 步骤 4: 部署第二个网站 (hongbao)

```bash
cd /home/ubuntu/telegram-ai-system/hbwy20251220

# 清理
rm -rf node_modules/.cache dist

# 安装依赖
npm install --legacy-peer-deps

# 构建
export NODE_OPTIONS="--max-old-space-size=3072"
npm run build

# 停止旧进程
pm2 delete hongbao-frontend 2>/dev/null || true
sudo lsof -ti :3002 | xargs sudo kill -9 2>/dev/null || true

# 启动服务
pm2 start serve --name hongbao-frontend -- dist --listen 3002 --single
pm2 save

# 验证
sleep 3
curl http://127.0.0.1:3002
```

### 步骤 5: 部署第三个网站 (aizkw)

```bash
cd /home/ubuntu/telegram-ai-system/aizkw20251219

# 清理
rm -rf node_modules/.cache dist

# 安装依赖
npm install --legacy-peer-deps

# 构建
export NODE_OPTIONS="--max-old-space-size=3072"
npm run build

# 停止旧进程
pm2 delete aizkw-frontend 2>/dev/null || true
sudo lsof -ti :3003 | xargs sudo kill -9 2>/dev/null || true

# 启动服务
pm2 start serve --name aizkw-frontend -- dist --listen 3003 --single
pm2 save

# 验证
sleep 3
curl http://127.0.0.1:3003
```

---

## 📊 验证部署

```bash
# 检查 PM2 进程（应该看到三个新网站）
pm2 list

# 检查端口
sudo lsof -i :3001
sudo lsof -i :3002
sudo lsof -i :3003

# 测试本地访问
curl http://127.0.0.1:3001
curl http://127.0.0.1:3002
curl http://127.0.0.1:3003
```

---

## ⚠️ 常见问题

### 问题 1: 命令打错

**错误**: `bash script`  
**正确**: `bash scripts/server/comprehensive-fix.sh`

### 问题 2: PM2 显示旧进程

**现象**: PM2 显示 `backend` 和 `frontend`，但没有 `tgmini-frontend`、`hongbao-frontend`、`aizkw-frontend`

**解决**: 需要部署三个新网站的服务

### 问题 3: 端口无法连接

**原因**: 
- 服务未启动
- 端口被其他进程占用
- 构建失败

**解决**: 运行全面修复脚本或手动部署

---

**最后更新**: 2025-12-21
