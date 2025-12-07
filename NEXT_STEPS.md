# 🎯 下一步操作指南

## 📊 当前状态

✅ Systemd 服务已安装  
❌ 服务启动失败（自动重启循环）  
⏳ 需要诊断和修复

---

## 🔍 步骤 1: 诊断问题

在服务器上执行：

```bash
cd ~/telegram-ai-system

# 运行诊断脚本
bash scripts/server/diagnose-service.sh
```

**或者手动检查：**

```bash
# 查看服务状态
sudo systemctl status telegram-backend

# 查看详细日志
sudo journalctl -u telegram-backend -n 100 --no-pager

# 查看实时日志
sudo journalctl -u telegram-backend -f
```

---

## 🔧 步骤 2: 修复问题

### 方法 A: 使用自动修复脚本（推荐）

```bash
cd ~/telegram-ai-system

# 运行修复脚本
bash scripts/server/fix-service.sh
```

### 方法 B: 手动修复

根据诊断结果，常见问题和解决方案：

#### 问题 1: 虚拟环境不存在或依赖缺失

```bash
cd ~/telegram-ai-system/admin-backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

#### 问题 2: .env 文件缺失

```bash
cd ~/telegram-ai-system/admin-backend

# 创建 .env 文件
cat > .env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=change_me_in_production
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
EOF
```

#### 问题 3: 端口被占用

```bash
# 查找占用 8000 端口的进程
sudo lsof -i :8000

# 或使用
sudo netstat -tlnp | grep 8000

# 停止占用端口的进程
sudo kill -9 <PID>
```

#### 问题 4: 权限问题

```bash
cd ~/telegram-ai-system

# 修复权限
sudo chown -R ubuntu:ubuntu admin-backend
chmod +x admin-backend/venv/bin/*
```

#### 问题 5: 服务文件路径错误

```bash
# 重新运行安装脚本
cd ~/telegram-ai-system
sudo bash deploy/systemd/setup-service.sh
```

---

## ✅ 步骤 3: 验证服务

修复后验证：

```bash
# 检查服务状态
sudo systemctl status telegram-backend

# 应该显示: Active: active (running)

# 测试 API
curl http://localhost:8000/health

# 或
curl http://localhost:8000/healthz
```

---

## 🚀 步骤 4: 配置 GitHub Actions（如果服务正常）

服务正常运行后，配置 GitHub Actions 自动部署：

### 4.1 配置 GitHub Secrets

1. 打开 GitHub 仓库
2. 进入 **Settings** → **Secrets and variables** → **Actions**
3. 添加以下 Secrets：

#### SSH_HOST
- **Name:** `SSH_HOST`
- **Value:** `10.56.130.4`

#### SSH_USERNAME
- **Name:** `SSH_USERNAME`
- **Value:** `ubuntu`

#### SSH_PRIVATE_KEY
- **Name:** `SSH_PRIVATE_KEY`
- **Value:** 从服务器获取的私钥内容

**获取私钥：**
```bash
# 在服务器上执行
cat ~/.ssh/github_actions_deploy
```

### 4.2 测试自动部署

```bash
# 在本地推送代码
git add .
git commit -m "Test automatic deployment"
git push origin main
```

或在 GitHub 上手动触发：**Actions** → **Deploy to Server** → **Run workflow**

---

## 📋 完整检查清单

- [ ] 服务状态正常：`sudo systemctl status telegram-backend`
- [ ] 服务日志无错误：`sudo journalctl -u telegram-backend -n 50`
- [ ] API 可访问：`curl http://localhost:8000/health`
- [ ] 虚拟环境存在：`ls -la admin-backend/venv`
- [ ] 依赖已安装：`admin-backend/venv/bin/pip list`
- [ ] .env 文件存在：`cat admin-backend/.env`
- [ ] GitHub Secrets 已配置
- [ ] 自动部署测试成功

---

## 🆘 如果仍然失败

### 查看详细错误

```bash
# 查看完整日志
sudo journalctl -u telegram-backend -n 200 --no-pager

# 实时查看日志
sudo journalctl -u telegram-backend -f

# 手动测试启动
cd ~/telegram-ai-system/admin-backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 常见错误和解决方案

| 错误信息 | 解决方案 |
|---------|---------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `Port already in use` | `sudo lsof -i :8000` 然后 `sudo kill -9 <PID>` |
| `Permission denied` | `sudo chown -R ubuntu:ubuntu admin-backend` |
| `Database connection error` | 检查 `.env` 文件中的 `DATABASE_URL` |
| `File not found` | 检查服务文件中的路径是否正确 |

---

## 🎯 推荐执行顺序

1. **立即执行：** `bash scripts/server/diagnose-service.sh`
2. **根据诊断结果：** `bash scripts/server/fix-service.sh`
3. **验证：** `sudo systemctl status telegram-backend`
4. **如果成功：** 配置 GitHub Secrets
5. **测试：** 推送代码触发自动部署

---

**最后更新：** 2025-01-17

