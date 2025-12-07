# 🔍 服务启动失败排查指南

## ❌ 当前问题

服务启动失败，退出码为 `1/FAILURE`。需要查看详细错误日志来找出原因。

---

## 🔍 步骤 1: 查看详细错误日志

在服务器上执行：

```bash
cd ~/telegram-ai-system

# 查看最近的日志（推荐）
bash scripts/server/view-service-logs.sh

# 或手动查看
sudo journalctl -u telegram-backend -n 100 --no-pager

# 实时查看日志
sudo journalctl -u telegram-backend -f
```

---

## 🧪 步骤 2: 手动测试启动

手动启动应用以查看具体错误：

```bash
cd ~/telegram-ai-system

# 使用测试脚本
bash scripts/server/test-startup.sh

# 或手动执行
cd admin-backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**按 Ctrl+C 停止**，然后根据错误信息修复。

---

## 🔧 常见错误和解决方案

### 错误 1: ModuleNotFoundError

**错误信息：**
```
ModuleNotFoundError: No module named 'xxx'
```

**解决方案：**
```bash
cd ~/telegram-ai-system/admin-backend
source venv/bin/activate
pip install -r requirements.txt
```

### 错误 2: 数据库连接错误

**错误信息：**
```
sqlalchemy.exc.OperationalError: unable to open database file
```

**解决方案：**
```bash
cd ~/telegram-ai-system/admin-backend

# 检查 .env 文件
cat .env

# 确保数据库路径正确
# 如果是 SQLite，确保目录存在
mkdir -p $(dirname $(grep DATABASE_URL .env | cut -d= -f2 | sed 's|sqlite:///||'))
```

### 错误 3: 端口被占用

**错误信息：**
```
Address already in use
```

**解决方案：**
```bash
# 查找占用端口的进程
sudo lsof -i :8000

# 停止进程
sudo kill -9 <PID>

# 或使用
sudo netstat -tlnp | grep 8000
```

### 错误 4: 权限问题

**错误信息：**
```
Permission denied
```

**解决方案：**
```bash
cd ~/telegram-ai-system
sudo chown -R ubuntu:ubuntu admin-backend
chmod +x admin-backend/venv/bin/*
```

### 错误 5: 导入错误

**错误信息：**
```
ImportError: cannot import name 'xxx' from 'app.xxx'
```

**解决方案：**
```bash
# 检查 Python 路径
cd ~/telegram-ai-system/admin-backend
source venv/bin/activate
python -c "import sys; print(sys.path)"

# 确保在正确的目录
pwd  # 应该是 ~/telegram-ai-system/admin-backend
```

### 错误 6: 环境变量问题

**错误信息：**
```
KeyError: 'DATABASE_URL'
```

**解决方案：**
```bash
cd ~/telegram-ai-system/admin-backend

# 检查 .env 文件
cat .env

# 如果不存在，创建它
cat > .env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=change_me_in_production
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
EOF
```

---

## 🔄 完整修复流程

### 方法 1: 使用诊断脚本

```bash
cd ~/telegram-ai-system

# 1. 查看日志
bash scripts/server/view-service-logs.sh

# 2. 测试启动
bash scripts/server/test-startup.sh

# 3. 根据错误修复

# 4. 重启服务
sudo systemctl restart telegram-backend
```

### 方法 2: 手动逐步排查

```bash
cd ~/telegram-ai-system/admin-backend

# 1. 激活虚拟环境
source venv/bin/activate

# 2. 检查依赖
pip list | grep -i "fastapi\|uvicorn\|sqlalchemy"

# 3. 检查 .env
cat .env

# 4. 测试导入
python -c "from app.main import app; print('Import OK')"

# 5. 手动启动查看错误
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📋 检查清单

在修复前，确认：

- [ ] 虚拟环境存在：`ls -la admin-backend/venv`
- [ ] 依赖已安装：`admin-backend/venv/bin/pip list | grep fastapi`
- [ ] .env 文件存在：`cat admin-backend/.env`
- [ ] 端口未被占用：`sudo lsof -i :8000`
- [ ] 权限正确：`ls -la admin-backend/venv/bin/uvicorn`
- [ ] 工作目录正确：服务文件中的 `WorkingDirectory` 路径正确

---

## 🎯 推荐执行顺序

1. **立即执行：** `bash scripts/server/view-service-logs.sh`
2. **查看错误：** 从日志中找出具体的错误信息
3. **测试启动：** `bash scripts/server/test-startup.sh`
4. **修复问题：** 根据错误信息使用上面的解决方案
5. **重启服务：** `sudo systemctl restart telegram-backend`
6. **验证：** `sudo systemctl status telegram-backend`

---

## 🆘 如果仍然失败

### 获取完整错误信息

```bash
# 查看完整日志
sudo journalctl -u telegram-backend --no-pager > service-errors.log
cat service-errors.log

# 或实时查看
sudo journalctl -u telegram-backend -f
```

### 检查系统资源

```bash
# 检查磁盘空间
df -h

# 检查内存
free -h

# 检查 Python 进程
ps aux | grep python
```

---

**下一步：** 在服务器上运行 `bash scripts/server/view-service-logs.sh` 查看具体错误信息。

