# 手动修复前端 500 错误

> **问题**: 自动修复脚本因内存不足被杀死

---

## 🚀 分步骤手动修复（推荐）

### 步骤 1: 停止前端服务

```bash
pm2 stop frontend
```

### 步骤 2: 清理构建文件

```bash
cd /home/ubuntu/telegram-ai-system/saas-demo
rm -rf .next
rm -rf node_modules/.cache
```

### 步骤 3: 检查内存和 Swap

```bash
# 检查内存
free -h

# 检查 Swap
swapon --show

# 如果 Swap 不足 2GB，增加 Swap
if [ $(swapon --show | wc -l) -eq 0 ] || [ $(swapon --show | grep -c swapfile) -eq 0 ]; then
    echo "增加 Swap..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
fi
```

### 步骤 4: 使用内存限制构建

```bash
# 设置 Node.js 内存限制（避免 OOM）
export NODE_OPTIONS="--max-old-space-size=1536"

# 构建（可能需要 5-10 分钟）
npm run build
```

### 步骤 5: 验证构建

```bash
# 检查构建文件
ls -la .next/static

# 如果存在，构建成功
```

### 步骤 6: 重启服务

```bash
cd /home/ubuntu/telegram-ai-system
pm2 restart frontend
pm2 save
```

### 步骤 7: 验证修复

```bash
# 等待几秒
sleep 5

# 检查服务
pm2 status

# 测试响应
curl -I http://localhost:3000
```

---

## 🔧 如果构建仍然失败

### 方案 1: 增加更多 Swap

```bash
# 检查当前 Swap
swapon --show

# 如果小于 4GB，增加到 4GB
sudo swapoff /swapfile 2>/dev/null || true
sudo rm /swapfile 2>/dev/null || true
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 验证
free -h
```

### 方案 2: 使用更小的内存限制

```bash
# 如果 1.5GB 还是太大，尝试 1GB
export NODE_OPTIONS="--max-old-space-size=1024"
npm run build
```

### 方案 3: 分阶段构建

```bash
# 只构建生产版本（跳过开发依赖）
NODE_ENV=production npm run build
```

### 方案 4: 清理并重新安装依赖

```bash
# 清理
rm -rf node_modules
rm -rf .next
rm package-lock.json

# 重新安装
npm install

# 构建
export NODE_OPTIONS="--max-old-space-size=1536"
npm run build
```

---

## 📋 完整手动修复流程

```bash
# ===== 步骤 1: 准备 =====
cd /home/ubuntu/telegram-ai-system
git pull origin main

# ===== 步骤 2: 停止服务 =====
pm2 stop frontend

# ===== 步骤 3: 清理 =====
cd saas-demo
rm -rf .next
rm -rf node_modules/.cache

# ===== 步骤 4: 检查资源 =====
free -h
swapon --show

# ===== 步骤 5: 构建（关键步骤）=====
export NODE_OPTIONS="--max-old-space-size=1536"
npm run build

# ===== 步骤 6: 验证构建 =====
if [ -d ".next" ] && [ -d ".next/static" ]; then
    echo "✓ 构建成功"
else
    echo "✗ 构建失败，请检查错误信息"
    exit 1
fi

# ===== 步骤 7: 重启服务 =====
cd ..
pm2 restart frontend
pm2 save

# ===== 步骤 8: 验证 =====
sleep 5
pm2 status
curl -I http://localhost:3000
```

---

## 🐛 常见错误处理

### 错误 1: "Killed" 在构建过程中

**原因**: 内存不足

**解决方案**:
```bash
# 1. 增加 Swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. 使用内存限制
export NODE_OPTIONS="--max-old-space-size=1536"
npm run build
```

### 错误 2: "ENOSPC: no space left on device"

**原因**: 磁盘空间不足（虽然显示有空间，可能是 inode 用尽）

**解决方案**:
```bash
# 检查 inode
df -i

# 清理临时文件
npm cache clean --force
rm -rf /tmp/*
```

### 错误 3: 构建成功但服务仍返回 500

**原因**: 服务未正确重启或文件权限问题

**解决方案**:
```bash
# 1. 完全重启
pm2 delete frontend
cd /home/ubuntu/telegram-ai-system
pm2 start ecosystem.config.js --only frontend
pm2 save

# 2. 检查权限
ls -la saas-demo/.next
chmod -R 755 saas-demo/.next 2>/dev/null || true
```

---

## 🎯 快速修复命令（一键执行）

```bash
cd /home/ubuntu/telegram-ai-system && \
pm2 stop frontend && \
cd saas-demo && \
rm -rf .next node_modules/.cache && \
export NODE_OPTIONS="--max-old-space-size=1536" && \
npm run build && \
cd .. && \
pm2 restart frontend && \
pm2 save && \
echo "✓ 修复完成"
```

---

## 📊 验证清单

修复后检查：

- [ ] 构建成功: ✅ `.next` 目录存在
- [ ] 服务运行: ✅ PM2 显示 online
- [ ] 端口监听: ✅ :3000 正在监听
- [ ] 前端响应: ✅ HTTP 200/301/302
- [ ] 浏览器访问: ✅ 页面正常加载

---

**最后更新**: 2025-12-09

