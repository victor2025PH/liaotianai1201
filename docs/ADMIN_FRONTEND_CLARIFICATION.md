# admin-frontend 和 sites-admin-frontend 说明

**重要说明**: `admin-frontend/` 和 `sites-admin-frontend/` 是**同一个服务**，用于管理三个展示网站的后台。

---

## ✅ 统一使用 sites-admin-frontend

### 正确的配置

- **文件夹**: `sites-admin-frontend/`
- **端口**: **3007**
- **PM2 进程名**: `sites-admin-frontend`
- **Nginx 路径**: `aiadmin.usdt2026.cc/admin`
- **部署脚本**: `scripts/deploy_sites_admin.sh`

### 不再使用的配置

- ❌ `admin-frontend/` - 已弃用，与 sites-admin-frontend 重复
- ❌ 端口 3006 - 已被 ai-monitor-frontend 使用
- ❌ 端口 3008 - 不再需要

---

## 📋 相关脚本

### 使用这些脚本（正确）

- `scripts/deploy_sites_admin.sh` - 部署站点管理后台
- `scripts/check_sites_admin_port.sh` - 检查端口

### 不再使用（已弃用）

- `scripts/deploy_admin_frontend.sh` - 已弃用，使用 deploy_sites_admin.sh
- `scripts/check_admin_frontend.sh` - 已弃用
- `scripts/verify_admin_frontend.sh` - 已弃用
- `scripts/fix_admin_frontend_port.sh` - 已弃用，不再需要

---

## 🔧 如果需要部署站点管理后台

```bash
# 使用正确的脚本
bash scripts/deploy_sites_admin.sh
```

服务将在端口 **3007** 启动，可以通过 `https://aiadmin.usdt2026.cc/admin` 访问。

---

**最后更新**: 2025-12-24

