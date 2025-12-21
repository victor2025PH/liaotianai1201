# 立即修复部署问题

> **问题**: GitHub Actions 部署失败，网站无法访问

---

## 🚀 快速修复（推荐）

### 方法 1: 在服务器上运行快速修复脚本

```bash
# SSH 到服务器
ssh ubuntu@<SERVER_HOST>

# 下载并运行修复脚本
cd /home/ubuntu/telegram-ai-system
git pull origin main
bash scripts/server/quick-fix-deployment.sh
```

### 方法 2: 手动部署

```bash
# SSH 到服务器
ssh ubuntu@<SERVER_HOST>

cd /home/ubuntu/telegram-ai-system

# 拉取最新代码
git pull origin main

# 部署第一个网站 (tgmini)
cd tgmini20251220
npm install
export NODE_OPTIONS="--max-old-space-size=3072"
npm run build
pm2 delete tgmini-frontend 2>/dev/null || true
pm2 start serve --name tgmini-frontend -- dist --listen 3001 --single
pm2 save

# 部署第二个网站 (hongbao)
cd ../hbwy20251220
npm install
export NODE_OPTIONS="--max-old-space-size=3072"
npm run build
pm2 delete hongbao-frontend 2>/dev/null || true
pm2 start serve --name hongbao-frontend -- dist --listen 3002 --single
pm2 save

# 部署第三个网站 (aizkw)
cd ../aizkw20251219
npm install
export NODE_OPTIONS="--max-old-space-size=3072"
npm run build
pm2 delete aizkw-frontend 2>/dev/null || true
pm2 start serve --name aizkw-frontend -- dist --listen 3003 --single
pm2 save
```

---

## 🔍 诊断问题

### 步骤 1: 检查服务器状态

```bash
# SSH 到服务器
ssh ubuntu@<SERVER_HOST>

# 运行诊断脚本
cd /home/ubuntu/telegram-ai-system
bash scripts/server/check-deployment-status.sh
```

### 步骤 2: 检查 GitHub Actions 日志

1. 访问: https://github.com/victor2025PH/liaotianai1201/actions
2. 点击失败的 `deploy-three-sites.yml` 运行
3. 查看每个站点的详细错误信息

---

## 🔧 常见问题

### 问题 1: 目录不存在

**症状**: "站点目录不存在"

**修复**:
```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
ls -la | grep -E "tgmini|hbwy|aizkw"
```

### 问题 2: npm install 失败

**症状**: "npm install 失败"

**修复**:
```bash
cd /home/ubuntu/telegram-ai-system/tgmini20251220
rm -rf node_modules package-lock.json
npm install
```

### 问题 3: 构建失败

**症状**: "npm run build 失败"

**修复**:
```bash
cd /home/ubuntu/telegram-ai-system/tgmini20251220
export NODE_OPTIONS="--max-old-space-size=3072"
npm run build
```

### 问题 4: PM2 进程不存在

**症状**: 网站无法访问，PM2 列表中没有进程

**修复**:
```bash
# 检查 PM2
pm2 list

# 手动启动
cd /home/ubuntu/telegram-ai-system/tgmini20251220
pm2 start serve --name tgmini-frontend -- dist --listen 3001 --single
pm2 save
```

### 问题 5: 端口被占用

**症状**: "端口未在监听"

**修复**:
```bash
# 检查端口
sudo lsof -i :3001
sudo lsof -i :3002
sudo lsof -i :3003

# 停止占用端口的进程
sudo kill -9 <PID>
```

---

## 📋 验证部署

```bash
# 检查 PM2 进程
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

## 🔄 重新触发 GitHub Actions

修复后，可以重新触发 GitHub Actions：

1. 访问: https://github.com/victor2025PH/liaotianai1201/actions
2. 点击 `deploy-three-sites.yml`
3. 点击 "Run workflow"
4. 选择 `main` 分支
5. 点击 "Run workflow"

或者推送一个空提交：

```bash
git commit --allow-empty -m "chore: 重新触发部署"
git push origin main
```

---

**最后更新**: 2025-12-21
