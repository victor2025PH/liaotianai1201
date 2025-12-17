# 手动修复 DNS 和软件源（无需 Git Pull）

## 问题
由于 DNS 解析失败，无法执行 `git pull` 来获取修复脚本。

## 解决方案：直接执行修复命令

以下命令可以直接复制粘贴到服务器终端执行，**无需 git pull**。

---

## 第一步：修复 DNS 配置

```bash
# 1. 配置 systemd-resolved（Ubuntu 22.04 默认 DNS 服务）
sudo bash -c 'cat > /etc/systemd/resolved.conf << EOF
[Resolve]
DNS=223.5.5.5 114.114.114.114 8.8.8.8
FallbackDNS=1.1.1.1 8.8.4.4
EOF'

# 2. 重启 DNS 服务
sudo systemctl restart systemd-resolved

# 3. 更新 /etc/resolv.conf（备用配置）
sudo bash -c 'cat > /etc/resolv.conf << EOF
nameserver 223.5.5.5
nameserver 114.114.114.114
nameserver 8.8.8.8
EOF'

# 4. 等待 2 秒让 DNS 服务生效
sleep 2

# 5. 测试 DNS 解析
host google.com
host github.com
```

如果看到域名被解析为 IP 地址，说明 DNS 修复成功。

---

## 第二步：更换软件源

```bash
# 备份原有配置
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup.$(date +%Y%m%d_%H%M%S)

# 更换为阿里云镜像（Ubuntu 22.04 jammy）
sudo bash -c 'cat > /etc/apt/sources.list << EOF
deb https://mirrors.aliyun.com/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ jammy-backports main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ jammy-security main restricted universe multiverse
EOF'

# 清理 apt 缓存
sudo apt clean
sudo apt autoclean

# 更新软件包列表
sudo apt update
```

---

## 第三步：验证修复

```bash
# 1. 测试 DNS 解析
echo "测试 DNS 解析:"
host google.com
host github.com
host mirrors.aliyun.com

# 2. 测试网络连接
echo "测试网络连接:"
ping -c 2 8.8.8.8

# 3. 测试软件源
echo "测试软件源:"
sudo apt update
```

---

## 第四步：拉取代码（DNS 修复后）

```bash
cd ~/telegram-ai-system
git pull origin main
```

---

## 如果第一步仍然失败（DNS 无法解析）

如果执行 `host google.com` 仍然失败，可能是网络连接问题，尝试以下方法：

### 方法 A：检查网络连接

```bash
# 测试能否 ping 通 IP 地址（不依赖 DNS）
ping -c 3 8.8.8.8
ping -c 3 114.114.114.114

# 如果 IP 能 ping 通但 DNS 不能解析，尝试临时使用 IP 地址配置软件源
```

### 方法 B：使用 IP 地址直接配置软件源（临时方案）

如果 DNS 完全无法工作，可以临时使用 IP 地址：

```bash
# 查找阿里云镜像的 IP 地址（从能访问的机器上）
# 或者使用清华大学镜像的 IP
# 注意：这种方法不推荐，因为 IP 地址可能会变化

# 使用清华大学镜像（如果阿里云不可用）
sudo bash -c 'cat > /etc/apt/sources.list << EOF
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-security main restricted universe multiverse
EOF'
```

### 方法 C：检查防火墙和网络配置

```bash
# 检查防火墙
sudo ufw status
sudo iptables -L

# 检查网络接口
ip addr show
ip route

# 检查系统日志
sudo journalctl -u systemd-resolved -n 50
```

---

## 完整的一键执行命令（复制粘贴整个代码块）

```bash
# ==========================================
# 一键修复 DNS 和软件源
# ==========================================

echo "开始修复 DNS 配置..."

# 1. 配置 DNS
sudo bash -c 'cat > /etc/systemd/resolved.conf << EOF
[Resolve]
DNS=223.5.5.5 114.114.114.114 8.8.8.8
FallbackDNS=1.1.1.1 8.8.4.4
EOF'

sudo systemctl restart systemd-resolved

sudo bash -c 'cat > /etc/resolv.conf << EOF
nameserver 223.5.5.5
nameserver 114.114.114.114
nameserver 8.8.8.8
EOF'

sleep 2

echo "测试 DNS 解析..."
host google.com || echo "DNS 解析仍然失败"

# 2. 更换软件源
echo "更换软件源..."
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup.$(date +%Y%m%d_%H%M%S)

sudo bash -c 'cat > /etc/apt/sources.list << EOF
deb https://mirrors.aliyun.com/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ jammy-backports main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ jammy-security main restricted universe multiverse
EOF'

# 3. 更新软件包列表
echo "更新软件包列表..."
sudo apt clean
sudo apt update

echo "✅ 修复完成！现在可以执行 git pull 了"
```

---

执行完成后，您应该能够：
1. ✅ 解析 DNS（`host google.com` 应该能返回 IP）
2. ✅ 执行 `apt update` 成功
3. ✅ 执行 `git pull origin main` 成功

然后再继续执行部署脚本。
