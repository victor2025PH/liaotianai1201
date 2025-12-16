# 网络连接问题排查指南

## 问题现象

从服务器截图看到：
- ✅ 服务正常运行（端口 80, 443, 3000, 8000 都在监听）
- ❌ 外网连接失败（`ping 8.8.8.8` 100% 丢包）
- ❌ SSH 无法连接（端口 22 未监听）
- ❌ 网站无法访问

## 问题分析

**根本原因：服务器网络配置问题**

服务器无法访问外网，导致：
1. 无法从外部 SSH 连接（虽然服务在运行）
2. 无法访问网站（虽然 Nginx 在监听）
3. 可能是路由表、网关或 DNS 配置问题

## 立即修复步骤

### 1. 通过 VNC 控制台登录服务器

1. 登录 UCloud 控制台
2. 进入服务器详情页
3. 点击"VNC 登录"或"控制台登录"
4. 使用 root 或 ubuntu 用户登录

### 2. 运行网络修复脚本

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/fix_network_connectivity.sh
```

### 3. 手动检查网络配置

如果脚本无法自动修复，手动检查：

```bash
# 检查网络接口
ip addr show

# 检查路由表
ip route show

# 检查默认网关
ip route | grep default

# 检查 DNS 配置
cat /etc/resolv.conf

# 测试网关连接
ping -c 3 [网关IP]
```

### 4. 修复 SSH 服务

```bash
# 检查 SSH 服务状态
sudo systemctl status ssh

# 如果未运行，启动 SSH
sudo systemctl start ssh
sudo systemctl enable ssh

# 检查端口 22 是否监听
sudo ss -tlnp | grep :22
```

## 常见网络问题修复

### 问题 1: 缺少默认路由

**症状：** `ip route | grep default` 无输出

**修复：**
```bash
# 获取网络接口（通常是 eth0 或 ens3）
INTERFACE=$(ip route | grep -v default | awk '{print $3}' | head -1)
GATEWAY=$(ip route | grep -v default | awk '{print $1}' | head -1 | cut -d'/' -f1 | awk -F'.' '{print $1"."$2"."$3".1"}')

# 添加默认路由（需要根据实际情况调整）
sudo ip route add default via $GATEWAY dev $INTERFACE
```

### 问题 2: DNS 解析失败

**症状：** `nslookup google.com` 失败

**修复：**
```bash
# 备份原配置
sudo cp /etc/resolv.conf /etc/resolv.conf.bak

# 配置 Google DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf
```

### 问题 3: 网络接口未启动

**症状：** `ip addr show` 显示接口没有 IP

**修复：**
```bash
# 重启网络接口（替换 eth0 为实际接口名）
sudo ip link set eth0 down
sudo ip link set eth0 up

# 或使用 NetworkManager
sudo systemctl restart NetworkManager
```

### 问题 4: SSH 服务未运行

**症状：** 端口 22 未监听

**修复：**
```bash
# 启动 SSH 服务
sudo systemctl start ssh
sudo systemctl enable ssh

# 检查 SSH 配置
sudo cat /etc/ssh/sshd_config | grep -E "Port|PermitRootLogin"
```

## UCloud 控制台检查

### 1. 检查网络配置

1. 进入服务器详情页
2. 检查"网络"或"网卡"配置
3. 确认：
   - 公网 IP 是否正确
   - 内网 IP 是否正确
   - 子网配置是否正确

### 2. 检查路由表

1. 进入"VPC"或"网络"管理页面
2. 检查路由表配置
3. 确认有默认路由指向互联网网关

### 3. 检查安全组/防火墙

1. 确认防火墙规则包含：
   - 入站：TCP 22, 80, 443
   - 出站：允许所有流量（或至少允许 DNS 和 HTTP/HTTPS）

## 完整修复流程

```bash
# 1. 检查网络接口
ip addr show

# 2. 检查路由
ip route show

# 3. 修复 DNS（如果需要）
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf

# 4. 启动 SSH 服务
sudo systemctl start ssh
sudo systemctl enable ssh

# 5. 重启网络服务
sudo systemctl restart NetworkManager 2>/dev/null || true

# 6. 测试连接
ping -c 3 8.8.8.8
ping -c 3 google.com

# 7. 检查服务状态
sudo systemctl status nginx
sudo systemctl status liaotian-frontend
sudo systemctl status luckyred-api
sudo systemctl status ssh
```

## 如果问题仍然存在

1. **检查 UCloud 控制台**：
   - 服务器网络配置
   - VPC/子网配置
   - 路由表配置

2. **联系 UCloud 技术支持**：
   - 提供服务器 ID: `uhost-1kgb7nabqyq0`
   - 提供问题描述：无法访问外网，ping 8.8.8.8 失败
   - 提供网络配置截图

3. **临时解决方案**：
   - 如果只是 DNS 问题，可以手动配置 DNS
   - 如果只是 SSH 问题，可以通过 VNC 继续管理服务器

## 预防措施

1. **配置服务自动启动**：
   ```bash
   sudo systemctl enable ssh
   sudo systemctl enable nginx
   sudo systemctl enable liaotian-frontend
   sudo systemctl enable luckyred-api
   ```

2. **配置网络自动启动**：
   - 确保 NetworkManager 或 systemd-networkd 已启用
   - 检查网络配置文件（`/etc/netplan/` 或 `/etc/network/interfaces`）

3. **定期检查网络连接**：
   - 设置监控告警
   - 定期测试网络连接

