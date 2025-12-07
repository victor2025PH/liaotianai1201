# ⚡ 快速部署指南

## 🎯 当前状态

✅ SSH 密钥已生成和配置  
⏳ 需要上传部署文件到 GitHub

---

## 📤 步骤 1: 上传部署文件到 GitHub（本地执行）

在本地项目目录执行：

```bash
# 添加所有新创建的部署文件
git add .github/workflows/deploy.yml
git add deploy/systemd/telegram-backend.service
git add deploy/systemd/setup-service.sh
git add DEPLOY_GUIDE.md
git add scripts/server/quick-deploy-setup.sh

# 提交
git commit -m "Add GitHub Actions deployment workflow and systemd service"

# 推送到 GitHub
git push origin main
```

---

## 📥 步骤 2: 在服务器上拉取文件（服务器执行）

```bash
cd ~/telegram-ai-system

# 拉取最新代码
git pull origin main

# 运行快速设置脚本
bash scripts/server/quick-deploy-setup.sh
```

**或者手动执行：**

```bash
cd ~/telegram-ai-system

# 拉取代码
git pull origin main

# 安装服务（需要 sudo）
sudo bash deploy/systemd/setup-service.sh
```

---

## 🔐 步骤 3: 配置 GitHub Secrets

1. 打开 GitHub 仓库
2. 进入 **Settings** → **Secrets and variables** → **Actions**
3. 添加以下 Secrets：

### SSH_HOST
- **Name:** `SSH_HOST`
- **Value:** `10.56.130.4` (你的服务器 IP)

### SSH_USERNAME
- **Name:** `SSH_USERNAME`
- **Value:** `ubuntu`

### SSH_PRIVATE_KEY
- **Name:** `SSH_PRIVATE_KEY`
- **Value:** 从服务器复制的私钥内容（已在终端显示）

**获取私钥：**
```bash
# 在服务器上执行
cat ~/.ssh/github_actions_deploy
```

复制完整的输出（包括 `-----BEGIN` 和 `-----END` 行）

---

## ✅ 步骤 4: 测试部署

### 方法 1: 推送代码触发

```bash
# 在本地
git add .
git commit -m "Test deployment"
git push origin main
```

### 方法 2: 手动触发

1. 打开 GitHub 仓库
2. 点击 **Actions** 标签
3. 选择 **Deploy to Server** workflow
4. 点击 **Run workflow** → **Run workflow**

---

## 🔍 验证部署

### 在服务器上检查：

```bash
# 检查服务状态
sudo systemctl status telegram-backend

# 查看日志
sudo journalctl -u telegram-backend -f

# 检查应用
curl http://localhost:8000/health
```

### 在 GitHub 上检查：

1. 打开 **Actions** 标签
2. 查看最新的 workflow run
3. 检查是否有错误

---

## 🆘 常见问题

### 问题 1: `deploy/systemd/setup-service.sh: No such file or directory`

**原因：** 文件还没有被推送到服务器

**解决：**
```bash
# 在服务器上
cd ~/telegram-ai-system
git pull origin main
```

### 问题 2: 权限被拒绝

**解决：**
```bash
# 确保使用 sudo
sudo bash deploy/systemd/setup-service.sh
```

### 问题 3: 虚拟环境不存在

**解决：**
```bash
cd ~/telegram-ai-system/admin-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📋 完整流程总结

1. ✅ **服务器端**：生成 SSH 密钥对（已完成）
2. ⏳ **本地**：上传部署文件到 GitHub
3. ⏳ **服务器端**：拉取文件并安装服务
4. ⏳ **GitHub**：配置 Secrets
5. ⏳ **测试**：推送代码触发部署

---

**下一步：** 在本地执行步骤 1，然后到服务器执行步骤 2

