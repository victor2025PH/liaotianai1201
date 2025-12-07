# GitHub Actions 自动部署配置指南

## 📋 概述

本项目已配置 GitHub Actions 自动部署工作流。当你推送代码到 `main` 分支时，GitHub 会自动将代码部署到服务器并重启服务。

## 🔧 配置步骤

### 步骤 1: 配置 GitHub Secrets

在 GitHub 仓库中配置以下 Secrets：

1. **进入 GitHub 仓库**
   - 访问: `https://github.com/<你的用户名>/<仓库名>/settings/secrets/actions`

2. **添加以下三个 Secrets**:

   | Secret 名称 | 说明 | 示例值 |
   |------------|------|--------|
   | `SERVER_HOST` | 服务器 IP 地址 | `165.154.255.48` |
   | `SERVER_USER` | SSH 用户名 | `ubuntu` |
   | `SERVER_SSH_KEY` | SSH 私钥内容 | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

### 步骤 2: 生成 SSH 密钥对（如果还没有）

#### 在服务器上生成密钥对

```bash
# 1. SSH 连接到服务器
ssh ubuntu@<你的服务器IP>

# 2. 生成 SSH 密钥对（如果还没有）
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_deploy_key -N ""

# 3. 查看公钥内容
cat ~/.ssh/github_deploy_key.pub

# 4. 将公钥添加到 authorized_keys（允许自己连接）
cat ~/.ssh/github_deploy_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

#### 在本地生成密钥对（推荐）

```powershell
# 在 PowerShell 中执行
ssh-keygen -t rsa -b 4096 -f $env:USERPROFILE\.ssh\github_deploy_key -N ""

# 查看私钥内容（复制整个内容，包括 BEGIN 和 END 行）
Get-Content $env:USERPROFILE\.ssh\github_deploy_key

# 查看公钥内容
Get-Content $env:USERPROFILE\.ssh\github_deploy_key.pub
```

### 步骤 3: 配置服务器

#### 3.1 将公钥添加到服务器

```bash
# 在服务器上执行
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 将公钥内容添加到 authorized_keys
echo "你的公钥内容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

#### 3.2 确保服务器上的项目目录存在

```bash
# 在服务器上执行
mkdir -p /home/ubuntu/telegram-ai-system
cd /home/ubuntu/telegram-ai-system

# 如果是新服务器，需要初始化 Git 仓库
git init
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git pull origin main
```

#### 3.3 确保虚拟环境和服务已配置

```bash
# 在服务器上执行
cd /home/ubuntu/telegram-ai-system

# 创建虚拟环境（如果还没有）
cd admin-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 确保 systemd 服务已配置
# 参考: deploy/systemd/telegram-backend.service
sudo systemctl enable telegram-backend
sudo systemctl start telegram-backend
```

### 步骤 4: 在 GitHub 中添加 Secrets

1. **复制私钥内容**
   - 打开 `~/.ssh/github_deploy_key` 文件
   - 复制**整个内容**（包括 `-----BEGIN OPENSSH PRIVATE KEY-----` 和 `-----END OPENSSH PRIVATE KEY-----`）

2. **在 GitHub 中添加 Secrets**
   - 进入: `Settings` → `Secrets and variables` → `Actions`
   - 点击 `New repository secret`
   - 添加以下三个 Secrets:

   **SERVER_HOST**
   ```
   165.154.255.48
   ```

   **SERVER_USER**
   ```
   ubuntu
   ```

   **SERVER_SSH_KEY**
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
   ...（完整的私钥内容）...
   -----END OPENSSH PRIVATE KEY-----
   ```

## 🚀 使用方式

### 自动部署（推送代码）

```bash
# 1. 在本地修改代码
git add .
git commit -m "Update code"
git push origin main

# 2. GitHub Actions 会自动触发部署
# 3. 查看部署状态: https://github.com/<用户名>/<仓库名>/actions
```

### 手动触发部署

1. 访问 GitHub Actions 页面
2. 选择 "Deploy to Server" 工作流
3. 点击 "Run workflow"
4. 选择分支（通常是 `main`）
5. 点击 "Run workflow" 按钮

## 📊 查看部署状态

### 在 GitHub 上查看

1. 访问: `https://github.com/<用户名>/<仓库名>/actions`
2. 点击最新的工作流运行
3. 查看部署日志

### 在服务器上验证

```bash
# SSH 连接到服务器
ssh ubuntu@<你的服务器IP>

# 检查服务状态
sudo systemctl status telegram-backend

# 查看服务日志
sudo journalctl -u telegram-backend -n 50

# 检查代码是否已更新
cd /home/ubuntu/telegram-ai-system
git log -1
```

## 🔍 故障排查

### 问题 1: 部署失败 - "Permission denied (publickey)"

**原因**: SSH 密钥未正确配置

**解决方案**:
1. 检查 GitHub Secrets 中的 `SERVER_SSH_KEY` 是否包含完整的私钥（包括 BEGIN 和 END 行）
2. 检查服务器上的 `~/.ssh/authorized_keys` 是否包含对应的公钥
3. 检查服务器上的文件权限:
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   ```

### 问题 2: 部署失败 - "git pull failed"

**原因**: 服务器上的 Git 仓库未正确配置

**解决方案**:
```bash
# 在服务器上执行
cd /home/ubuntu/telegram-ai-system
git remote -v  # 检查远程仓库配置
git pull origin main  # 手动测试拉取
```

### 问题 3: 部署失败 - "Service restart failed"

**原因**: systemd 服务未配置或服务启动失败

**解决方案**:
```bash
# 在服务器上执行
# 1. 检查服务文件是否存在
sudo systemctl status telegram-backend

# 2. 查看服务日志
sudo journalctl -u telegram-backend -n 50

# 3. 手动测试启动
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 问题 4: 部署失败 - "Virtual environment not found"

**原因**: 虚拟环境未创建

**解决方案**:
```bash
# 在服务器上执行
cd /home/ubuntu/telegram-ai-system/admin-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📝 工作流文件说明

工作流文件位于: `.github/workflows/deploy.yml`

**触发条件**:
- 推送到 `main` 分支
- 手动触发（workflow_dispatch）

**执行步骤**:
1. 检出代码
2. 通过 SSH 连接到服务器
3. 进入项目目录
4. 拉取最新代码
5. 激活虚拟环境
6. 更新依赖
7. 重启服务
8. 检查服务状态

## ✅ 验证清单

在首次部署前，请确认：

- [ ] GitHub Secrets 已配置（SERVER_HOST, SERVER_USER, SERVER_SSH_KEY）
- [ ] 服务器上的 SSH 密钥已配置
- [ ] 服务器上的项目目录存在 (`/home/ubuntu/telegram-ai-system`)
- [ ] 服务器上的 Git 仓库已初始化并连接到 GitHub
- [ ] 服务器上的虚拟环境已创建
- [ ] 服务器上的 systemd 服务已配置并启用
- [ ] 服务器上的防火墙允许 SSH 连接（端口 22）

## 🎯 下一步

配置完成后，推送代码到 `main` 分支即可触发自动部署！

```bash
git add .
git commit -m "Test automatic deployment"
git push origin main
```

然后访问 GitHub Actions 页面查看部署状态。

