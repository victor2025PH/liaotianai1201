# 管理后台系统端口与文件夹关系分析

**生成时间**: 2025-12-24  
**分析范围**: 文件夹、端口、网站、Nginx 配置关系

---

## 📊 当前配置关系总览

### 1. 文件夹与服务映射

| 文件夹 | 服务名称 | 当前端口 | PM2 名称 | 用途 | 状态 |
|--------|---------|---------|---------|------|------|
| `admin-backend/` | 后端 API | **8000** | `backend` / `luckyred-api` | FastAPI 后端服务 | ✅ 正常 |
| `admin-frontend/` | 管理后台前端 | **3006** | `admin-frontend` | Next.js 应用 | ⚠️ 端口冲突 |
| `sites-admin-frontend/` | 站点管理后台 | **3007** | `sites-admin-frontend` | 三个展示网站管理后台 | ✅ 正常 |
| `ai-monitor-frontend/` | AI 监控系统 | **3006** | `ai-monitor-frontend` | AI 监控前端 | ⚠️ 端口冲突 |
| `saas-demo/` | SaaS 演示 | **3000** | `next-server` | 主前端应用 | ✅ 正常 |

### 2. 域名与 Nginx 配置

**域名**: `aiadmin.usdt2026.cc`

| Nginx 路径 | 代理目标端口 | 对应服务 | 备注 |
|-----------|-------------|---------|------|
| `/api/` | **8000** | `admin-backend` | 后端 API |
| `/admin` | **3007** | `sites-admin-frontend` | 站点管理后台 |
| `/ai-monitor` | **3006** | `ai-monitor-frontend` | AI 监控系统 |

### 3. 其他域名配置

| 域名 | 路径 | 端口 | 文件夹 | 服务 |
|------|------|------|--------|------|
| `aikz.usdt2026.cc` | `/` | 3000/3005 | `saas-demo` | SaaS 前端 |
| `tgmini.usdt2026.cc` | `/` | 3001 | `tgmini20251220/` | TON Mini App |
| `hongbao.usdt2026.cc` | `/` | 3002 | `hbwy20251220/` | RedEnvelope |
| `aizkw.usdt2026.cc` | `/` | 3003 | `aizkw20251219/` | Smart Control King |

---

## ⚠️ 发现的问题

### 问题 1: 端口冲突

**冲突详情**:
- `admin-frontend/` 使用端口 **3006**（根据 `deploy_admin_frontend.sh`）
- `ai-monitor-frontend/` 也使用端口 **3006**（根据 `deploy_ai_monitor.sh`）

**影响**:
- 两个服务无法同时运行
- 文档 `ADMIN_FRONTEND_DEPLOYMENT.md` 显示 `admin-frontend` 使用 3006，但实际 Nginx 配置中 `/admin` 指向 3007

### 问题 2: 文档与配置不一致

**不一致点**:
1. `docs/ADMIN_FRONTEND_DEPLOYMENT.md` 提到 `admin-frontend` 使用 3006，但 Nginx 配置中 `/admin` 指向 3007
2. `admin-frontend` 的实际用途不明确

### 问题 3: 文件夹缺失

- 代码库中**未找到** `ai-monitor-frontend/` 文件夹
- 但部署脚本 `deploy_ai_monitor.sh` 引用此文件夹
- 可能导致部署失败

---

## 🔍 详细分析

### Nginx 配置文件分析

**文件位置**: `/etc/nginx/sites-available/aiadmin.usdt2026.cc`

**当前配置逻辑**:
```nginx
# 后端 API
location /api/ {
    proxy_pass http://127.0.0.1:8000;  # admin-backend
}

# AI 监控系统前端
location /ai-monitor {
    proxy_pass http://127.0.0.1:3006;  # ai-monitor-frontend
    rewrite ^/ai-monitor/?(.*) /$1 break;
}

# 站点管理后台前端
location /admin {
    proxy_pass http://127.0.0.1:3007;  # sites-admin-frontend
    rewrite ^/admin/?(.*) /$1 break;
}
```

**结论**: 
- Nginx 配置期望 `/admin` → 3007（sites-admin-frontend）
- Nginx 配置期望 `/ai-monitor` → 3006（ai-monitor-frontend）

### 部署脚本分析

#### `scripts/deploy_admin_frontend.sh`
- 文件夹: `admin-frontend/`
- 端口: **3006**
- PM2 名称: `admin-frontend`
- **与 ai-monitor-frontend 冲突**

#### `scripts/deploy_sites_admin.sh`
- 文件夹: `sites-admin-frontend/`
- 端口: **3007**
- PM2 名称: `sites-admin-frontend`
- **与 Nginx 配置 `/admin` 匹配**

#### `scripts/deploy_ai_monitor.sh`
- 文件夹: `ai-monitor-frontend/`（**不存在**）
- 端口: **3006**
- PM2 名称: `ai-monitor-frontend`
- **与 admin-frontend 冲突，且文件夹缺失**

---

## 💡 推荐的解决方案

### 方案 A: 重新分配端口（推荐）

**端口分配方案**:

