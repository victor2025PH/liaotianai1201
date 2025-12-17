# 修复 DNS 解析和软件源问题

## 问题症状

执行 `apt update` 或 `apt install` 时出现以下错误：
```
E: Failed to fetch http://mirrors.ucloud.cn/ubuntu/...
Temporary failure resolving 'mirrors.ucloud.cn'
```

这表明服务器无法解析 DNS，导致无法下载软件包。

---

## 快速修复

### 方法一：使用自动修复脚本（推荐）

```bash
cd ~/telegram-ai-system
chmod +x scripts/server/fix-dns-and-sources.sh
sudo bash scripts/server/fix-dns-and-sources.sh
```

### 方法二：手动修复

#### 步骤 1：修复 DNS 配置

```bash
# 1. 配置 systemd-resolved（Ubuntu 22.04 默认）
sudo nano /etc/systemd/resolved.conf
```

**修改为以下内容：**
```ini
[Resolve]
DNS=223.5.5.5 114.114.114.114 8.8.8.8
FallbackDNS=1.1.1.1 8.8.4.4
```

**保存后重启服务：**
```bash
sudo systemctl restart systemd-resolved
```

**同时更新 /etc/resolv.conf：**
```bash
sudo bash -c 'cat > /etc/resolv.conf << EOF
nameserver 223.5.5.5
nameserver 114.114.114.114
nameserver 8.8.8.8
EOF'
```

#### 步骤 2：更换软件源

```bash
# 备份原配置
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup

# 更换为阿里云镜像（Ubuntu 22.04）
sudo bash -c 'cat > /etc/apt/sources.list << EOF
deb https://mirrors.aliyun.com/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ jammy-backports main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ jammy-security main restricted universe multiverse
EOF'
```

**或者使用清华大学镜像：**
```bash
sudo bash -c 'cat > /etc/apt/sources.list << EOF
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-security main restricted universe multiverse
EOF'
```

#### 步骤 3：测试修复

```bash
# 清理缓存
sudo apt clean

# 更新软件包列表
sudo apt update

# 测试 DNS 解析
host google.com
host mirrors.aliyun.com
```

---

## 验证修复

执行以下命令验证：

```bash
# 1. 测试 DNS 解析
host google.com
host baidu.com
nslookup mirrors.aliyun.com

# 2. 测试网络连接
ping -c 3 8.8.8.8
ping -c 3 114.114.114.114

# 3. 测试软件源
sudo apt update
sudo apt install -y curl
```

---

## 如果仍然失败

### 检查网络连接

```bash
# 检查是否能 ping 通外网 IP
ping -c 3 8.8.8.8

# 检查路由
ip route

# 检查网络接口
ip addr show
```

### 检查防火墙

```bash
# 检查 iptables
sudo iptables -L

# 检查 ufw
sudo ufw status
```

### 使用其他 DNS

如果上述 DNS 服务器都不可用，可以尝试：

```bash
# 腾讯 DNS
nameserver 119.29.29.29

# 百度 DNS
nameserver 180.76.76.76

# Cloudflare DNS
nameserver 1.1.1.1
```

---

## 修复后继续部署

DNS 和软件源修复后，可以继续执行部署脚本：

```bash
cd ~/telegram-ai-system
sudo bash scripts/server/initial-deploy-ubuntu22-pm2.sh
```

或手动继续安装：

```bash
# 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 PM2
sudo npm install -g pm2@latest

# 继续其他部署步骤...
```
