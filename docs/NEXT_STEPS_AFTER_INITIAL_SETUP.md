# 初始化完成后的下一步操作指南

## ✅ 当前状态检查

首先，让我们确认初始化脚本是否完全执行完毕：

```bash
# 检查脚本是否完成（查看最后输出是否显示"🎉 服务器初始化完成！"）
# 如果没有看到完成消息，脚本可能还在执行中或已中断
```

---

## 🔍 验证已完成的项目

### 1. 检查基础环境

```bash
# 检查 Node.js
node --version
# 应该显示: v20.x.x

# 检查 Python
python3 --version
# 应该显示: Python 3.10.x

# 检查 PM2
pm2 --version
# 应该显示版本号

# 检查 Nginx
nginx -v
# 应该显示版本号
```

### 2. 检查用户和目录

```bash
# 检查 deployer 用户是否存在
id deployer

# 检查项目目录是否存在
ls -la /home/deployer/telegram-ai-system

# 检查日志目录
ls -la /home/deployer/telegram-ai-system/logs
```

### 3. 检查 Swap 文件

```bash
# 检查 Swap 是否已启用
free -h
swapon --show
# 应该显示 8GB Swap
```

### 4. 检查防火墙

```bash
# 检查 UFW 状态
sudo ufw status verbose
# 应该显示:
# - OpenSSH (22/tcp) - ALLOW
# - Nginx Full (80, 443/tcp) - ALLOW
```

### 5. 检查 SSH 配置

```bash
# 验证 SSH 配置已生效
sudo sshd -T | grep -E "ClientAliveInterval|PasswordAuthentication|PubkeyAuthentication"
```

---

## 📋 如果脚本未完成

如果初始化脚本没有完全执行，您可以：

### 方法 1：查看脚本输出

滚动终端查看是否有错误，或检查脚本是否还在执行。

### 方法 2：手动完成缺失的步骤

参考主脚本 `scripts/server/complete-initial-setup.sh`，手动执行缺失的部分。

### 方法 3：重新运行脚本（安全）

```bash
# 脚本是幂等的（可以重复运行），大部分操作都会跳过已存在的配置
sudo bash /path/to/complete-initial-setup.sh
```

---

## 🚀 脚本完成后的下一步操作

### 步骤 1：切换到 deployer 用户

```bash
sudo su - deployer
```

### 步骤 2：查看 SSH 公钥（用于 GitHub Actions）

```bash
cat ~/.ssh/id_rsa.pub
```

**重要：** 复制输出的公钥内容，稍后需要添加到 GitHub Secrets。

### 步骤 3：克隆项目代码

```bash
cd /home/deployer/telegram-ai-system

# 克隆项目（替换为您的实际仓库地址）
git clone https://github.com/victor2025PH/liaotianai1201.git .

# 或者如果仓库地址不同，使用：
# git clone <YOUR_REPO_URL> .
```

### 步骤 4：配置 GitHub Actions SSH Key

1. **获取 SSH 私钥（用于 GitHub Secrets）：**

   ```bash
   # 显示私钥（复制全部内容）
   cat ~/.ssh/id_rsa
   ```

2. **添加到 GitHub Secrets：**

   - 访问 GitHub 仓库 → Settings → Secrets and variables → Actions
   - 添加以下 Secrets：
     - `SERVER_HOST`: 您的服务器 IP 地址（例如: `10.56.61.200`）
     - `SERVER_USER`: `deployer`
     - `SERVER_SSH_KEY`: 粘贴上面复制的私钥内容

3. **测试 GitHub Actions 部署：**

   - 推送代码到 `main` 分支，或手动触发 GitHub Actions workflow

### 步骤 5：安装项目依赖

```bash
# 确保在 deployer 用户下
cd /home/deployer/telegram-ai-system

# 安装后端依赖
cd admin-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 安装前端依赖
cd saas-demo
npm install
npm run build
cd ..
```

### 步骤 6：配置 PM2（生成 ecosystem.config.js）

如果项目根目录还没有 `ecosystem.config.js`，需要创建一个：

```bash
cd /home/deployer/telegram-ai-system

# 参考项目文档或使用现有模板
# 确保配置了 backend 和 frontend 两个服务
```

### 步骤 7：启动服务（使用 PM2）

