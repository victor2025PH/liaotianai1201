# 完整服务器初始化指南

## 📋 概述

本指南将帮助您在全新的 Ubuntu 22.04 服务器上完成所有必要的配置，为 Telegram AI 系统项目做好准备。

## 🚀 快速开始

### 方法 1：直接从 GitHub 下载并运行（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/victor2025PH/liaotianai1201/main/scripts/server/complete-initial-setup.sh | sudo bash
```

### 方法 2：手动下载后运行

```bash
# 1. 下载脚本
wget https://raw.githubusercontent.com/victor2025PH/liaotianai1201/main/scripts/server/complete-initial-setup.sh

# 2. 添加执行权限
chmod +x complete-initial-setup.sh

# 3. 运行脚本（需要 root 权限）
sudo bash complete-initial-setup.sh
```

### 方法 3：从本地项目运行

如果您已经在服务器上有项目代码：

```bash
cd telegram-ai-system
chmod +x scripts/server/complete-initial-setup.sh
sudo bash scripts/server/complete-initial-setup.sh
```

---

## 📦 脚本功能清单

脚本将自动完成以下配置：

### ✅ 1. 基础环境安装
- [x] 更新 apt 源 (`apt update && apt upgrade`)
- [x] 安装常用工具：`curl`, `wget`, `git`, `unzip`, `fail2ban`
- [x] 安装 **Node.js 20.x LTS** 和 `npm`
- [x] 安装 **Python 3.10+** 和 `pip`
- [x] 安装 **Nginx**
- [x] 全局安装 **PM2**

### ✅ 2. 用户与权限配置
- [x] 创建 `deployer` 用户
- [x] 加入 `sudo` 组
- [x] 配置无密码 sudo（方便部署脚本）
- [x] 创建 SSH 目录 (`/home/deployer/.ssh`)
- [x] 生成 SSH Key 对（如果不存在）
- [x] 设置正确的目录权限（700 for .ssh, 600 for authorized_keys）

### ✅ 3. 项目目录结构
- [x] 创建项目根目录 `/home/deployer/telegram-ai-system`
- [x] 设置正确的所有权给 `deployer` 用户
- [x] 创建日志目录 `/home/deployer/telegram-ai-system/logs`

### ✅ 4. 防火墙与连接优化
- [x] 配置 UFW 防火墙
  - [x] 允许 OpenSSH (Port 22)
  - [x] 允许 Nginx Full (Port 80, 443)
  - [x] 启用防火墙
- [x] 优化 SSH 配置 (`/etc/ssh/sshd_config`)
  - [x] `ClientAliveInterval 60`（防止空闲断开）
  - [x] `ClientAliveCountMax 3`
  - [x] `PasswordAuthentication yes`（暂时开启，后续可关闭）
  - [x] `PubkeyAuthentication yes`

### ✅ 5. Swap 文件（防止 OOM）
- [x] 创建 8GB Swap 文件
- [x] 启用 Swap
- [x] 添加到 `/etc/fstab` 实现开机自动挂载

### ✅ 6. Nginx 配置
- [x] 创建基础反向代理配置框架
- [x] 配置前端代理 (Port 3000)
- [x] 配置后端 API 代理 (Port 8000)
- [x] 配置 WebSocket 支持 (`/api/v1/notifications/ws`)

---

## 📝 执行步骤详解

### 步骤 1：连接到服务器

使用您的 SSH 客户端连接到 Ubuntu 22.04 服务器：

```bash
ssh root@your-server-ip
# 或者
ssh ubuntu@your-server-ip
```

### 步骤 2：运行初始化脚本

选择上述方法之一运行脚本。脚本会自动执行所有配置，预计需要 **5-10 分钟**。

**重要提示：**
- ✅ 脚本必须以 `root` 或 `sudo` 权限运行
- ✅ 确保服务器有稳定的网络连接
- ✅ 脚本会自动备份 SSH 配置文件

### 步骤 3：查看执行结果

脚本执行完成后，您会看到：

```
🎉 服务器初始化完成！

已完成以下配置：
  ✓ 基础环境：Node.js v20.x, Python 3.10.x, Nginx, PM2
  ✓ 用户配置：deployer (sudo 权限，SSH Key 已生成)
  ✓ 项目目录：/home/deployer/telegram-ai-system
  ✓ 防火墙：UFW 已启用（允许 SSH, HTTP, HTTPS）
  ✓ SSH 优化：ClientAliveInterval 60（防止断开）
  ✓ Swap 文件：8GB
  ✓ Nginx 配置：已创建反向代理框架
```

---

## 🔐 下一步操作

### 1. 切换到 deployer 用户

```bash
sudo su - deployer
```

### 2. 查看 SSH 公钥（用于 GitHub Actions）

```bash
cat ~/.ssh/id_rsa.pub
```

**重要：** 将输出内容复制，用于配置 GitHub Actions Secrets（`SERVER_SSH_KEY`）。

### 3. 克隆项目代码

```bash
cd /home/deployer/telegram-ai-system
git clone https://github.com/victor2025PH/liaotianai1201.git .
```

### 4. 部署项目

参考项目文档进行部署：

```bash
# 安装后端依赖
cd admin-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 安装前端依赖并构建
cd ../saas-demo
npm install
npm run build

