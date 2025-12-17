# 修复 SSH 连接被重置问题

## 🚨 错误信息

```
ssh: handshake failed: read tcp ...->...:22: read: connection reset by peer
```

这通常表示：
1. 服务器主动关闭了连接
2. 可能是服务器内存不足导致 SSH 守护进程不稳定
3. 可能是网络不稳定
4. 可能是 SSH 连接超时

---

## 立即检查

### 1. 检查服务器内存和 Swap

```bash
# SSH 登录服务器
ssh ubuntu@your-server-ip

# 检查内存
free -h

# 检查 Swap
swapon --show

# 如果 Swap 未启用
sudo swapon /swapfile
```

### 2. 检查 SSH 服务状态

```bash
# 在服务器上执行
sudo systemctl status sshd

# 检查 SSH 日志
sudo tail -50 /var/log/auth.log | grep ssh

# 重启 SSH 服务（如果必要）
sudo systemctl restart sshd
```

### 3. 检查系统负载

```bash
# 检查系统负载
uptime

# 检查进程
top

# 检查是否有进程占用大量内存
ps aux --sort=-%mem | head -10
```

---

## 临时解决方案

### 方案 1：启用 Swap 并等待系统稳定

```bash
# 1. 启用 Swap
sudo swapon /swapfile

# 2. 等待 30 秒让系统稳定
sleep 30

# 3. 然后重新尝试部署
```

### 方案 2：重启服务器（如果可行）

如果服务器完全无响应：

1. 通过云服务商控制台重启服务器
2. 等待服务器完全启动
3. 确保 Swap 已自动启用
4. 然后重新尝试 GitHub Actions 部署

### 方案 3：减少部署时的内存使用

在部署脚本中：
- 限制 Node.js 内存使用（已更新）
- 分批执行命令
- 避免同时运行多个内存密集型操作

---

## 长期解决方案

### 1. 确保 Swap 持久化

```bash
# 检查 Swap 是否在 /etc/fstab 中
grep swapfile /etc/fstab

# 如果不在，添加
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 2. 优化系统配置

```bash
# 增加 SSH 连接超时
sudo nano /etc/ssh/sshd_config

# 添加或修改：
# ClientAliveInterval 30
# ClientAliveCountMax 3
# TCPKeepAlive yes

# 重启 SSH
sudo systemctl restart sshd
```

### 3. 监控内存使用

定期检查内存使用情况，如果经常内存不足，考虑：
- 升级服务器配置（增加内存）
- 优化应用配置
- 减少并发连接

---

## GitHub Actions 已优化的配置

我已经更新了 GitHub Actions 配置：
- ✅ 增加了 SSH 重试机制（3 次）
- ✅ 增加了连接超时设置
- ✅ 添加了 ServerAlive 保活机制
- ✅ 限制了 Node.js 构建内存使用（512MB）

---

## 验证修复

```bash
# 1. 从本地测试 SSH 连接
ssh -v ubuntu@your-server-ip "echo 'SSH 连接测试'"

# 2. 检查连接稳定性
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 ubuntu@your-server-ip "free -h"

# 3. 然后在 GitHub Actions 重新运行部署
```

---

如果问题持续，可能需要：
1. 升级服务器内存
2. 优化应用内存使用
3. 使用更轻量级的构建方式