```bash
cd /home/deployer/telegram-ai-system

# 启动服务
pm2 start ecosystem.config.js

# 保存 PM2 配置（开机自启）
pm2 save

# 检查服务状态
pm2 status
pm2 logs
```

### 步骤 8：配置并重启 Nginx

```bash
# 测试 Nginx 配置
sudo nginx -t

# 如果有域名，编辑配置文件
sudo nano /etc/nginx/sites-available/telegram-ai-system

# 将 server_name _; 改为您的域名
# server_name example.com www.example.com;

# 重启 Nginx
sudo systemctl restart nginx

# 检查状态
sudo systemctl status nginx
```

### 步骤 9：验证服务

```bash
# 检查端口监听
sudo netstat -tlnp | grep -E "3000|8000|80|443"

# 或者使用 ss 命令
sudo ss -tlnp | grep -E "3000|8000|80|443"

# 检查 PM2 服务
pm2 list

# 检查服务日志
pm2 logs backend
pm2 logs frontend
```

### 步骤 10：访问网站

在浏览器中访问：
- HTTP: `http://your-server-ip` 或 `http://your-domain.com`
- HTTPS（如果已配置 SSL）: `https://your-domain.com`

---

## 🔒 安全加固（可选但推荐）

### 关闭密码登录，仅使用 SSH Key

```bash
# 编辑 SSH 配置
sudo nano /etc/ssh/sshd_config

# 找到并修改：
PasswordAuthentication no

# 保存后重启 SSH 服务
sudo systemctl restart ssh

# 验证配置
sudo sshd -T | grep PasswordAuthentication
# 应该显示: PasswordAuthentication no
```

**⚠️ 警告：** 在执行此操作前，确保：
1. ✅ SSH Key 已经添加到 `~/.ssh/authorized_keys`
2. ✅ 您可以使用 SSH Key 正常登录
3. ✅ 已经测试过从其他机器使用 Key 登录

---

## 🐛 常见问题排查

### 问题 1：PM2 服务无法启动

```bash
# 检查 PM2 日志
pm2 logs

# 检查端口是否被占用
sudo lsof -i :3000
sudo lsof -i :8000

# 检查文件权限
ls -la /home/deployer/telegram-ai-system
```

### 问题 2：Nginx 502 Bad Gateway

```bash
# 检查后端服务是否运行
pm2 status backend

# 检查后端日志
pm2 logs backend

# 检查端口 8000 是否监听
sudo ss -tlnp | grep 8000
```

### 问题 3：前端无法访问

```bash
# 检查前端服务是否运行
pm2 status frontend

# 检查前端日志
pm2 logs frontend

# 检查端口 3000 是否监听
sudo ss -tlnp | grep 3000

# 检查 Nginx 配置
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### 问题 4：GitHub Actions 部署失败

参考文档：
- [GitHub Actions SSH 配置指南](./SETUP_GITHUB_ACTIONS_SSH.md)
- [防火墙修复指南](./FIX_FIREWALL_FOR_GITHUB_ACTIONS.md)

---

## ✅ 完成检查清单

- [ ] Node.js 20.x 已安装
- [ ] Python 3.10+ 已安装
- [ ] PM2 已全局安装
- [ ] Nginx 已安装并配置
- [ ] `deployer` 用户已创建
- [ ] SSH Key 已生成并查看
- [ ] 项目代码已克隆
- [ ] GitHub Secrets 已配置（SERVER_HOST, SERVER_USER, SERVER_SSH_KEY）
- [ ] 后端依赖已安装
- [ ] 前端已构建
- [ ] PM2 服务已启动（backend, frontend）
- [ ] Nginx 已重启
- [ ] 网站可以访问
- [ ] GitHub Actions 部署测试成功

---

## 📚 相关文档

- [完整初始化脚本说明](./COMPLETE_INITIAL_SETUP.md)
- [GitHub Actions SSH 配置](./SETUP_GITHUB_ACTIONS_SSH.md)
- [防火墙修复指南](./FIX_FIREWALL_FOR_GITHUB_ACTIONS.md)
- [Ubuntu 22.04 PM2 部署文档](./UBUNTU22_PM2_DEPLOY.md)

---

**🎉 完成所有步骤后，您的服务器就可以正常提供服务了！**
