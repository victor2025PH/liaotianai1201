# 🚀 GitHub Actions 自动部署指南

本指南将帮助你设置 GitHub Actions 自动部署流程，实现代码推送到 `main` 分支时自动部署到服务器。

---

## 📋 目录

1. [前置准备](#前置准备)
2. [服务器端设置](#服务器端设置)
3. [GitHub 配置](#github-配置)
4. [验证部署](#验证部署)
5. [故障排查](#故障排查)

---

## 🔧 前置准备

### 服务器需要安装的软件

在服务器上执行以下命令安装必要的软件：

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Git
sudo apt install -y git

# 安装 Python 3 和虚拟环境
sudo apt install -y python3 python3-pip python3-venv

# 安装其他可能需要的依赖
sudo apt install -y build-essential curl
```

### 验证安装

```bash
git --version
python3 --version
python3 -m venv --help
```

---

## 🔑 服务器端设置

### 步骤 1: 生成 SSH 密钥对

在服务器上执行以下命令生成 SSH 密钥对：

```bash
# 切换到部署用户（通常是 ubuntu 或你的用户名）
cd ~

# 生成 SSH 密钥对（如果还没有）
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# 按 Enter 使用默认路径，或设置密码（推荐设置密码以提高安全性）
```

**重要提示：**
- 密钥文件会生成在 `~/.ssh/` 目录
- `github_actions_deploy` 是私钥（**保密，不要泄露**）
- `github_actions_deploy.pub` 是公钥（可以公开）

### 步骤 2: 配置 SSH 公钥

将公钥添加到服务器的 `authorized_keys` 文件中：

```bash
# 查看公钥内容
cat ~/.ssh/github_actions_deploy.pub

# 将公钥添加到 authorized_keys（如果文件不存在会自动创建）
cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys

# 设置正确的权限
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### 步骤 3: 测试 SSH 连接

在服务器上测试 SSH 连接是否正常：

```bash
# 测试本地 SSH 连接
ssh -i ~/.ssh/github_actions_deploy localhost

# 如果成功，输入 exit 退出
exit
```

### 步骤 4: 准备项目目录

```bash
# 创建项目目录（如果不存在）
mkdir -p ~/telegram-ai-system
cd ~/telegram-ai-system

# 如果是新服务器，克隆仓库
git clone https://github.com/你的用户名/你的仓库名.git .

# 如果目录已存在，确保是最新代码
git pull origin main
```

### 步骤 5: 设置虚拟环境

```bash
cd ~/telegram-ai-system/admin-backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 步骤 6: 安装 Systemd 服务

```bash
# 进入项目根目录
cd ~/telegram-ai-system

# 运行设置脚本（需要 sudo 权限）
sudo bash deploy/systemd/setup-service.sh
```

---

## 🔐 GitHub 配置

### 步骤 1: 获取 SSH 私钥

在服务器上查看私钥内容：

```bash
# 查看私钥内容（复制整个输出，包括 -----BEGIN 和 -----END 行）
cat ~/.ssh/github_actions_deploy
```

**重要：** 私钥内容应该类似这样：
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
...
（更多内容）
...
-----END OPENSSH PRIVATE KEY-----
```

### 步骤 2: 配置 GitHub Secrets

1. 打开你的 GitHub 仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret** 添加以下三个 secrets：

#### Secret 1: `SSH_HOST`
- **Name:** `SSH_HOST`
- **Value:** 你的服务器 IP 地址或域名
  - 例如：`123.456.789.0` 或 `your-server.com`

#### Secret 2: `SSH_USERNAME`
- **Name:** `SSH_USERNAME`
- **Value:** SSH 登录用户名
  - 通常是 `ubuntu` 或 `root`

#### Secret 3: `SSH_PRIVATE_KEY`
- **Name:** `SSH_PRIVATE_KEY`
- **Value:** 从步骤 1 复制的完整私钥内容（包括 `-----BEGIN` 和 `-----END` 行）

#### Secret 4 (可选): `SSH_PORT`
- **Name:** `SSH_PORT`
- **Value:** SSH 端口号（默认是 22）
  - 如果使用默认端口，可以不设置

### 步骤 3: 验证 Secrets 配置

确保所有必需的 secrets 都已配置：
- ✅ `SSH_HOST`
- ✅ `SSH_USERNAME`
- ✅ `SSH_PRIVATE_KEY`
- ⚪ `SSH_PORT` (可选)

---

## ✅ 验证部署

### 方法 1: 手动触发部署

1. 打开 GitHub 仓库
2. 点击 **Actions** 标签
3. 选择 **Deploy to Server** workflow
4. 点击 **Run workflow** → **Run workflow**

### 方法 2: 推送代码触发

```bash
# 在本地项目目录
git add .
git commit -m "Test deployment"
git push origin main
```

### 查看部署日志

1. 在 GitHub 仓库的 **Actions** 页面
2. 点击最新的 workflow run
3. 查看 **Deploy to server** job 的日志

### 检查服务器状态

在服务器上执行：

```bash
# 检查服务状态
sudo systemctl status telegram-backend

# 查看服务日志
sudo journalctl -u telegram-backend -f

# 检查应用是否运行
curl http://localhost:8000/health
```

---

## 🔍 故障排查

### 问题 1: SSH 连接失败

**错误信息：**
```
Error: ssh: handshake failed: ssh: unable to authenticate
```

**解决方案：**
1. 检查 `SSH_HOST` 和 `SSH_USERNAME` 是否正确
2. 验证私钥是否正确复制（包括所有行）
3. 检查服务器上的 `~/.ssh/authorized_keys` 是否包含公钥
4. 检查服务器防火墙是否允许 SSH 连接

### 问题 2: 服务重启失败

**错误信息：**
```
Service restart failed
```

**解决方案：**
```bash
# 在服务器上手动检查服务
sudo systemctl status telegram-backend

# 查看详细错误
sudo journalctl -u telegram-backend -n 50

# 手动重启
sudo systemctl restart telegram-backend
```

### 问题 3: 依赖安装失败

**错误信息：**
```
pip install failed
```

**解决方案：**
```bash
# 在服务器上手动安装依赖
cd ~/telegram-ai-system/admin-backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 问题 4: 权限问题

**错误信息：**
```
Permission denied
```

**解决方案：**
```bash
# 检查文件权限
ls -la ~/telegram-ai-system/admin-backend

# 确保用户有执行权限
chmod +x ~/telegram-ai-system/admin-backend/venv/bin/uvicorn

# 检查 systemd 服务文件权限
sudo chown root:root /etc/systemd/system/telegram-backend.service
```

### 问题 5: 端口被占用

**错误信息：**
```
Address already in use
```

**解决方案：**
```bash
# 查找占用端口的进程
sudo lsof -i :8000

# 或使用
sudo netstat -tlnp | grep 8000

# 停止占用端口的进程
sudo kill -9 <PID>
```

---

## 📝 常用命令

### 服务器端

```bash
# 查看服务状态
sudo systemctl status telegram-backend

# 重启服务
sudo systemctl restart telegram-backend

# 停止服务
sudo systemctl stop telegram-backend

# 启动服务
sudo systemctl start telegram-backend

# 查看日志
sudo journalctl -u telegram-backend -f

# 查看最近 100 行日志
sudo journalctl -u telegram-backend -n 100

# 重新加载服务配置
sudo systemctl daemon-reload
sudo systemctl restart telegram-backend
```

### GitHub Actions

- 查看部署历史：**Actions** → **Deploy to Server**
- 手动触发：**Actions** → **Deploy to Server** → **Run workflow**
- 查看日志：点击具体的 workflow run

---

## 🔒 安全建议

1. **使用 SSH 密钥密码**：生成密钥时设置密码
2. **限制 SSH 访问**：在服务器防火墙中只允许特定 IP 访问 SSH
3. **定期轮换密钥**：定期更换 SSH 密钥对
4. **使用非 root 用户**：使用普通用户运行服务，而不是 root
5. **监控部署日志**：定期检查 GitHub Actions 日志，发现异常及时处理

---

## 📚 相关文件

- `.github/workflows/deploy.yml` - GitHub Actions workflow 配置
- `deploy/systemd/telegram-backend.service` - Systemd 服务配置文件
- `deploy/systemd/setup-service.sh` - 服务安装脚本

---

## 🆘 获取帮助

如果遇到问题：

1. 检查 GitHub Actions 日志
2. 查看服务器服务日志：`sudo journalctl -u telegram-backend -f`
3. 验证 SSH 连接：在本地测试 `ssh -i ~/.ssh/github_actions_deploy user@host`
4. 检查服务状态：`sudo systemctl status telegram-backend`

---

**最后更新：** 2025-01-17

