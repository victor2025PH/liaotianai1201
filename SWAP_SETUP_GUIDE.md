# Swap File Setup Guide - Prevent OOM (Out of Memory)

## 📋 问题描述

服务器在运行 `npm run build` 时因为内存不足（OOM）而冻结。需要创建交换文件来增加可用内存。

## 🚀 快速设置

### 方式 1: 使用自动化脚本（推荐）

```bash
# 1. SSH 到服务器
ssh ubuntu@165.154.233.55

# 2. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 3. 拉取最新代码
git pull origin main

# 4. 执行交换文件创建脚本
bash scripts/server/create-swap.sh
```

### 方式 2: 手动执行

```bash
# 1. SSH 到服务器
ssh ubuntu@165.154.233.55

# 2. 创建 4GB 交换文件
sudo fallocate -l 4G /swapfile

# 3. 设置正确的权限
sudo chmod 600 /swapfile

# 4. 格式化为交换文件
sudo mkswap /swapfile

# 5. 启用交换文件
sudo swapon /swapfile

# 6. 使交换文件永久生效（重启后仍然有效）
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 7. 验证交换文件
free -h
```

## 📊 验证交换文件

执行 `free -h` 后，应该看到类似这样的输出：

```
              total        used        free      shared  buff/cache   available
Mem:           2.0Gi       1.2Gi       200Mi        50Mi       600Mi       600Mi
Swap:          4.0Gi         0Bi       4.0Gi
```

注意 `Swap` 行应该显示 `4.0Gi` 的总量。

## 🔄 重试部署

交换文件创建完成后，可以重试部署：

```bash
# 1. 进入前端目录
cd /home/ubuntu/telegram-ai-system/saas-demo

# 2. 安装依赖（如果需要）
npm install

# 3. 构建前端（现在有足够的交换空间）
npm run build

# 4. 启动 PM2 服务
cd /home/ubuntu/telegram-ai-system
pm2 start ecosystem.config.js

# 5. 验证状态
pm2 status
```

## 🔧 故障排除

### 检查交换文件状态

```bash
# 查看交换文件使用情况
free -h

# 查看交换文件详情
swapon --show

# 查看交换文件大小
ls -lh /swapfile
```

### 如果交换文件已存在

如果 `/swapfile` 已存在，脚本会提示是否删除并重新创建。或者手动删除：

```bash
# 禁用交换文件
sudo swapoff /swapfile

# 删除交换文件
sudo rm /swapfile

# 从 /etc/fstab 中删除（如果存在）
sudo sed -i '/swapfile/d' /etc/fstab
```

### 检查磁盘空间

确保有足够的磁盘空间（至少 4GB）：

```bash
df -h
```

### 调整交换文件大小

如果需要更大的交换文件（例如 8GB）：

```bash
# 禁用当前交换文件
sudo swapoff /swapfile

# 删除旧文件
sudo rm /swapfile

# 创建新的 8GB 交换文件
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 📝 完整命令序列

```bash
# 1. SSH 到服务器
ssh ubuntu@165.154.233.55

# 2. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 3. 拉取最新代码
git pull origin main

# 4. 创建交换文件
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 5. 验证交换文件
free -h

# 6. 重试前端构建
cd saas-demo
npm run build

# 7. 启动 PM2 服务
cd ..
pm2 start ecosystem.config.js

# 8. 验证服务状态
pm2 status
```

## ⚠️ 注意事项

1. **交换文件会占用磁盘空间**：确保有足够的磁盘空间（至少 4GB）
2. **交换文件性能较慢**：交换文件使用磁盘空间，比 RAM 慢得多，但可以防止 OOM
3. **永久生效**：通过添加到 `/etc/fstab`，交换文件会在重启后自动启用
4. **建议大小**：对于 2GB RAM 的服务器，4GB 交换文件通常足够

## 📌 最佳实践

1. **监控内存使用**：定期检查内存使用情况
   ```bash
   free -h
   ```

2. **监控交换文件使用**：如果交换文件经常被使用，考虑升级服务器 RAM
   ```bash
   swapon --show
   ```

3. **优化构建过程**：考虑使用构建缓存或增量构建来减少内存使用

---

**最后更新**: 2025-12-07

