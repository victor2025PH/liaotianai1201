# PM2 到 Systemd 迁移指南

> **状态**: PM2 配置已废弃，请使用 Systemd 服务

## 📋 概述

本项目已从 PM2 迁移到 Systemd，原因：
- PM2 在服务器上不稳定（进程被 Killed）
- Systemd 是 Linux 标准服务管理工具，更可靠
- Systemd 提供更好的日志管理和自动重启功能
- 与 Python 环境集成更简单

## 🚀 快速开始

### 1. 部署 Systemd 服务

在服务器上执行：

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/deploy-systemd.sh
```

这个脚本会：
- ✅ 检查虚拟环境
- ✅ 安装 systemd 服务文件
- ✅ 启用服务（开机自启）
- ✅ 启动服务
- ✅ 检查服务状态

### 2. 管理服务

使用管理脚本：

```bash
# 查看服务状态
sudo bash scripts/server/manage-services.sh status all

# 重启所有服务
sudo bash scripts/server/manage-services.sh restart all

# 启动后端
sudo bash scripts/server/manage-services.sh start backend

# 启动 Bot
sudo bash scripts/server/manage-services.sh start bot
```

### 3. 查看日志

```bash
# 查看后端日志（实时跟踪）
bash scripts/server/view-logs.sh backend -f

# 查看 Bot 日志（最后 100 行）
bash scripts/server/view-logs.sh bot -n 100

# 查看所有服务错误日志
bash scripts/server/view-logs.sh all -e

# 查看最近 1 小时的日志
bash scripts/server/view-logs.sh backend -s 1h
```

## 📁 服务文件位置

- **后端服务**: `/etc/systemd/system/telegram-backend.service`
- **Bot 服务**: `/etc/systemd/system/telegram-bot.service`
- **源文件**: `deploy/systemd/telegram-backend.service`, `deploy/systemd/telegram-bot.service`

## 🔧 手动管理服务

### 查看服务状态

```bash
sudo systemctl status telegram-backend
sudo systemctl status telegram-bot
```

### 启动/停止/重启

```bash
sudo systemctl start telegram-backend
sudo systemctl stop telegram-backend
sudo systemctl restart telegram-backend

sudo systemctl start telegram-bot
sudo systemctl stop telegram-bot
sudo systemctl restart telegram-bot
```

### 启用/禁用开机自启

```bash
sudo systemctl enable telegram-backend
sudo systemctl disable telegram-backend

sudo systemctl enable telegram-bot
sudo systemctl disable telegram-bot
```

### 查看日志

```bash
# 查看后端日志
sudo journalctl -u telegram-backend -f

# 查看 Bot 日志
sudo journalctl -u telegram-bot -f

# 查看最近 50 行
sudo journalctl -u telegram-backend -n 50

# 查看错误日志
sudo journalctl -u telegram-backend -p err

# 查看指定时间范围的日志
sudo journalctl -u telegram-backend --since "1 hour ago"
sudo journalctl -u telegram-backend --since "2024-01-01 00:00:00"
```

## 🔄 从 PM2 迁移

### 步骤 1: 停止 PM2 服务

```bash
pm2 stop all
pm2 delete all
```

### 步骤 2: 部署 Systemd 服务

```bash
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/deploy-systemd.sh
```

### 步骤 3: 验证服务运行

```bash
sudo systemctl status telegram-backend
sudo systemctl status telegram-bot
```

### 步骤 4: 检查端口监听

```bash
ss -tlnp | grep :8000  # 后端
ps aux | grep "python.*main.py"  # Bot
```

## ⚠️ 注意事项

1. **虚拟环境路径**: 确保虚拟环境路径正确
   - 后端: `/home/ubuntu/telegram-ai-system/admin-backend/venv`
   - Bot: `/home/ubuntu/telegram-ai-system/venv`

2. **环境变量**: 服务文件会从 `.env` 文件读取环境变量，确保文件存在且配置正确

3. **权限**: 服务以 `ubuntu` 用户运行，确保该用户有足够权限

4. **日志位置**: 日志存储在 systemd journal 中，使用 `journalctl` 查看

## 📝 废弃文件

以下 PM2 相关文件已废弃（保留用于参考）：

- `ecosystem.config.js` - PM2 配置文件
- `docs/PM2_KILLED_SOLUTION.md` - PM2 问题解决方案
- `MANUAL_PM2_SETUP.md` - PM2 手动设置指南
- `PM2_SETUP_GUIDE.md` - PM2 设置指南
- `scripts/server/install-pm2-manual.sh` - PM2 安装脚本
- `scripts/server/setup-pm2.sh` - PM2 设置脚本

## 🆘 故障排查

### 服务无法启动

1. 检查服务状态：
   ```bash
   sudo systemctl status telegram-backend
   ```

2. 查看详细日志：
   ```bash
   sudo journalctl -u telegram-backend -n 100
   ```

3. 检查虚拟环境：
   ```bash
   ls -la /home/ubuntu/telegram-ai-system/admin-backend/venv/bin/python
   ```

4. 手动测试启动：
   ```bash
   cd /home/ubuntu/telegram-ai-system/admin-backend
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### 服务频繁重启

1. 查看错误日志：
   ```bash
   sudo journalctl -u telegram-backend -p err -n 50
   ```

2. 检查资源限制：
   ```bash
   systemctl show telegram-backend | grep -i limit
   ```

3. 检查系统资源：
   ```bash
   free -h
   df -h
   ```

## 📚 相关文档

- [Systemd 服务管理](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Journalctl 日志查看](https://www.freedesktop.org/software/systemd/man/journalctl.html)