| 服务 | 新端口 | 理由 |
|------|--------|------|
| `admin-frontend/` | **3008** | 避免冲突，保留 3006/3007 给现有服务 |
| `ai-monitor-frontend/` | **3006** | 保持不变，与 Nginx 配置一致 |
| `sites-admin-frontend/` | **3007** | 保持不变，与 Nginx 配置一致 |

**需要修改的文件**:
1. `scripts/deploy_admin_frontend.sh` - 修改端口为 3008
2. `docs/ADMIN_FRONTEND_DEPLOYMENT.md` - 更新文档
3. 如果将来需要在 Nginx 中添加 `admin-frontend` 路由，添加配置

### 方案 B: 合并或重命名服务

**选项 1**: 确认 `admin-frontend` 是否还需要
- 如果不需要，删除相关脚本和文档
- 如果需要，明确其用途并重新配置

**选项 2**: 确认 `ai-monitor-frontend` 文件夹是否存在
- 如果不存在，需要创建或找到正确的文件夹
- 如果已合并到其他项目，更新脚本引用

### 方案 C: 统一管理（长期方案）

**建议结构**:
```
admin-frontend/          → 端口 3008 (如果需要独立部署)
sites-admin-frontend/    → 端口 3007 (/admin)
ai-monitor-frontend/     → 端口 3006 (/ai-monitor)
```

**Nginx 配置统一管理**:
- 所有管理相关服务统一在 `aiadmin.usdt2026.cc` 下
- 路径清晰区分不同功能模块

---

## 📋 需要执行的修改步骤

### 步骤 1: 确认服务用途

1. 确认 `admin-frontend/` 的实际用途
2. 确认 `ai-monitor-frontend/` 文件夹是否存在或位置
3. 确认 `sites-admin-frontend/` 是否正确对应三个展示网站管理后台

### 步骤 2: 修复端口冲突

**如果采用方案 A**:

```bash
# 1. 修改 deploy_admin_frontend.sh
sed -i 's/PORT=3006/PORT=3008/g' scripts/deploy_admin_frontend.sh

# 2. 更新相关文档
# 编辑 docs/ADMIN_FRONTEND_DEPLOYMENT.md，将 3006 改为 3008

# 3. 检查并更新其他引用
grep -r "3006.*admin-frontend\|admin-frontend.*3006" scripts/ docs/
```

### 步骤 3: 验证 Nginx 配置

确保 Nginx 配置与实际端口一致：

```bash
# 验证配置
bash scripts/verify_admin_nginx.sh

# 如果配置不正确，重新配置
bash scripts/configure_admin_nginx.sh
```

### 步骤 4: 创建缺失的文件夹（如需要）

如果 `ai-monitor-frontend/` 确实需要，需要：
1. 创建文件夹
2. 初始化项目
3. 配置部署脚本

---

## 🔄 推荐的最终配置

### 端口分配表（推荐）

| 端口 | 服务 | 文件夹 | Nginx 路径 | PM2 名称 |
|------|------|--------|-----------|---------|
| 3000 | SaaS Demo | `saas-demo/` | `/` (aikz.usdt2026.cc) | `next-server` |
| 3001 | TON Mini App | `tgmini20251220/` | `/` (tgmini.usdt2026.cc) | `tgmini-frontend` |
| 3002 | RedEnvelope | `hbwy20251220/` | `/` (hongbao.usdt2026.cc) | `hongbao-frontend` |
| 3003 | Smart Control King | `aizkw20251219/` | `/` (aizkw.usdt2026.cc) | `aizkw-frontend` |
| 3006 | AI 监控系统 | `ai-monitor-frontend/` | `/ai-monitor` | `ai-monitor-frontend` |
| 3007 | 站点管理后台 | `sites-admin-frontend/` | `/admin` | `sites-admin-frontend` |
| 3008 | 管理后台前端 | `admin-frontend/` | (待定或移除) | `admin-frontend` |
| 8000 | 后端 API | `admin-backend/` | `/api/` | `backend` / `luckyred-api` |

### Nginx 配置结构（推荐）

```nginx
# aiadmin.usdt2026.cc
server {
    listen 443 ssl http2;
    server_name aiadmin.usdt2026.cc;

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }

    # AI 监控系统 (端口 3006)
    location /ai-monitor {
        proxy_pass http://127.0.0.1:3006;
        rewrite ^/ai-monitor/?(.*) /$1 break;
    }

    # 站点管理后台 (端口 3007)
    location /admin {
        proxy_pass http://127.0.0.1:3007;
        rewrite ^/admin/?(.*) /$1 break;
    }
}
```

---

## ✅ 检查清单

执行修改前，请确认：

- [ ] `admin-frontend/` 的实际用途和是否需要独立部署
- [ ] `ai-monitor-frontend/` 文件夹是否存在
- [ ] `sites-admin-frontend/` 是否对应三个展示网站管理后台
- [ ] Nginx 配置是否与实际端口匹配
- [ ] 所有部署脚本是否使用正确的端口
- [ ] 文档是否与实际配置一致

---

**最后更新**: 2025-12-24  
**维护者**: System Analysis

