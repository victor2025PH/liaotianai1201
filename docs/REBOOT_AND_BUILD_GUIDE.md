# 重启服务器后构建指南

> **方案**: 重启服务器释放内存，然后重新构建前端

---

## 🚀 完整流程

### 步骤 1: 重启服务器

```bash
# 在服务器上执行
sudo reboot
```

**注意**: 重启后需要重新 SSH 连接。

---

### 步骤 2: 重新连接并检查状态

重启后，重新 SSH 连接：

```bash
# 重新 SSH 连接
ssh ubuntu@165.154.233.55
```

然后检查系统状态：

```bash
# 检查系统运行时间（应该是刚重启）
uptime

# 检查内存（应该很充足）
free -h

# 检查 PM2 服务（应该自动启动，因为之前设置了 pm2 startup）
pm2 status
```

---

### 步骤 3: 使用自动构建脚本（推荐）

```bash
# 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 拉取最新代码（包含构建脚本）
git pull origin main

# 运行构建脚本
bash scripts/server/reboot_and_build.sh
```

这个脚本会：
- 自动停止服务释放内存
- 清理旧的构建文件
- 根据可用内存自动设置内存限制
- 执行构建
- 重启所有服务
- 验证服务状态

---

### 步骤 4: 手动构建（如果脚本有问题）

如果自动脚本有问题，可以手动执行：

```bash
# 1. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 2. 停止所有服务（释放内存）
pm2 stop all

# 3. 清理构建文件
cd saas-demo
rm -rf .next
rm -rf node_modules/.cache

# 4. 检查可用内存
free -h

# 5. 根据可用内存设置限制并构建
# 如果可用内存 > 1.5GB，使用 1.5GB
export NODE_OPTIONS="--max-old-space-size=1536"
npm run build

# 或者如果内存较少，使用 1GB
# export NODE_OPTIONS="--max-old-space-size=1024"
# npm run build

# 6. 验证构建
ls -la .next/static

# 7. 重启服务
cd ..
pm2 restart all
pm2 save

# 8. 检查状态
pm2 status
sleep 5
curl -I http://localhost:3000
```

---

## 📋 重启后的检查清单

### 系统检查

- [ ] 系统已重启（`uptime` 显示运行时间很短）
- [ ] 内存充足（`free -h` 显示可用内存 > 1GB）
- [ ] Swap 正常（`swapon --show` 显示 Swap 已启用）

### 服务检查

- [ ] PM2 服务自动启动（`pm2 status` 显示服务）
- [ ] 如果没有自动启动，手动启动：
  ```bash
  cd /home/ubuntu/telegram-ai-system
  pm2 start ecosystem.config.js
  pm2 save
  ```

### 构建检查

- [ ] 构建成功（`.next` 目录存在）
- [ ] 构建文件完整（`.next/static` 目录存在）
- [ ] 服务正常响应（`curl -I http://localhost:3000` 返回 200）

---

## 🔧 如果 PM2 服务未自动启动

重启后，如果 PM2 服务没有自动启动，需要重新设置：

```bash
# 1. 启动 PM2 服务
cd /home/ubuntu/telegram-ai-system
pm2 start ecosystem.config.js

# 2. 设置开机自启
pm2 startup
# 按照输出的命令执行（通常是 sudo 命令）

# 3. 保存当前进程列表
pm2 save
```

---

## 🎯 推荐执行流程

### 完整流程（一键执行）

```bash
# 1. 重启服务器
sudo reboot

# 2. 等待 1-2 分钟，然后重新 SSH 连接
ssh ubuntu@165.154.233.55

# 3. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 4. 拉取最新代码
git pull origin main

# 5. 运行构建脚本
bash scripts/server/reboot_and_build.sh
```

---

## 💡 为什么重启后构建更容易成功？

1. **内存完全释放**: 重启后所有进程都被清理，内存完全释放
2. **干净的环境**: 没有残留的进程占用内存
3. **Swap 重置**: Swap 使用量归零，有更多可用空间
4. **系统优化**: 重启后系统状态最佳

---

## 📊 预期结果

### 重启后

- **内存使用**: < 500MB（系统基础进程）
- **可用内存**: > 1.4GB
- **Swap 使用**: 0MB（未使用）

### 构建时

- **内存使用**: 1-1.5GB（构建进程）
- **可用内存**: 仍然充足
- **Swap 使用**: 可能使用少量 Swap

### 构建后

- **服务状态**: 所有服务正常运行
- **前端响应**: HTTP 200/301/302
- **页面加载**: 正常

---

## 🐛 如果重启后构建仍然失败

### 检查 1: 内存是否真的充足

```bash
free -h
# 如果可用内存 < 1GB，可能需要升级服务器
```

### 检查 2: 是否有其他进程占用内存

```bash
ps aux --sort=-%mem | head -n 10
```

### 检查 3: 使用更小的内存限制

```bash
export NODE_OPTIONS="--max-old-space-size=768"
npm run build
```

### 检查 4: 考虑本地构建

如果服务器内存确实不足，使用本地构建后上传（见之前的指南）。

---

## ✅ 验证修复

构建完成后，验证：

```bash
# 1. 检查服务
pm2 status

# 2. 测试后端
curl http://localhost:8000/health

# 3. 测试前端
curl -I http://localhost:3000

# 4. 浏览器访问
# 访问 https://aikz.usdt2026.cc/group-ai/chat-features
# 应该能正常加载，不再有 500 错误
```

---

**最后更新**: 2025-12-09