# 使用 PM2 启动服务（参考 ecosystem.config.js）
cd /home/deployer/telegram-ai-system
pm2 start ecosystem.config.js
pm2 save
```

### 5. 重启 Nginx（应用配置）

```bash
sudo systemctl restart nginx
sudo systemctl status nginx
```

---

## 🔒 安全加固（可选但推荐）

### 关闭密码登录，仅使用 SSH Key

在项目部署完成后，建议关闭密码登录以提高安全性：

```bash
# 编辑 SSH 配置
sudo nano /etc/ssh/sshd_config

# 找到并修改：
PasswordAuthentication no

# 保存后重启 SSH 服务
sudo systemctl restart sshd
```

**⚠️ 警告：** 在执行此操作前，请确保：
1. ✅ SSH Key 已经添加到 `~/.ssh/authorized_keys`
2. ✅ 您可以使用 SSH Key 正常登录
3. ✅ 已经测试过 SSH Key 连接

---

## 🌐 配置域名（可选）

如果您有域名，需要修改 Nginx 配置：

```bash
sudo nano /etc/nginx/sites-available/telegram-ai-system
```

找到 `server_name _;` 并替换为您的域名：

```nginx
server_name example.com www.example.com;
```

然后重新加载 Nginx：

```bash
sudo nginx -t  # 测试配置
sudo systemctl reload nginx
```

---

## 🔍 验证配置

### 检查用户和权限

```bash
# 检查用户
id deployer

# 检查 sudo 权限
sudo -u deployer sudo -n echo "无密码 sudo 正常"
```

### 检查防火墙状态

```bash
sudo ufw status verbose
```

应该看到：
- ✅ OpenSSH (22/tcp) - ALLOW
- ✅ Nginx Full (80, 443/tcp) - ALLOW

### 检查 Swap

```bash
free -h
swapon --show
```

应该显示 8GB Swap 已启用。

### 检查 SSH 配置

```bash
sudo sshd -T | grep -E "ClientAliveInterval|PasswordAuthentication|PubkeyAuthentication"
```

应该看到：
- `ClientAliveInterval 60`
- `PasswordAuthentication yes`（或 no，取决于您的安全设置）
- `PubkeyAuthentication yes`

### 检查 Nginx 配置

```bash
sudo nginx -t
sudo systemctl status nginx
```

---

## 🐛 故障排除

### 问题 1：脚本执行失败

**错误信息：** `E: Unable to locate package ...`

**解决方法：**
```bash
# 更新 apt 源
sudo apt update

# 重新运行脚本
sudo bash complete-initial-setup.sh
```

### 问题 2：无法切换到 deployer 用户

**错误信息：** `su: user deployer does not exist`

**解决方法：**
```bash
# 手动创建用户
sudo useradd -m -s /bin/bash deployer
sudo usermod -aG sudo deployer
sudo su - deployer
```

### 问题 3：UFW 防火墙阻止连接

**错误信息：** `Connection refused` 或 `Connection timed out`

**解决方法：**
```bash
# 检查防火墙状态
sudo ufw status

# 如果需要，临时允许所有连接（仅用于测试）
sudo ufw allow from any to any

# 或者，确保 SSH 端口开放
sudo ufw allow 22/tcp
sudo ufw reload
```

### 问题 4：Nginx 配置错误

**错误信息：** `nginx: [emerg] ...`

**解决方法：**
```bash
# 测试配置
sudo nginx -t

# 查看错误详情
sudo tail -f /var/log/nginx/error.log

# 如果配置文件损坏，可以恢复默认配置
sudo rm /etc/nginx/sites-enabled/telegram-ai-system
sudo ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

---

## 📚 相关文档

- [GitHub Actions SSH 配置指南](./SETUP_GITHUB_ACTIONS_SSH.md)
- [防火墙修复指南](./FIX_FIREWALL_FOR_GITHUB_ACTIONS.md)
- [Ubuntu 22.04 PM2 部署文档](./UBUNTU22_PM2_DEPLOY.md)

---

## ✅ 完成检查清单

初始化完成后，请确认：

- [ ] 用户 `deployer` 已创建并可登录
- [ ] SSH Key 已生成，公钥已复制（用于 GitHub Actions）
- [ ] 项目目录 `/home/deployer/telegram-ai-system` 已创建
- [ ] Node.js 20.x 已安装 (`node --version`)
- [ ] Python 3.10+ 已安装 (`python3 --version`)
- [ ] PM2 已全局安装 (`pm2 --version`)
- [ ] Nginx 已安装并运行 (`sudo systemctl status nginx`)
- [ ] UFW 防火墙已启用并允许 SSH、HTTP、HTTPS
- [ ] Swap 文件 8GB 已创建并启用 (`free -h`)
- [ ] SSH 配置已优化（ClientAliveInterval 60）
- [ ] Nginx 配置已创建（`/etc/nginx/sites-available/telegram-ai-system`）

---

**🎉 恭喜！服务器初始化完成，可以开始部署项目了！**
