# 管理后台系统端口与配置修复方案

**基于**: `ADMIN_SYSTEM_PORT_MAPPING_ANALYSIS.md`  
**目标**: 解决端口冲突、配置不一致问题

---

## 🎯 修复目标

1. ✅ 解决 `admin-frontend` 和 `ai-monitor-frontend` 的端口冲突（3006）
2. ✅ 统一 Nginx 配置与实际端口映射
3. ✅ 更新相关文档和脚本
4. ✅ 确保所有服务可以正常运行

---

## 📝 修复方案详情

### 方案选择：方案 A - 重新分配端口

**理由**:
- 最小化对现有配置的影响
- 保持 `sites-admin-frontend` (3007) 和 `ai-monitor-frontend` (3006) 不变
- 仅调整 `admin-frontend` 到新端口 3008

---

## 🔧 需要修改的文件清单

### 1. 部署脚本

| 文件 | 修改内容 | 原值 | 新值 |
|------|---------|------|------|
| `scripts/deploy_admin_frontend.sh` | 端口配置 | `PORT=3006` | `PORT=3008` |
| `scripts/deploy_admin_frontend.sh` | PM2 名称检查 | - | 保持不变 |
| `scripts/check_admin_frontend.sh` | 端口检查 | `:3006` | `:3008` |
| `scripts/verify_admin_frontend.sh` | 端口检查 | `:3006` | `:3008` |

### 2. 文档文件

| 文件 | 修改内容 | 原值 | 新值 |
|------|---------|------|------|
| `docs/ADMIN_FRONTEND_DEPLOYMENT.md` | 端口说明 | `3006` | `3008` |
| `docs/ADMIN_FRONTEND_DEPLOYMENT.md` | 访问地址 | `127.0.0.1:3006` | `127.0.0.1:3008` |
| `docs/ADMIN_FRONTEND_DEPLOYMENT.md` | Nginx 配置示例 | `3006` | `3008` |

### 3. Nginx 配置（可选）

**注意**: 如果 `admin-frontend` 需要通过 Nginx 访问，需要添加配置

```nginx
# 如果需要在 aiadmin.usdt2026.cc 下添加 admin-frontend 路由
location /admin-frontend {
    proxy_pass http://127.0.0.1:3008;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    rewrite ^/admin-frontend/?(.*) /$1 break;
}
```

---

## 🚀 执行步骤

### 步骤 1: 备份当前配置

```bash
# 备份相关脚本
cd /home/ubuntu/telegram-ai-system
cp scripts/deploy_admin_frontend.sh scripts/deploy_admin_frontend.sh.backup
cp docs/ADMIN_FRONTEND_DEPLOYMENT.md docs/ADMIN_FRONTEND_DEPLOYMENT.md.backup
```

### 步骤 2: 修改部署脚本

执行脚本修改（见下方脚本）

### 步骤 3: 更新文档

执行文档更新（见下方脚本）

### 步骤 4: 验证修改

```bash
# 检查端口引用
grep -r "3006.*admin-frontend\|admin-frontend.*3006" scripts/ docs/

# 应该没有结果（除了备份文件和此文档）

# 检查新端口引用
grep -r "3008.*admin-frontend\|admin-frontend.*3008" scripts/ docs/
```

### 步骤 5: 如果服务正在运行，重启服务

```bash
# 停止旧服务（如果使用 3006）
pm2 delete admin-frontend 2>/dev/null || true

# 使用新端口重新部署
bash scripts/deploy_admin_frontend.sh
```

---

## ✅ 验证清单

修复完成后，验证以下内容：

- [ ] `scripts/deploy_admin_frontend.sh` 使用端口 3008
- [ ] `scripts/check_admin_frontend.sh` 检查端口 3008
- [ ] `scripts/verify_admin_frontend.sh` 检查端口 3008
- [ ] `docs/ADMIN_FRONTEND_DEPLOYMENT.md` 文档更新为 3008
- [ ] 没有其他脚本引用 `admin-frontend` 使用 3006
- [ ] `ai-monitor-frontend` 继续使用 3006（无冲突）
- [ ] `sites-admin-frontend` 继续使用 3007（无冲突）

---

## 📋 端口分配最终确认

| 端口 | 服务 | 文件夹 | 状态 |
|------|------|--------|------|
| 3006 | AI 监控系统 | `ai-monitor-frontend/` | ✅ 保持不变 |
| 3007 | 站点管理后台 | `sites-admin-frontend/` | ✅ 保持不变 |
| 3008 | 管理后台前端 | `admin-frontend/` | ✅ 新分配（修复后） |
| 8000 | 后端 API | `admin-backend/` | ✅ 保持不变 |

---

## 🔍 相关服务检查命令

### 检查端口占用

```bash
# 检查 3006
sudo lsof -i :3006 || sudo netstat -tlnp | grep :3006

# 检查 3007
sudo lsof -i :3007 || sudo netstat -tlnp | grep :3007

# 检查 3008（修复后）
sudo lsof -i :3008 || sudo netstat -tlnp | grep :3008
```

### 检查 PM2 进程

```bash
pm2 list | grep -E "admin-frontend|sites-admin-frontend|ai-monitor-frontend"
```

### 检查服务可访问性

```bash
# admin-frontend (修复后应在 3008)
curl -s http://127.0.0.1:3008 | head -20

# sites-admin-frontend (应在 3007)
curl -s http://127.0.0.1:3007 | head -20

# ai-monitor-frontend (应在 3006)
curl -s http://127.0.0.1:3006 | head -20
```

---

**最后更新**: 2025-12-24  
**状态**: 待执行

