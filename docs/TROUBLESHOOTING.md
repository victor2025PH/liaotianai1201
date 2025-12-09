# 故障排查指南

> **常见问题**: 脚本执行时出现 "Killed" 错误

---

## 🐛 问题: 脚本被系统杀死

### 症状
```bash
scripts/server/verify_deployment.sh: line 36: 963345 Killed
```

### 原因
- **内存不足 (OOM)**: 系统内存耗尽，内核杀死进程
- **资源限制**: 进程使用的资源超过系统限制
- **脚本过于复杂**: 一次性执行太多操作

---

## ✅ 解决方案

### 方案 1: 使用轻量级验证脚本（推荐）

```bash
# 使用轻量级版本，避免内存问题
bash scripts/server/verify_deployment_light.sh
```

### 方案 2: 分步骤手动检查

```bash
# 1. 检查 PM2 服务
pm2 status

# 2. 检查端口
ss -tln | grep -E ":8000|:3000"

# 3. 检查健康状态
curl http://localhost:8000/health
curl -I http://localhost:3000

# 4. 检查环境变量（只检查关键项）
cd admin-backend
grep JWT_SECRET .env
grep ADMIN_DEFAULT_PASSWORD .env
```

### 方案 3: 增加 Swap 内存

如果内存不足，可以增加 Swap：

```bash
# 检查当前 Swap
free -h

# 如果 Swap 不足，创建 2GB Swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 🔍 诊断步骤

### 1. 检查系统资源

```bash
# 检查内存使用
free -h

# 检查磁盘空间
df -h

# 检查系统负载
uptime
```

### 2. 检查进程状态

```bash
# 查看 PM2 进程
pm2 list

# 查看系统进程
ps aux | head -n 20

# 查看内存使用最多的进程
ps aux --sort=-%mem | head -n 10
```

### 3. 检查系统日志

```bash
# 查看系统日志（可能显示 OOM 信息）
sudo dmesg | tail -n 50

# 查看系统日志
sudo journalctl -n 50
```

---

## 🚀 快速验证命令

### 最小化验证（最快）

```bash
# 1. PM2 状态
pm2 list

# 2. 端口检查
ss -tln | grep -E ":8000|:3000"

# 3. 健康检查
curl -s http://localhost:8000/health | head -c 50
```

### 完整验证（分步执行）

```bash
# 步骤 1: 服务状态
echo "=== 服务状态 ==="
pm2 status

# 步骤 2: 端口监听
echo "=== 端口监听 ==="
ss -tln | grep -E ":8000|:3000"

# 步骤 3: 健康检查
echo "=== 健康检查 ==="
curl -s http://localhost:8000/health

# 步骤 4: 环境变量
echo "=== 环境变量 ==="
cd admin-backend
grep -E "JWT_SECRET|ADMIN_DEFAULT_PASSWORD" .env | head -c 100
```

---

## 📋 常见问题

### 问题 1: 内存不足

**症状**: 进程被 "Killed"，`free -h` 显示内存几乎用完

**解决方案**:
```bash
# 1. 增加 Swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. 重启服务（释放内存）
pm2 restart all

# 3. 使用轻量级脚本
bash scripts/server/verify_deployment_light.sh
```

### 问题 2: 磁盘空间不足

**症状**: `df -h` 显示磁盘使用率 > 90%

**解决方案**:
```bash
# 清理日志
pm2 flush

# 清理旧的构建文件
cd saas-demo
rm -rf .next
npm run build

# 清理系统日志
sudo journalctl --vacuum-time=7d
```

### 问题 3: 服务未运行

**症状**: `pm2 status` 显示服务 offline 或不存在

**解决方案**:
```bash
# 检查 ecosystem.config.js
cat ecosystem.config.js

# 启动服务
pm2 start ecosystem.config.js
pm2 save
```

---

## 🎯 推荐的验证流程

### 第一次验证（快速）

```bash
# 1. 使用轻量级脚本
bash scripts/server/verify_deployment_light.sh

# 2. 如果成功，继续功能测试
# 如果失败，查看错误信息并修复
```

### 完整验证（分步）

```bash
# 步骤 1: 服务状态
pm2 status

# 步骤 2: 健康检查
curl http://localhost:8000/health

# 步骤 3: 安全检查
bash scripts/server/check_security.sh

# 步骤 4: 功能测试
# 访问网站并测试功能
```

---

## 📝 验证结果记录

### 快速检查结果

- [ ] PM2 服务: ✅ 正常 / ❌ 异常
- [ ] 端口监听: ✅ 正常 / ❌ 异常
- [ ] 健康检查: ✅ 正常 / ❌ 异常
- [ ] 环境变量: ✅ 已配置 / ❌ 未配置

### 如果发现问题

1. **记录错误信息**
2. **检查系统资源** (`free -h`, `df -h`)
3. **查看日志** (`pm2 logs`, `sudo journalctl`)
4. **尝试修复**（根据错误信息）
5. **重新验证**

---

**最后更新**: 2025-12-09

