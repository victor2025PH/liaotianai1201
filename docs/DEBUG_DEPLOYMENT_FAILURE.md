# 调试部署失败问题

> **问题**: GitHub Actions 部署工作流失败，网站无法访问

---

## 🔍 问题分析

从 GitHub Actions 日志来看，`deploy-three-sites.yml` 工作流执行失败。可能的原因：

1. **目录不存在**: 服务器上可能没有这三个网站目录
2. **构建失败**: `npm run build` 可能失败
3. **PM2 启动失败**: `serve` 服务可能无法启动
4. **Nginx 配置错误**: Nginx 配置可能有问题
5. **端口冲突**: 端口可能被占用

---

## 🛠️ 诊断步骤

### 步骤 1: 检查服务器上的目录

SSH 到服务器并检查：

```bash
ssh ubuntu@<SERVER_HOST>

cd /home/ubuntu/telegram-ai-system

# 检查三个网站目录是否存在
ls -la | grep -E "tgmini|hbwy|aizkw"

# 检查每个目录的内容
ls -la tgmini20251220/
ls -la hbwy20251220/
ls -la aizkw20251219/
```

### 步骤 2: 运行诊断脚本

在服务器上运行诊断脚本：

```bash
cd /home/ubuntu/telegram-ai-system
bash scripts/server/check-deployment-status.sh
```

或者从本地上传并运行：

```bash
# 从本地上传脚本
scp scripts/server/check-deployment-status.sh ubuntu@<SERVER_HOST>:/home/ubuntu/telegram-ai-system/scripts/server/

# SSH 到服务器
ssh ubuntu@<SERVER_HOST>

# 运行脚本
cd /home/ubuntu/telegram-ai-system
bash scripts/server/check-deployment-status.sh
```

### 步骤 3: 检查 GitHub Actions 日志

1. 访问: https://github.com/victor2025PH/liaotianai1201/actions
2. 点击失败的 `deploy-three-sites.yml` 运行
3. 查看每个站点的部署日志
4. 找到具体的错误信息

---

## 🔧 常见问题修复

### 问题 1: 目录不存在

**症状**: 工作流报错 "站点目录不存在"

**修复**:

```bash
# SSH 到服务器
ssh ubuntu@<SERVER_HOST>

cd /home/ubuntu/telegram-ai-system

# 确保目录存在
mkdir -p tgmini20251220 hbwy20251220 aizkw20251219

# 拉取最新代码
git pull origin main
```

### 问题 2: 构建失败

**症状**: `npm run build` 失败

**修复**:

```bash
# 进入网站目录
cd /home/ubuntu/telegram-ai-system/tgmini20251220

# 清理并重新安装依赖
rm -rf node_modules package-lock.json
npm install

# 重新构建
export NODE_OPTIONS="--max-old-space-size=3072"
npm run build
```

### 问题 3: PM2 启动失败

**症状**: PM2 进程不存在或已停止

**修复**:

```bash
# 检查 PM2 状态
pm2 list

# 手动启动服务
cd /home/ubuntu/telegram-ai-system/tgmini20251220
pm2 start serve --name tgmini-frontend -- dist --listen 3001 --single

# 保存 PM2 配置
pm2 save
```

### 问题 4: Nginx 配置错误

**症状**: Nginx 配置测试失败

**修复**:

```bash
# 测试 Nginx 配置
sudo nginx -t

# 查看错误详情
sudo nginx -T | grep -A 10 -B 10 error

# 修复配置后重载
sudo systemctl reload nginx
```

### 问题 5: 端口被占用

**症状**: 端口无法监听

**修复**:

```bash
# 检查端口占用
sudo lsof -i :3001
sudo lsof -i :3002
sudo lsof -i :3003

# 停止占用端口的进程
sudo kill -9 <PID>
```

---

## 🚀 手动部署（临时方案）

如果 GitHub Actions 持续失败，可以手动部署：

```bash
# SSH 到服务器
ssh ubuntu@<SERVER_HOST>

cd /home/ubuntu/telegram-ai-system

# 拉取最新代码
git pull origin main

# 部署每个网站
cd tgmini20251220
npm install
export NODE_OPTIONS="--max-old-space-size=3072"
npm run build
pm2 delete tgmini-frontend 2>/dev/null || true
pm2 start serve --name tgmini-frontend -- dist --listen 3001 --single
pm2 save

# 重复上述步骤 for hbwy20251220 和 aizkw20251219
```

---

## 📋 检查清单

- [ ] 服务器上三个网站目录存在
- [ ] 每个目录有 `package.json`
- [ ] `npm install` 成功
- [ ] `npm run build` 成功生成 `dist` 目录
- [ ] PM2 进程正在运行
- [ ] 端口正在监听
- [ ] Nginx 配置正确且已启用
- [ ] Nginx 服务正在运行

---

## 📞 获取帮助

如果问题仍然存在，请提供：

1. GitHub Actions 日志（完整的错误信息）
2. 诊断脚本的输出
3. 服务器上的目录结构
4. PM2 进程列表
5. Nginx 配置内容

---

**最后更新**: 2025-12-21
