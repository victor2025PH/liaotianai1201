# PM2 被杀死问题解决方案

> **问题**: 所有 PM2 命令都被系统杀死（"Killed"）

---

## 🔍 问题诊断

### 症状
- `pm2 start` → Killed
- `pm2 status` → Killed
- `pm2 save` → Killed
- 所有 PM2 命令都无法执行

### 可能原因
1. **系统资源限制过严**（ulimit）
2. **实际可用内存不足**（虽然显示正常）
3. **PM2 安装损坏**
4. **Node.js 环境问题**

---

## ✅ 解决方案

### 方案 1: 检查并修复系统资源限制

```bash
# 1. 检查当前限制
ulimit -a

# 2. 临时增加限制（当前会话）
ulimit -v unlimited  # 虚拟内存
ulimit -m unlimited  # 物理内存
ulimit -s 8192       # 栈大小

# 3. 尝试执行 PM2
pm2 --version
```

### 方案 2: 重新安装 PM2

```bash
# 1. 卸载 PM2
npm uninstall -g pm2

# 2. 清理缓存
npm cache clean --force

# 3. 重新安装
sudo npm install -g pm2

# 4. 验证安装
pm2 --version
```

### 方案 3: 使用 systemd 代替 PM2（推荐）

如果 PM2 一直有问题，可以使用 systemd 直接管理服务：

#### 创建后端服务

```bash
# 创建 systemd 服务文件
sudo nano /etc/systemd/system/telegram-backend.service
```

内容：

```ini
[Unit]
Description=Telegram AI Backend Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram-ai-system/admin-backend
Environment="PATH=/home/ubuntu/telegram-ai-system/admin-backend/venv/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 创建前端服务

```bash
sudo nano /etc/systemd/system/telegram-frontend.service
```

内容：

```ini
[Unit]
Description=Telegram AI Frontend Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram-ai-system/saas-demo
Environment="PATH=/usr/bin:/bin"
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 启动服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl enable telegram-backend
sudo systemctl enable telegram-frontend
sudo systemctl start telegram-backend
sudo systemctl start telegram-frontend

# 检查状态
sudo systemctl status telegram-backend
sudo systemctl status telegram-frontend
```

### 方案 4: 检查并修复内存问题

```bash
# 1. 检查实际内存使用
free -h

# 2. 检查哪些进程占用内存
ps aux --sort=-%mem | head -n 10

# 3. 如果内存不足，增加 Swap
swapon --show
# 如果 Swap 未启用或不足，增加：
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 4. 重启系统
sudo reboot
```

### 方案 5: 使用 nohup 直接运行（临时方案）

如果 PM2 无法使用，可以临时使用 nohup：

```bash
# 启动后端
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# 启动前端
cd /home/ubuntu/telegram-ai-system/saas-demo
nohup npm start > frontend.log 2>&1 &

# 检查进程
ps aux | grep -E "uvicorn|node"
```

---

## 🔧 详细排查步骤

### 步骤 1: 运行诊断脚本

```bash
cd /home/ubuntu/telegram-ai-system
git pull origin main
bash scripts/server/diagnose_killed_issue.sh
```

### 步骤 2: 检查系统日志

```bash
# 查看 OOM 日志
sudo dmesg | grep -i "killed\|oom" | tail -n 20

# 查看系统日志
sudo journalctl -n 50 | grep -i "killed\|oom"
```

### 步骤 3: 检查资源限制

```bash
# 查看当前限制
ulimit -a

# 查看进程限制
cat /proc/self/limits
```

### 步骤 4: 尝试简单命令

```bash
# 测试 Node.js
node --version

# 测试 npm
npm --version

# 测试 PM2（如果失败，说明问题在 PM2）
pm2 --version
```

---

## 🎯 推荐解决方案

### 如果 PM2 一直有问题

**使用 systemd 代替 PM2**（最可靠）：

1. 创建 systemd 服务文件（见上面的方案 3）
2. 启动服务
3. 管理服务使用 `systemctl` 而不是 `pm2`

### 如果只是临时问题

1. 重启服务器
2. 重新安装 PM2
3. 检查资源限制

---

## 📋 快速修复命令

### 尝试修复 PM2

```bash
# 1. 检查 PM2
which pm2
pm2 --version

# 2. 如果失败，重新安装
sudo npm uninstall -g pm2
sudo npm install -g pm2

# 3. 测试
pm2 --version
```

### 如果 PM2 无法修复，使用 systemd

```bash
# 创建服务文件（使用上面的内容）
# 然后启动
sudo systemctl daemon-reload
sudo systemctl enable telegram-backend telegram-frontend
sudo systemctl start telegram-backend telegram-frontend
```

---

## 🐛 常见问题

### 问题 1: PM2 命令全部被杀死

**原因**: 系统资源限制或内存不足

**解决方案**: 
- 检查 `ulimit -a`
- 增加资源限制
- 或使用 systemd 代替

### 问题 2: 重新安装 PM2 后仍然被杀死

**原因**: 系统级别的问题

**解决方案**: 
- 使用 systemd 管理服务
- 或检查系统配置

### 问题 3: systemd 服务也无法启动

**原因**: 权限或配置问题

**解决方案**:
```bash
# 检查服务日志
sudo journalctl -u telegram-backend -n 50
sudo journalctl -u telegram-frontend -n 50

# 检查权限
ls -la /home/ubuntu/telegram-ai-system
```

---

**最后更新**: 2025-12-09

