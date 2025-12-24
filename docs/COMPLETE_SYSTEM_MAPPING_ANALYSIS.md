# 完整系统映射关系分析

**生成时间**: 2025-12-24  
**目的**: 全面分析所有网站、文件夹、端口、域名的对应关系，找出错误和不一致之处

---

## 📋 完整映射关系表

### 1. 展示网站（独立域名）

| 网站名称 | 域名 | 文件夹 | 端口 | PM2进程名 | Nginx配置文件 | 状态 | 说明 |
|---------|------|--------|------|----------|--------------|------|------|
| TON Mini App Studio | `tgmini.usdt2026.cc` | `tgmini20251220/` | **3001** | `tgmini-frontend` | `/etc/nginx/sites-available/tgmini.usdt2026.cc` | ✅ 正常 | 营销展示网站 |
| RedEnvelope.fi | `hongbao.usdt2026.cc` | `hbwy20251220/` | **3002** | `hongbao-frontend` | `/etc/nginx/sites-available/hongbao.usdt2026.cc` | ✅ 正常 | 营销展示网站 |
| Smart Control King | `aizkw.usdt2026.cc` | `aizkw20251219/` | **3003** | `aizkw-frontend` | `/etc/nginx/sites-available/aizkw.usdt2026.cc` | ✅ 正常 | AI 智控王营销网站 |
| 聊天AI后台 | `aikz.usdt2026.cc` | `saas-demo/` | **3000** | `next-server` / `saas-demo` | `/etc/nginx/sites-available/aikz.usdt2026.cc` | ⚠️ **有冲突** | 主应用前端 |

---

### 2. 管理后台系统（统一域名：aiadmin.usdt2026.cc）

| 服务名称 | 文件夹 | 端口 | PM2进程名 | Nginx路径 | 状态 | 说明 |
|---------|--------|------|----------|----------|------|------|
| 后端 API | `admin-backend/` | **8000** | `backend` / `luckyred-api` | `/api/` | ✅ 正常 | FastAPI 后端服务 |
| 站点管理后台 | `sites-admin-frontend/` | **3007** | `sites-admin-frontend` | `/admin` | ✅ 正常 | 三个展示网站的管理后台 |
| AI 监控系统 | `ai-monitor-frontend/` | **3006** | `ai-monitor-frontend` | `/ai-monitor` | ✅ 正常 | AI 使用监控和分析 |
| 管理后台前端 | `admin-frontend/` | **3006→3008** | `admin-frontend` | (未配置) | ⚠️ **端口冲突已修复** | 用途不明确 |

**Nginx 配置文件**: `/etc/nginx/sites-available/aiadmin.usdt2026.cc`

---

## ⚠️ 发现的问题和错误

### 问题 1: aikz.usdt2026.cc 端口配置冲突 ⚠️ **严重**

**错误描述**:
- 文档 `docs/FIX_AIKZ_DOMAIN.md` 明确说明：`aikz.usdt2026.cc` 应该指向端口 **3000**（saas-demo）
- 但脚本 `scripts/server/quick_fix_backend_and_aikz.sh` 中配置为端口 **3003**
- 脚本 `scripts/server/fix_nginx_final.sh` 中也错误地配置为端口 **3003**

**正确配置应该是**:
- `aikz.usdt2026.cc` → 端口 **3000** → `saas-demo/`

**错误配置位置**:
1. `scripts/server/quick_fix_backend_and_aikz.sh` 第 129 行和第 148 行：`proxy_pass http://127.0.0.1:3003;`
2. `scripts/server/fix_nginx_final.sh` 第 21 行：`["aikz.usdt2026.cc"]="3003"`

---

### 问题 2: admin-frontend 端口已修复但文档未更新 ⚠️ **中等**

**当前状态**:
- 我们之前已经将 `admin-frontend` 端口从 3006 改为 3008
- 但 `scripts/deploy_admin_frontend.sh` 仍然使用 **3006**（需要修复）
- `docs/ADMIN_FRONTEND_DEPLOYMENT.md` 文档可能仍然显示 3006

**需要确认**:
- `scripts/deploy_admin_frontend.sh` 是否已更新为 3008？
- `docs/ADMIN_FRONTEND_DEPLOYMENT.md` 是否已更新？

---

### 问题 3: 配置文件路径不一致 ⚠️ **轻微**

**问题**:
- `docs/DEPLOY_THREE_SITES.md` 第 81 行提到：`/etc/nginx/sites-available/aikz.usdt2026.cc`
- 但正确的应该是 `aizkw.usdt2026.cc` 指向 `aizkw20251219/`（端口 3003）
- `aikz.usdt2026.cc` 应该指向 `saas-demo/`（端口 3000）

**注意**: `aikz` 和 `aizkw` 是两个不同的域名！

---

### 问题 4: deploy_full.sh 中端口 3005 的使用 ⚠️ **需要确认**

**发现**:
- `scripts/deploy_full.sh` 第 475 行使用 `PORT=3005`
- `scripts/server/setup_nginx.sh` 第 69 行也配置了端口 3005
- 但在我们的映射表中没有 3005 的用途

**需要确认**: 端口 3005 的用途是什么？是否是临时配置？

---

## ✅ 正确的映射关系（标准）

