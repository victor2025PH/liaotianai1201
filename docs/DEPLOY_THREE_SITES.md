# 三个网站部署指南

> **网站列表**:
> - https://tgmini.usdt2026.cc - TON Mini App Studio
> - https://hongbao.usdt2026.cc - RedEnvelope.fi
> - https://aizkw.usdt2026.cc - Smart Control King // AI 智控王

---

## 📋 项目结构

### 本地目录

1. **tgmini20251220/** - TON Mini App Studio
   - 技术栈: Vite + React + TypeScript
   - 端口: 3001
   - PM2 名称: `tgmini-frontend`

2. **hbwy20251220/** - RedEnvelope.fi
   - 技术栈: Vite + React + TypeScript
   - 端口: 3002
   - PM2 名称: `hongbao-frontend`

3. **aizkw20251219/** - Smart Control King
   - 技术栈: Vite + React + TypeScript
   - 端口: 3003
   - PM2 名称: `aizkw-frontend`

---

## 🚀 部署方式

### 自动部署（GitHub Actions）

当以下文件发生变更时，会自动触发部署：

- `tgmini20251220/**`
- `hbwy20251220/**`
- `aizkw20251219/**`
- `.github/workflows/deploy-three-sites.yml`

**工作流文件**: `.github/workflows/deploy-three-sites.yml`

### 手动触发部署

在 GitHub Actions 页面点击 "Run workflow" 按钮。

---

## 📝 部署流程

每个网站的部署流程：

1. **拉取最新代码** - 从 GitHub 同步代码
2. **安装依赖** - 执行 `npm install`
3. **构建项目** - 执行 `npm run build`（生成 `dist` 目录）
4. **停止旧进程** - 停止 PM2 中的旧进程
5. **启动服务** - 使用 `serve` 在指定端口启动静态文件服务
6. **配置 Nginx** - 更新 Nginx 配置并重载

---

## 🔧 服务器配置

### 端口分配

- `tgmini`: 3001
- `hongbao`: 3002
- `aizkw`: 3003

### PM2 进程名称

- `tgmini-frontend`
- `hongbao-frontend`
- `aizkw-frontend`

### Nginx 配置位置

- `/etc/nginx/sites-available/tgmini.usdt2026.cc`
- `/etc/nginx/sites-available/hongbao.usdt2026.cc`
- `/etc/nginx/sites-available/aikz.usdt2026.cc`

---

## ⚠️ 重要注意事项

### 1. 环境变量文件

每个项目可能包含 `.env.local` 文件，这些文件**不会**被提交到 GitHub。

**需要手动上传的文件**:

- `tgmini20251220/.env.local`（如果存在）
- `hbwy20251220/.env.local`（如果存在）
- `aizkw20251219/.env.local`（如果存在）

**上传命令**:

```bash
scp tgmini20251220/.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/tgmini20251220/.env.local
scp hbwy20251220/.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/hbwy20251220/.env.local
scp aizkw20251219/.env.local ubuntu@165.154.242.60:/home/ubuntu/telegram-ai-system/aizkw20251219/.env.local
```

### 2. SSL 证书

确保每个域名都有有效的 SSL 证书：

```bash
# 检查证书
sudo certbot certificates

# 如果需要申请证书
sudo certbot --nginx -d tgmini.usdt2026.cc
sudo certbot --nginx -d hongbao.usdt2026.cc
sudo certbot --nginx -d aikz.usdt2026.cc
```

### 3. 构建输出

所有项目使用 Vite 构建，输出目录为 `dist/`。

构建后的文件是静态文件，使用 `serve` 提供服务。

---

## 🔍 验证部署

### 检查服务状态

```bash
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

## 🛠️ 故障排查

### 问题 1: 构建失败

**检查**:
- 查看 GitHub Actions 日志
- 检查 `package.json` 和依赖

**解决**:
- 确保所有依赖都已安装
- 检查 Node.js 版本兼容性

### 问题 2: 服务未启动

**检查**:
```bash
pm2 logs tgmini-frontend
pm2 logs hongbao-frontend
pm2 logs aizkw-frontend
```

**解决**:
- 检查端口是否被占用
- 检查 `dist` 目录是否存在
- 检查 `serve` 是否已安装

### 问题 3: Nginx 502 错误

**检查**:
```bash
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

**解决**:
- 检查 Nginx 配置语法
- 检查后端服务是否运行
- 检查端口是否正确

---

## 📚 相关文档

- [包含 API Key 的文件清单](./FILES_WITH_API_KEYS.md)
- [手动上传 .env 文件指南](./MANUAL_UPLOAD_ENV_FILES.md)
- [GitHub Actions 部署配置](../.github/workflows/deploy-three-sites.yml)
