# 前端 500 错误修复指南

> **问题**: 页面无法加载，静态资源返回 500 错误

---

## 🔍 问题诊断

### 症状
- 浏览器显示 "Application error: a client-side exception has occurred"
- 控制台显示多个 500 错误：
  - CSS 文件加载失败
  - JavaScript 文件加载失败
  - Chunk 加载失败

### 可能原因
1. **前端构建文件损坏或缺失**
   - `.next` 目录不存在或损坏
   - 静态资源文件缺失

2. **前端服务未正常运行**
   - PM2 服务崩溃
   - 端口未监听

3. **构建过程失败**
   - 内存不足导致构建中断
   - 依赖安装问题

4. **Nginx 配置问题**
   - 静态文件路径配置错误
   - 权限问题

---

## ✅ 解决方案

### 方案 1: 使用自动修复脚本（推荐）

```bash
# 在服务器上执行
cd /home/ubuntu/telegram-ai-system
git pull origin main
bash scripts/server/fix_frontend_500.sh
```

### 方案 2: 手动修复步骤

#### 步骤 1: 检查服务状态

```bash
# 检查 PM2 状态
pm2 status

# 查看前端日志
pm2 logs frontend --lines 50
```

#### 步骤 2: 停止前端服务

```bash
pm2 stop frontend
```

#### 步骤 3: 清理并重新构建

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

# 清理旧的构建文件
rm -rf .next
rm -rf node_modules/.cache

# 重新构建（可能需要几分钟）
npm run build
```

#### 步骤 4: 重启服务

```bash
cd /home/ubuntu/telegram-ai-system
pm2 restart frontend
pm2 save

# 检查状态
pm2 status
```

#### 步骤 5: 验证修复

```bash
# 检查端口
ss -tln | grep ":3000"

# 测试响应
curl -I http://localhost:3000
```

---

## 🔧 详细排查步骤

### 1. 检查构建文件

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo

# 检查 .next 目录
ls -la .next/static 2>/dev/null || echo ".next 目录不存在"

# 检查文件大小
du -sh .next 2>/dev/null || echo "构建文件不存在"
```

### 2. 检查服务日志

```bash
# PM2 日志
pm2 logs frontend --lines 100

# 系统日志
sudo journalctl -u nginx -n 50
```

### 3. 检查磁盘空间

```bash
# 检查磁盘空间
df -h

# 如果空间不足，清理
pm2 flush
sudo journalctl --vacuum-time=7d
```

### 4. 检查内存

```bash
# 检查内存使用
free -h

# 如果内存不足，增加 Swap（如果还没有）
sudo swapon --show
```

---

## 🐛 常见问题

### 问题 1: 构建失败（内存不足）

**症状**: `npm run build` 失败，显示内存错误

**解决方案**:
```bash
# 增加 Swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 重新构建
cd saas-demo
npm run build
```

### 问题 2: 构建成功但服务仍返回 500

**症状**: 构建成功，但访问页面仍返回 500

**解决方案**:
```bash
# 1. 检查文件权限
ls -la saas-demo/.next

# 2. 修复权限（如果需要）
chmod -R 755 saas-demo/.next

# 3. 重启服务
pm2 restart frontend

# 4. 检查 Nginx 配置
sudo nginx -t
sudo systemctl reload nginx
```

### 问题 3: 静态资源路径错误

**症状**: 资源文件存在但路径不正确

**解决方案**:
```bash
# 检查 Next.js 配置
cat saas-demo/next.config.ts

# 检查 basePath 和 assetPrefix 配置
# 确保与 Nginx 配置匹配
```

---

## 📋 完整修复流程

```bash
# 1. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 2. 拉取最新代码
git pull origin main

# 3. 停止前端服务
pm2 stop frontend

# 4. 清理构建文件
cd saas-demo
rm -rf .next
rm -rf node_modules/.cache

# 5. 重新构建
npm run build

# 6. 检查构建结果
ls -la .next/static

# 7. 重启服务
cd ..
pm2 restart frontend
pm2 save

# 8. 验证
sleep 5
curl -I http://localhost:3000
pm2 status
```

---

## 🎯 预防措施

### 1. 定期检查构建文件

```bash
# 检查 .next 目录大小
du -sh saas-demo/.next

# 如果异常小（< 10MB），可能需要重新构建
```

### 2. 监控服务状态

```bash
# 设置 PM2 自动重启
pm2 startup
pm2 save

# 监控日志
pm2 logs frontend --lines 20
```

### 3. 设置构建验证

在部署脚本中添加构建验证：

```bash
# 构建后验证
if [ ! -d "saas-demo/.next" ]; then
    echo "构建失败：.next 目录不存在"
    exit 1
fi
```

---

## 📊 验证修复

修复后，检查以下内容：

- [ ] PM2 服务状态: ✅ online
- [ ] 端口监听: ✅ :3000 正在监听
- [ ] 构建文件: ✅ .next 目录存在
- [ ] 前端响应: ✅ HTTP 200/301/302
- [ ] 浏览器访问: ✅ 页面正常加载

---

**最后更新**: 2025-12-09

