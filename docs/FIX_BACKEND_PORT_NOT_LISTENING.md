# 修复后端端口 8000 未监听问题

## 🚨 问题描述

PM2 显示后端服务为 "online"，但端口 8000 未监听，健康检查失败。

**可能原因：**
1. 后端服务启动时出错，但 PM2 没有正确检测到
2. Python 依赖缺失或虚拟环境问题
3. 应用代码错误导致启动失败
4. 端口被其他进程占用
5. 权限问题

---

## ✅ 快速诊断

运行诊断脚本：

```bash
# 切换到 deployer 用户
sudo su - deployer
cd /home/deployer/telegram-ai-system

# 运行诊断脚本
bash scripts/server/diagnose-backend-issue.sh
```

诊断脚本会检查：
- PM2 服务状态
- 端口监听情况
- 后端日志（错误和标准输出）
- 虚拟环境和依赖
- 应用文件存在性
- 手动启动测试

---

## 🔧 修复步骤

### 步骤 1：查看后端日志

```bash
# 查看 PM2 日志（实时）
pm2 logs backend --lines 100

# 或者查看错误日志文件
tail -100 /home/deployer/telegram-ai-system/logs/backend-error.log

# 查看标准输出日志
tail -100 /home/deployer/telegram-ai-system/logs/backend-out.log
```

**重点关注：**
- Python 导入错误
- 模块未找到
- 端口绑定失败
- 配置文件缺失

### 步骤 2：检查虚拟环境和依赖

```bash
cd /home/deployer/telegram-ai-system/admin-backend

# 激活虚拟环境
source venv/bin/activate

# 检查 uvicorn 是否存在
which uvicorn
uvicorn --version

# 检查关键依赖
pip list | grep -E "uvicorn|fastapi|pydantic"

# 如果依赖缺失，重新安装
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

### 步骤 3：手动测试启动

```bash
cd /home/deployer/telegram-ai-system/admin-backend
source venv/bin/activate

# 尝试手动启动（查看具体错误）
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 如果启动成功，按 Ctrl+C 停止
# 查看启动时的错误信息
```

### 步骤 4：修复常见问题

#### 问题 A：模块未找到 (ModuleNotFoundError)

```bash
cd /home/deployer/telegram-ai-system/admin-backend
source venv/bin/activate

# 重新安装所有依赖
pip install -r requirements.txt

# 检查 Python 路径
python -c "import sys; print('\n'.join(sys.path))"
```

#### 问题 B：应用文件不存在

```bash
# 检查应用结构
ls -la /home/deployer/telegram-ai-system/admin-backend/app/

# 应该看到 main.py
# 如果不存在，检查项目是否完整克隆
cd /home/deployer/telegram-ai-system
git status
git pull origin main
```

#### 问题 C：端口被占用

```bash
# 检查端口占用
sudo lsof -i :8000

# 如果被占用，找到进程并停止
sudo kill -9 <PID>

# 或者更改端口（在 ecosystem.config.js 中）
```

#### 问题 D：权限问题

```bash
# 确保目录权限正确
sudo chown -R deployer:deployer /home/deployer/telegram-ai-system

# 确保虚拟环境可执行
chmod +x /home/deployer/telegram-ai-system/admin-backend/venv/bin/*
```

### 步骤 5：重启后端服务

```bash
# 停止后端服务
pm2 stop backend
pm2 delete backend

# 重新启动
pm2 start ecosystem.config.js

# 或者只启动后端
pm2 start ecosystem.config.js --only backend

# 查看状态
pm2 status
pm2 logs backend --lines 50
```

### 步骤 6：验证修复

```bash
# 检查端口监听
sudo ss -tlnp | grep 8000

# 测试健康检查
curl http://localhost:8000/health
# 或者
curl http://localhost:8000/api/health

# 检查 PM2 状态
pm2 status
```

---

## 📋 完整修复脚本

如果上述步骤无法解决问题，执行完整修复：

```bash
#!/bin/bash
# 完整修复脚本

sudo su - deployer
cd /home/deployer/telegram-ai-system

# 1. 停止后端服务
pm2 stop backend 2>/dev/null || true
pm2 delete backend 2>/dev/null || true

# 2. 确保虚拟环境完整
cd admin-backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..

# 3. 修复权限
sudo chown -R deployer:deployer /home/deployer/telegram-ai-system
chmod +x admin-backend/venv/bin/*

# 4. 确保日志目录存在
mkdir -p logs

# 5. 测试手动启动（检查是否有错误）
cd admin-backend
source venv/bin/activate
timeout 3 uvicorn app.main:app --host 0.0.0.0 --port 8000 || echo "启动测试完成"
deactivate
cd ..

# 6. 重新启动 PM2 服务
pm2 start ecosystem.config.js --only backend

# 7. 等待并检查
sleep 5
pm2 status
pm2 logs backend --lines 20

# 8. 验证端口
echo ""
echo "检查端口 8000："
sudo ss -tlnp | grep 8000 || echo "端口未监听，请查看日志"
```

---

## 🔍 常见错误和解决方案

### 错误 1：`ModuleNotFoundError: No module named 'xxx'`

**解决方案：**
```bash
cd /home/deployer/telegram-ai-system/admin-backend
source venv/bin/activate
pip install -r requirements.txt
```

### 错误 2：`Address already in use`

**解决方案：**
```bash
# 查找占用端口的进程
sudo lsof -i :8000
# 停止进程
sudo kill -9 <PID>
```

### 错误 3：`Permission denied`

**解决方案：**
```bash
sudo chown -R deployer:deployer /home/deployer/telegram-ai-system
chmod +x admin-backend/venv/bin/*
```

### 错误 4：`FileNotFoundError: [Errno 2] No such file or directory`

**解决方案：**
```bash
# 检查应用文件是否存在
ls -la admin-backend/app/
# 如果不存在，重新克隆项目
cd /home/deployer/telegram-ai-system
git pull origin main
```

---

## ✅ 验证清单

修复后，确认以下项目：

- [ ] PM2 显示 backend 为 online
- [ ] 端口 8000 正在监听（`ss -tlnp | grep 8000`）
- [ ] 健康检查通过（`curl http://localhost:8000/health`）
- [ ] 日志中没有错误信息
- [ ] 可以访问后端 API

---

**如果问题仍然存在，请运行诊断脚本并提供完整的错误日志！**
