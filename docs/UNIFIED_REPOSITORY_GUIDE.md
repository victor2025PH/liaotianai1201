# 统一仓库管理指南

> **仓库**: https://github.com/victor2025PH/liaotianai1201  
> **状态**: ✅ 三个网站已统一管理

---

## 📋 统一管理的网站

| 网站 | 域名 | 本地目录 | 状态 |
|------|------|---------|------|
| TON Mini App Studio | https://tgmini.usdt2026.cc | `tgmini20251220/` | ✅ 已添加 |
| RedEnvelope.fi | https://hongbao.usdt2026.cc | `hbwy20251220/` | ✅ 已添加 |
| Smart Control King | https://aikz.usdt2026.cc | `aizkw20251219/` | ✅ 已添加 |

---

## ✅ 已完成的配置

### 1. GitHub Actions 自动部署 ✅

**工作流文件**: `.github/workflows/deploy-three-sites.yml`

**功能**:
- 自动检测三个网站目录的变更
- 并行部署三个网站
- 每个网站使用独立端口（3001, 3002, 3003）
- 自动配置 Nginx 反向代理
- 使用 PM2 管理进程

**触发条件**:
- `tgmini20251220/**` 文件变更
- `hbwy20251220/**` 文件变更
- `aizkw20251219/**` 文件变更
- 手动触发 (workflow_dispatch)

### 2. 项目结构 ✅

```
telegram-ai-system/
├── tgmini20251220/          # TON Mini App Studio
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   └── dist/                # 构建输出
├── hbwy20251220/            # RedEnvelope.fi
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   └── dist/                # 构建输出
├── aizkw20251219/           # Smart Control King
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   └── dist/                # 构建输出
└── .github/
    └── workflows/
        └── deploy-three-sites.yml
```

### 3. 环境变量保护 ✅

- 所有 `.env.local` 文件已在 `.gitignore` 中
- 需要手动上传到服务器

---

## 🚀 部署流程

### 自动部署（推荐）

1. **提交代码到 GitHub**:
   ```powershell
   git add .
   git commit -m "feat: 更新网站内容"
   git push origin main
   ```

2. **GitHub Actions 自动触发**:
   - 检测到三个网站目录的变更
   - 自动执行部署流程
   - 部署到服务器

### 手动触发部署

1. 访问: https://github.com/victor2025PH/liaotianai1201/actions
2. 选择 "Deploy Three Sites" 工作流
3. 点击 "Run workflow"
4. 选择分支（通常是 `main`）
5. 点击 "Run workflow"

---

## 📝 日常开发流程

### 修改网站内容

```powershell
# 1. 修改代码
# 编辑 tgmini20251220/, hbwy20251220/, 或 aizkw20251219/ 中的文件

# 2. 提交更改
git add tgmini20251220/
git commit -m "feat: 更新 TON Mini App Studio"

# 3. 推送到 GitHub
git push origin main

# 4. GitHub Actions 自动部署
```

### 添加新功能

```powershell
# 1. 创建功能分支（可选）
git checkout -b feature/new-feature

# 2. 开发功能
# ...

# 3. 提交
git add .
git commit -m "feat: 添加新功能"

# 4. 推送到 GitHub
git push origin main

# 5. 自动部署
```

---

## 🔧 服务器配置

### 端口分配

- `tgmini`: 3001
- `hongbao`: 3002
- `aizkw`: 3003

### PM2 进程

```bash
# 查看所有进程
pm2 list

# 应该看到:
# - tgmini-frontend (端口 3001)
# - hongbao-frontend (端口 3002)
# - aizkw-frontend (端口 3003)
```

### Nginx 配置

每个网站有独立的 Nginx 配置：

- `/etc/nginx/sites-available/tgmini.usdt2026.cc`
- `/etc/nginx/sites-available/hongbao.usdt2026.cc`
- `/etc/nginx/sites-available/aikz.usdt2026.cc`

---

## ⚠️ 重要注意事项

### 1. 环境变量文件

**不要提交** `.env.local` 文件到 GitHub！

**手动上传**:
```bash
scp tgmini20251220/.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/tgmini20251220/.env.local
scp hbwy20251220/.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/hbwy20251220/.env.local
scp aizkw20251219/.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/aizkw20251219/.env.local
```

### 2. SSL 证书

确保每个域名都有有效的 SSL 证书：

```bash
sudo certbot --nginx -d tgmini.usdt2026.cc
sudo certbot --nginx -d hongbao.usdt2026.cc
sudo certbot --nginx -d aikz.usdt2026.cc
```

### 3. 构建输出

- 所有项目使用 Vite 构建
- 构建输出目录: `dist/`
- 构建输出**不会**被提交到 Git（在 `.gitignore` 中）

---

## 🔍 验证部署

### 检查 GitHub Actions

1. 访问: https://github.com/victor2025PH/liaotianai1201/actions
2. 查看 "Deploy Three Sites" 工作流状态
3. 检查部署日志

### 检查服务器状态

```bash
# SSH 到服务器
ssh ubuntu@165.154.242.60

# 检查 PM2 进程
pm2 list

# 检查端口监听
sudo lsof -i :3001
sudo lsof -i :3002
sudo lsof -i :3003

# 检查 Nginx 状态
sudo systemctl status nginx
```

### 测试网站

- https://tgmini.usdt2026.cc
- https://hongbao.usdt2026.cc
- https://aikz.usdt2026.cc

---

## 📚 相关文档

- [三个网站部署指南](./DEPLOY_THREE_SITES.md)
- [三个网站部署总结](./THREE_SITES_DEPLOYMENT_SUMMARY.md)
- [处理子模块指南](./HANDLE_SUBMODULES.md)
- [包含 API Key 的文件清单](./FILES_WITH_API_KEYS.md)

---

## 🎯 下一步操作

1. ✅ 三个网站已添加到主仓库
2. ⏳ 推送到 GitHub: `git push origin main`
3. ⏳ 验证 GitHub Actions 部署
4. ⏳ 上传 `.env.local` 文件（如果存在）
5. ⏳ 配置 SSL 证书（如果未配置）

---

**最后更新**: 2025-12-21
