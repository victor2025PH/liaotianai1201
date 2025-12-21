# 三个网站部署总结

> **完成时间**: 2025-12-21  
> **状态**: ✅ 部署配置已创建

---

## 📋 网站信息

| 网站 | 域名 | 本地目录 | 端口 | PM2 名称 |
|------|------|---------|------|---------|
| TON Mini App Studio | https://tgmini.usdt2026.cc | `tgmini20251220/` | 3001 | `tgmini-frontend` |
| RedEnvelope.fi | https://hongbao.usdt2026.cc | `hbwy20251220/` | 3002 | `hongbao-frontend` |
| Smart Control King | https://aikz.usdt2026.cc | `aizkw20251219/` | 3003 | `aizkw-frontend` |

---

## ✅ 已完成的配置

### 1. GitHub Actions 工作流 ✅

**文件**: `.github/workflows/deploy-three-sites.yml`

**功能**:
- 自动检测三个网站目录的变更
- 并行部署三个网站
- 每个网站使用独立端口
- 自动配置 Nginx 反向代理
- 使用 PM2 管理进程

**触发条件**:
- `tgmini20251220/**` 文件变更
- `hbwy20251220/**` 文件变更
- `aizkw20251219/**` 文件变更
- 手动触发 (workflow_dispatch)

### 2. 部署文档 ✅

**文件**: `docs/DEPLOY_THREE_SITES.md`

包含:
- 项目结构说明
- 部署流程详解
- 服务器配置说明
- 故障排查指南

### 3. 部署检查脚本 ✅

**文件**: `scripts/prepare-three-sites-deploy.sh`

功能:
- 检查三个网站目录是否存在
- 检查 `package.json` 和配置文件
- 检查 `.env.local` 文件状态
- 验证 GitHub Actions 工作流

---

## 🚀 部署步骤

### 步骤 1: 检查部署准备

```bash
# 在 Git Bash 中执行
cd d:\telegram-ai-system
bash scripts/prepare-three-sites-deploy.sh
```

### 步骤 2: 提交代码到 GitHub

```powershell
cd d:\telegram-ai-system

# 添加所有更改
git add .

# 提交
git commit -m "feat: 准备部署三个网站"

# 推送到 GitHub
git push origin main
```

### 步骤 3: 自动部署

GitHub Actions 会自动触发部署，或者：

1. 访问 GitHub 仓库
2. 进入 "Actions" 标签
3. 选择 "Deploy Three Sites" 工作流
4. 点击 "Run workflow"

---

## ⚠️ 重要注意事项

### 1. 环境变量文件

每个项目可能包含 `.env.local` 文件，这些文件**不会**被提交到 GitHub。

**需要手动上传**:

```bash
# 上传到服务器（如果文件存在）
scp tgmini20251220/.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/tgmini20251220/.env.local
scp hbwy20251220/.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/hbwy20251220/.env.local
scp aizkw20251219/.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/aizkw20251219/.env.local
```

### 2. SSL 证书

确保每个域名都有有效的 SSL 证书：

```bash
# 在服务器上执行
sudo certbot --nginx -d tgmini.usdt2026.cc
sudo certbot --nginx -d hongbao.usdt2026.cc
sudo certbot --nginx -d aikz.usdt2026.cc
```

### 3. 端口冲突

确保端口 3001, 3002, 3003 未被其他服务占用。

---

## 🔍 验证部署

### 检查服务状态

```bash
# SSH 到服务器
ssh ubuntu@165.154.242.60

# 检查 PM2 进程
pm2 list

# 应该看到:
# - tgmini-frontend (端口 3001)
# - hongbao-frontend (端口 3002)
# - aizkw-frontend (端口 3003)

# 检查端口监听
sudo lsof -i :3001
sudo lsof -i :3002
sudo lsof -i :3003

# 检查 Nginx 状态
sudo systemctl status nginx
sudo nginx -t
```

### 测试网站

```bash
# 测试本地端口
curl http://127.0.0.1:3001
curl http://127.0.0.1:3002
curl http://127.0.0.1:3003

# 测试域名（需要 SSL 证书）
curl https://tgmini.usdt2026.cc
curl https://hongbao.usdt2026.cc
curl https://aikz.usdt2026.cc
```

---

## 📚 相关文档

- [三个网站部署指南](./DEPLOY_THREE_SITES.md)
- [包含 API Key 的文件清单](./FILES_WITH_API_KEYS.md)
- [手动上传 .env 文件指南](./MANUAL_UPLOAD_ENV_FILES.md)

---

## 🎯 下一步

1. ✅ 提交代码到 GitHub
2. ✅ 触发 GitHub Actions 部署
3. ⏳ 验证三个网站是否正常访问
4. ⏳ 上传 `.env.local` 文件（如果存在）
5. ⏳ 配置 SSL 证书（如果未配置）
