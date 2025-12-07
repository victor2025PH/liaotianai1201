# 🚀 部署流程 - 下一步操作

## ✅ 已完成

- [x] GitHub Actions 工作流文件已创建 (`.github/workflows/deploy.yml`)
- [x] GitHub Secrets 已配置
- [x] Systemd 服务已安装

---

## 📋 下一步操作清单

### 步骤 1: 提交并推送部署工作流（本地执行）

```bash
# 在本地项目根目录
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions automatic deployment workflow"
git push origin main
```

### 步骤 2: 确保服务在服务器上正常运行

如果服务仍然启动失败，需要先修复：

```bash
# 在服务器上执行
cd ~/telegram-ai-system

# 查看错误日志
bash scripts/server/view-service-logs.sh

# 或手动查看
sudo journalctl -u telegram-backend -n 100 --no-pager

# 根据错误修复后，重启服务
sudo systemctl restart telegram-backend
sudo systemctl status telegram-backend
```

### 步骤 3: 验证 GitHub Actions 工作流

1. 打开 GitHub 仓库
2. 点击 **Actions** 标签
3. 应该能看到 **Deploy to Server** workflow
4. 推送代码后会自动触发，或点击 **Run workflow** 手动触发

### 步骤 4: 测试自动部署

#### 方法 1: 推送代码触发（推荐）

```bash
# 在本地
git add .
git commit -m "Test automatic deployment"
git push origin main
```

#### 方法 2: 手动触发

1. 打开 GitHub 仓库
2. 进入 **Actions** → **Deploy to Server**
3. 点击 **Run workflow** → **Run workflow**

### 步骤 5: 验证部署结果

#### 在 GitHub 上检查：

1. 打开 **Actions** 标签
2. 查看最新的 workflow run
3. 检查是否有错误

#### 在服务器上检查：

```bash
# 检查服务状态
sudo systemctl status telegram-backend

# 检查应用是否运行
curl http://localhost:8000/health

# 查看服务日志
sudo journalctl -u telegram-backend -f
```

---

## 🔍 如果部署失败

### 检查 GitHub Actions 日志

1. 打开失败的 workflow run
2. 查看 **Deploy to server** step 的日志
3. 找出错误信息

### 常见问题

#### 问题 1: SSH 连接失败

**错误：** `ssh: handshake failed`

**解决：**
- 检查 `SSH_HOST` 是否正确
- 检查 `SSH_PRIVATE_KEY` 是否完整（包括 `-----BEGIN` 和 `-----END`）
- 检查服务器防火墙是否允许 SSH

#### 问题 2: Git pull 失败

**错误：** `git pull` 失败

**解决：**
```bash
# 在服务器上手动执行
cd ~/telegram-ai-system
git pull origin main
```

#### 问题 3: 虚拟环境不存在

**错误：** `source: admin-backend/venv/bin/activate: No such file or directory`

**解决：**
```bash
# 在服务器上创建虚拟环境
cd ~/telegram-ai-system/admin-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 问题 4: 服务重启失败

**错误：** `Failed to restart telegram-backend.service`

**解决：**
```bash
# 检查服务是否存在
sudo systemctl status telegram-backend

# 如果不存在，重新安装
cd ~/telegram-ai-system
sudo bash deploy/systemd/setup-service.sh
```

---

## ✅ 成功标志

部署成功后，你应该看到：

1. **GitHub Actions** 显示绿色 ✓
2. **服务器服务状态**：`Active: active (running)`
3. **健康检查**：`curl http://localhost:8000/health` 返回成功

---

## 📝 完整流程总结

```
本地开发 → git push origin main 
         ↓
GitHub Actions 自动触发
         ↓
SSH 连接到服务器
         ↓
执行部署脚本：
  1. git pull
  2. 更新依赖
  3. 重启服务
         ↓
部署完成 ✓
```

---

**最后更新：** 2025-01-17

