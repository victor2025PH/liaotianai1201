# Systemd 自动化部署

## 📋 快速开始

### 1. 上传文件到服务器

将以下文件上传到服务器：

```
deploy/systemd/
├── auto_deploy.sh              # 自动化部署脚本
├── smart-tg-backend.service    # 后端服务配置
├── smart-tg-frontend.service   # 前端服务配置
└── check_deployment.sh         # 部署状态检查脚本
```

### 2. 在服务器上执行部署

```bash
# 1. 上传文件后，进入目录
cd deploy/systemd

# 2. 给脚本执行权限
chmod +x auto_deploy.sh
chmod +x check_deployment.sh

# 3. 执行自动化部署（需要 root 权限）
sudo ./auto_deploy.sh
```

### 3. 检查部署状态

```bash
# 运行检查脚本
sudo ./check_deployment.sh

# 或手动检查
sudo systemctl status smart-tg-backend
sudo systemctl status smart-tg-frontend
```

---

## 🔧 配置说明

### 修改部署路径

如果您的项目不在 `/opt/smart-tg`，请修改 `auto_deploy.sh` 中的变量：

```bash
PROJECT_ROOT="/opt/smart-tg"  # 改为您的实际路径
BACKEND_DIR="$PROJECT_ROOT/admin-backend"
FRONTEND_DIR="$PROJECT_ROOT/saas-demo"
SERVICE_USER="www-data"  # 改为您的实际用户
```

### 环境变量配置

部署前请确保：

1. **后端 `.env` 文件** (`$BACKEND_DIR/.env`):
   ```bash
   DATABASE_URL=postgresql://user:password@localhost/dbname
   JWT_SECRET=your-strong-secret-key
   CORS_ORIGINS=https://yourdomain.com
   ```

2. **前端 `.env.local` 文件** (`$FRONTEND_DIR/.env.local`):
   ```bash
   NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com/api/v1
   ```

---

## 📝 部署流程

自动化脚本会执行以下步骤：

1. ✅ 检查当前部署状态
2. ✅ 检查目录结构
3. ✅ 检查后端环境（虚拟环境、依赖）
4. ✅ 检查前端环境（node_modules、构建）
5. ✅ 创建 systemd 服务文件
6. ✅ 设置权限
7. ✅ 初始化数据库
8. ✅ 启动服务

---

## 🐛 故障排查

### 服务启动失败

```bash
# 查看详细日志
sudo journalctl -u smart-tg-backend -n 50 --no-pager
sudo journalctl -u smart-tg-frontend -n 50 --no-pager

# 检查权限
ls -la /opt/smart-tg/
sudo chown -R www-data:www-data /opt/smart-tg
```

### 端口被占用

```bash
# 查看端口占用
sudo netstat -tlnp | grep -E ":8000|:3000"

# 杀死占用进程
sudo kill -9 <PID>
```

### 手动测试启动

```bash
# 后端
cd /opt/smart-tg/admin-backend
source .venv/bin/activate
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 前端
cd /opt/smart-tg/saas-demo
npm start
```

---

## 📚 相关文档

- `部署指南.md` - 详细部署步骤
- `部署状态检查.md` - 检查清单
- `check_deployment.sh` - 自动检查脚本

---

*最后更新: 2025-11-26*

