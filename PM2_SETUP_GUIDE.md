# PM2 Zero-Downtime Deployment Setup Guide

## 📋 概述

本指南说明如何在服务器上设置 PM2 来管理后端和前端服务，实现零停机部署。

## 📁 文件说明

- `ecosystem.config.js` - PM2 配置文件（根目录）
- `scripts/server/setup-pm2.sh` - 自动化设置脚本

## 🚀 快速设置（推荐）

### 方式 1: 使用自动化脚本

```bash
# 1. SSH 到服务器
ssh ubuntu@165.154.233.55

# 2. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 3. 拉取最新代码
git pull origin main

# 4. 执行设置脚本
bash scripts/server/setup-pm2.sh
```

脚本会自动：
- ✅ 检查并安装 PM2（如果需要）
- ✅ 验证配置文件
- ✅ 检查后端虚拟环境
- ✅ 停止现有进程
- ✅ 启动服务
- ✅ 保存配置
- ✅ 设置开机自启

### 方式 2: 手动设置

```bash
# 1. SSH 到服务器
ssh ubuntu@165.154.233.55

# 2. 进入项目目录
cd /home/ubuntu/telegram-ai-system

# 3. 检查 PM2 是否安装
pm2 -v

# 4. 如果未安装，使用 sudo 安装
sudo npm install -g pm2

# 5. 验证后端虚拟环境
ls -la admin-backend/venv/bin/python

# 6. 如果虚拟环境不存在，创建它
cd admin-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 7. 停止现有进程（如果有）
pm2 stop all
pm2 delete all

# 8. 启动服务
pm2 start ecosystem.config.js

# 9. 保存配置
pm2 save

# 10. 设置开机自启
pm2 startup
# 执行上面命令输出的命令（通常需要 sudo）
```

## 📊 验证服务状态

```bash
# 查看 PM2 状态
pm2 status

# 应该看到类似这样的输出：
# ┌─────┬──────────┬─────────────┬─────────┬─────────┬──────────┐
# │ id  │ name     │ mode        │ ↺       │ status  │ cpu      │
# ├─────┼──────────┼─────────────┼─────────┼─────────┼──────────┤
# │ 0   │ backend  │ fork        │ 0       │ online  │ 0%       │
# │ 1   │ frontend │ fork        │ 0       │ online  │ 0%       │
# └─────┴──────────┴─────────────┴─────────┴─────────┴──────────┘
```

## 📝 常用命令

### 查看日志

```bash
# 查看所有日志
pm2 logs

# 查看后端日志
pm2 logs backend

# 查看前端日志
pm2 logs frontend

# 查看最近 100 行日志
pm2 logs --lines 100
```

### 管理进程

```bash
# 重启所有进程
pm2 restart all

# 重启单个进程
pm2 restart backend
pm2 restart frontend

# 停止所有进程
pm2 stop all

# 停止单个进程
pm2 stop backend

# 删除进程
pm2 delete backend

# 重新加载配置（零停机重启）
pm2 reload ecosystem.config.js
```

### 监控

```bash
# 实时监控
pm2 monit

# 查看详细信息
pm2 describe backend
pm2 describe frontend

# 查看进程信息
pm2 info backend
```

## 🔧 配置文件说明

`ecosystem.config.js` 配置了两个应用：

### Backend (后端)
- **名称**: `backend`
- **工作目录**: `./admin-backend`
- **脚本**: `main.py`
- **解释器**: `./venv/bin/python`
- **端口**: 8000
- **日志**: `./logs/backend-*.log`

### Frontend (前端)
- **名称**: `frontend`
- **工作目录**: `./saas-demo`
- **脚本**: `npm start`
- **端口**: 3000
- **日志**: `./logs/frontend-*.log`

## 🛠️ 故障排除

### PM2 未安装

```bash
sudo npm install -g pm2
pm2 -v  # 验证安装
```

### 虚拟环境不存在

```bash
cd admin-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 端口被占用

```bash
# 检查端口占用
sudo lsof -i :8000  # 后端
sudo lsof -i :3000  # 前端

# 或使用 netstat
netstat -tulpn | grep :8000
```

### 进程启动失败

```bash
# 查看详细错误日志
pm2 logs backend --err
pm2 logs frontend --err

# 查看进程信息
pm2 describe backend
pm2 describe frontend
```

### 权限问题

```bash
# 确保日志目录存在且有写权限
mkdir -p logs
chmod 755 logs
```

## 🔄 零停机部署流程

1. **拉取最新代码**
   ```bash
   cd /home/ubuntu/telegram-ai-system
   git pull origin main
   ```

2. **更新依赖（如果需要）**
   ```bash
   # 后端
   cd admin-backend
   source venv/bin/activate
   pip install -r requirements.txt
   
   # 前端
   cd ../saas-demo
   npm install
   ```

3. **重新加载服务（零停机）**
   ```bash
   cd /home/ubuntu/telegram-ai-system
   pm2 reload ecosystem.config.js
   ```

   或者分别重新加载：
   ```bash
   pm2 reload backend
   pm2 reload frontend
   ```

4. **验证服务状态**
   ```bash
   pm2 status
   curl http://localhost:8000/health  # 后端健康检查
   curl http://localhost:3000          # 前端健康检查
   ```

## 📌 注意事项

1. **PM2 必须使用 sudo 安装**（全局安装）
2. **虚拟环境路径**必须是 `./venv/bin/python`（相对于 `admin-backend` 目录）
3. **日志目录**会自动创建在项目根目录的 `logs/` 文件夹
4. **端口配置**在 `ecosystem.config.js` 中，确保不与现有服务冲突
5. **开机自启**需要执行 `pm2 startup` 输出的命令（通常需要 sudo）

## ✅ 验证清单

- [ ] PM2 已安装 (`pm2 -v`)
- [ ] 后端虚拟环境存在 (`admin-backend/venv/bin/python`)
- [ ] 前端 node_modules 存在 (`saas-demo/node_modules`)
- [ ] 配置文件存在 (`ecosystem.config.js`)
- [ ] 服务已启动 (`pm2 status` 显示 online)
- [ ] 配置已保存 (`pm2 save`)
- [ ] 开机自启已设置 (`pm2 startup`)
- [ ] 后端健康检查通过 (`curl http://localhost:8000/health`)
- [ ] 前端可访问 (`curl http://localhost:3000`)

---

**最后更新**: 2025-12-07

