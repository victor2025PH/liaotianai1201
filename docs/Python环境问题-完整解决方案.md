# 🔧 Python 环境问题 - 完整解决方案

## 🎯 问题分析

根据截图，发现关键问题：

1. **uvicorn 模块未安装**：`No module named uvicorn`
2. **pip 安装被阻止**：`externally-managed-environment` 错误（Ubuntu 24.04 PEP 668 限制）
3. **后端服务无法启动**：因为缺少必要的 Python 依赖

---

## ✅ 解决方案（3 种方法）

### 方法 1: 使用 --break-system-packages（最简单）

Ubuntu 24.04 允许使用 `--break-system-packages` 标志：

```bash
# 安装 uvicorn 和 fastapi
pip3 install uvicorn fastapi --break-system-packages

# 验证安装
python3 -c "import uvicorn; print('uvicorn 已安装')"
```

### 方法 2: 使用虚拟环境（推荐）

```bash
cd ~/liaotian

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install uvicorn fastapi

# 如果后端有 requirements.txt
cd admin-backend
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

### 方法 3: 使用系统包管理器

```bash
# 安装系统包（如果可用）
sudo apt update
sudo apt install python3-uvicorn python3-fastapi 2>/dev/null || echo "包不可用"
```

---

## 🚀 完整修复方案（一条龙）

在服务器上执行以下命令，修复所有问题：

```bash
cd ~/liaotian && sudo bash -c '
echo "========================================="
echo "完整修复 Python 环境和服务问题"
echo "========================================="
echo ""

echo "=== 步骤 1: 停止所有服务 ==="
systemctl stop liaotian-frontend 2>/dev/null || true
systemctl stop liaotian-backend 2>/dev/null || true

# 停止所有占用端口的进程
pkill -9 -f "next-server" 2>/dev/null || true
pkill -9 -f "node.*next" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "python.*uvicorn" 2>/dev/null || true

# 清理端口
PORT_3000_PIDS=$(ss -tlnp | grep :3000 | grep -oP "pid=\K[0-9]+" 2>/dev/null || true)
for PID in $PORT_3000_PIDS; do kill -9 "$PID" 2>/dev/null || true; done

PORT_8000_PIDS=$(ss -tlnp | grep :8000 | grep -oP "pid=\K[0-9]+" 2>/dev/null || true)
for PID in $PORT_8000_PIDS; do kill -9 "$PID" 2>/dev/null || true; done

sleep 5

echo ""
echo "=== 步骤 2: 安装 Python 依赖 ==="
cd /home/ubuntu/liaotian

# 检查 uvicorn
if python3 -c "import uvicorn" 2>/dev/null; then
    echo "✅ uvicorn 已安装"
else
    echo "安装 uvicorn 和 fastapi..."
    
    # 方法 1: 使用 --break-system-packages
    if pip3 install uvicorn fastapi --break-system-packages 2>/dev/null; then
        echo "✅ 使用 --break-system-packages 安装成功"
    # 方法 2: 使用 --user
    elif pip3 install uvicorn fastapi --user 2>/dev/null; then
        echo "✅ 使用 --user 安装成功"
    else
        echo "⚠️  需要手动安装"
    fi
fi

# 验证
if python3 -c "import uvicorn" 2>/dev/null; then
    echo "✅ uvicorn 安装成功"
else
    echo "❌ uvicorn 安装失败，请手动安装"
fi

echo ""
echo "=== 步骤 3: 修复 Systemd 服务文件 ==="

# 后端服务（使用完整路径）
cat > /etc/systemd/system/liaotian-backend.service << "EOFBACKEND"
[Unit]
Description=Liaotian Backend API Service (FastAPI)
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/admin-backend
Environment="PATH=/usr/bin:/bin:/usr/local/bin:/home/ubuntu/.local/bin"
ExecStart=/bin/bash -c "cd /home/ubuntu/liaotian/admin-backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 120"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-backend

[Install]
WantedBy=multi-user.target
EOFBACKEND

# 前端服务
cat > /etc/systemd/system/liaotian-frontend.service << "EOFFRONTEND"
[Unit]
Description=Liaotian Frontend Service (Next.js)
After=network.target liaotian-backend.service
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/saas-demo
Environment="PATH=/usr/bin:/bin:/usr/local/bin"
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/bin/bash -c "if [ -d /home/ubuntu/liaotian/saas-demo/.next/standalone ]; then cd /home/ubuntu/liaotian/saas-demo/.next/standalone && PORT=3000 /usr/bin/node server.js; else cd /home/ubuntu/liaotian/saas-demo && /usr/bin/npm start; fi"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOFFRONTEND

echo "✅ 服务文件已修复"

echo ""
echo "=== 步骤 4: 重新加载 systemd ==="
systemctl daemon-reload

echo ""
echo "=== 步骤 5: 启动服务 ==="
systemctl start liaotian-backend
sleep 10
systemctl start liaotian-frontend
sleep 10

echo ""
echo "=== 步骤 6: 验证 ==="
systemctl is-active liaotian-backend && echo "✅ 后端运行中" || echo "❌ 后端未运行"
systemctl is-active liaotian-frontend && echo "✅ 前端运行中" || echo "❌ 前端未运行"

ss -tlnp | grep :3000 && echo "✅ 端口 3000 监听" || echo "❌ 端口 3000 未监听"
ss -tlnp | grep :8000 && echo "✅ 端口 8000 监听" || echo "❌ 端口 8000 未监听"

echo ""
echo "✅ 修复完成！"
'
```

---

## 🔍 手动安装步骤

如果自动安装失败，手动执行：

### 1. 安装 uvicorn

```bash
# 方法 1: 使用 --break-system-packages（推荐）
pip3 install uvicorn fastapi --break-system-packages

# 方法 2: 使用 --user
pip3 install uvicorn fastapi --user

# 方法 3: 创建虚拟环境
python3 -m venv ~/venv
source ~/venv/bin/activate
pip install uvicorn fastapi
deactivate
```

### 2. 验证安装

```bash
# 检查 uvicorn
python3 -c "import uvicorn; print('uvicorn 已安装')"

# 检查版本
python3 -m uvicorn --version
```

### 3. 更新 Systemd 服务配置

如果使用虚拟环境，需要更新后端服务配置：

```bash
sudo nano /etc/systemd/system/liaotian-backend.service
```

修改 `ExecStart` 为：
```ini
ExecStart=/bin/bash -c "cd /home/ubuntu/liaotian/admin-backend && source /home/ubuntu/venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

---

## ✅ 修复后验证

```bash
# 检查 Python 依赖
python3 -c "import uvicorn; import fastapi; print('✅ 依赖已安装')"

# 检查服务状态
sudo systemctl status liaotian-backend
sudo systemctl status liaotian-frontend

# 检查端口
ss -tlnp | grep -E ":(3000|8000)"

# 测试后端
curl http://localhost:8000/health
```

---

**最后更新**: 2025-12-07