### 展示网站映射

```
tgmini.usdt2026.cc    → 端口 3001 → tgmini20251220/   → TON Mini App Studio
hongbao.usdt2026.cc   → 端口 3002 → hbwy20251220/     → RedEnvelope.fi
aizkw.usdt2026.cc     → 端口 3003 → aizkw20251219/    → Smart Control King
aikz.usdt2026.cc      → 端口 3000 → saas-demo/        → 聊天AI后台（主应用）
```

### 管理后台映射（aiadmin.usdt2026.cc）

```
/api/          → 端口 8000 → admin-backend/           → 后端 API
/admin         → 端口 3007 → sites-admin-frontend/    → 站点管理后台
/ai-monitor    → 端口 3006 → ai-monitor-frontend/     → AI 监控系统
(未配置)       → 端口 3008 → admin-frontend/          → 管理后台前端（用途待确认）
```

---

## 📊 端口使用总览

| 端口 | 服务 | 文件夹 | 域名/路径 | 状态 |
|------|------|--------|----------|------|
| 3000 | 聊天AI后台 | `saas-demo/` | `aikz.usdt2026.cc` | ✅ 正常 |
| 3001 | TON Mini App | `tgmini20251220/` | `tgmini.usdt2026.cc` | ✅ 正常 |
| 3002 | RedEnvelope | `hbwy20251220/` | `hongbao.usdt2026.cc` | ✅ 正常 |
| 3003 | Smart Control King | `aizkw20251219/` | `aizkw.usdt2026.cc` | ✅ 正常 |
| 3005 | (未知用途) | ? | ? | ⚠️ 需要确认 |
| 3006 | AI 监控系统 | `ai-monitor-frontend/` | `aiadmin.usdt2026.cc/ai-monitor` | ✅ 正常 |
| 3007 | 站点管理后台 | `sites-admin-frontend/` | `aiadmin.usdt2026.cc/admin` | ✅ 正常 |
| 3008 | 管理后台前端 | `admin-frontend/` | (未配置) | ✅ 已修复 |
| 8000 | 后端 API | `admin-backend/` | `aiadmin.usdt2026.cc/api/` | ✅ 正常 |

---

## 🔍 需要修复的错误清单

### 错误 1: quick_fix_backend_and_aikz.sh 端口错误

**文件**: `scripts/server/quick_fix_backend_and_aikz.sh`  
**位置**: 第 129 行、第 148 行  
**错误**: `proxy_pass http://127.0.0.1:3003;`  
**应该**: `proxy_pass http://127.0.0.1:3000;`

---

### 错误 2: fix_nginx_final.sh 端口映射错误

**文件**: `scripts/server/fix_nginx_final.sh`  
**位置**: 第 21 行  
**错误**: `["aikz.usdt2026.cc"]="3003"`  
**应该**: `["aikz.usdt2026.cc"]="3000"`

---

### 错误 3: deploy_admin_frontend.sh 端口未更新

**文件**: `scripts/deploy_admin_frontend.sh`  
**位置**: 第 60 行  
**当前**: `export PORT=3006`  
**应该**: `export PORT=3008`（如果我们的修复方案生效）

---

### 错误 4: DEPLOY_THREE_SITES.md 文档路径混淆

**文件**: `docs/DEPLOY_THREE_SITES.md`  
**位置**: 第 81 行  
**问题**: 提到 `/etc/nginx/sites-available/aikz.usdt2026.cc` 作为三个网站之一  
**应该**: 澄清 `aikz.usdt2026.cc` 是主应用，不是三个展示网站之一

---

## 📝 域名命名说明

**重要区分**:
- `aikz.usdt2026.cc` - 主聊天AI后台（端口 3000，saas-demo）
- `aizkw.usdt2026.cc` - AI 智控王营销网站（端口 3003，aizkw20251219）

这两个是不同的域名，不要混淆！

---

## ✅ 验证正确的映射关系

### 正确的完整映射表

| 域名 | 完整URL | 端口 | 文件夹 | 服务/功能 |
|------|---------|------|--------|----------|
| `tgmini.usdt2026.cc` | `https://tgmini.usdt2026.cc/` | 3001 | `tgmini20251220/` | TON Mini App Studio |
| `hongbao.usdt2026.cc` | `https://hongbao.usdt2026.cc/` | 3002 | `hbwy20251220/` | RedEnvelope.fi |
| `aizkw.usdt2026.cc` | `https://aizkw.usdt2026.cc/` | 3003 | `aizkw20251219/` | Smart Control King |
| `aikz.usdt2026.cc` | `https://aikz.usdt2026.cc/` | 3000 | `saas-demo/` | 聊天AI后台（主应用） |
| `aiadmin.usdt2026.cc` | `https://aiadmin.usdt2026.cc/api/` | 8000 | `admin-backend/` | 后端 API |
| `aiadmin.usdt2026.cc` | `https://aiadmin.usdt2026.cc/admin` | 3007 | `sites-admin-frontend/` | 站点管理后台 |
| `aiadmin.usdt2026.cc` | `https://aiadmin.usdt2026.cc/ai-monitor` | 3006 | `ai-monitor-frontend/` | AI 监控系统 |

---

**最后更新**: 2025-12-24  
**状态**: 待修复确认

