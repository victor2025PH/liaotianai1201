# 项目结构说明

## 主仓库

**唯一的主仓库：** `https://github.com/victor2025PH/liaotianai1201`

所有代码都应该提交到这个主仓库，不要使用其他仓库或子模块。

## 项目目录结构

```
telegram-ai-system/
├── saas-demo/              # 聊天AI后台 (端口 3000)
├── tgmini20251220/        # tgmini 项目 (端口 3001)
├── react-vite-template/
│   └── hbwy20251220/      # hbwy/hongbao 项目 (端口 3002)
│       └── components/
│           └── Technical.tsx
├── aizkw20251219/         # aizkw 项目 (端口 3003)
│   └── 或
└── migrations/
    └── aizkw20251219/     # aizkw 项目 (端口 3003)
```

## 端口分配

| 端口 | 项目 | 目录路径 | PM2 名称 |
|------|------|---------|---------|
| 3000 | saas-demo | `saas-demo/` | `saas-demo` |
| 3001 | tgmini | `tgmini20251220/` | `tgmini-frontend` |
| 3002 | hbwy/hongbao | `react-vite-template/hbwy20251220/` | `hongbao-frontend` |
| 3003 | aizkw | `aizkw20251219/` 或 `migrations/aizkw20251219/` | `aizkw-frontend` |
| 8000 | 后端 | `admin-backend/` | `backend` |

## 重要说明

1. **所有代码都在主仓库中**：不要使用子模块或外部仓库
2. **修复代码应该在本地完成**：修复后提交到主仓库
3. **服务器只负责部署**：从主仓库拉取代码、构建、启动服务

## 代码修复流程

1. **本地修复** → 2. **提交到 Git** → 3. **推送到 GitHub** → 4. **服务器拉取并部署**

## 服务器部署流程

1. **拉取最新代码**：`git pull origin main`
2. **重新构建项目**：`npm run build`
3. **重启服务**：`pm2 restart <service-name>`

或使用自动化脚本：
```bash
bash scripts/server/deploy_from_github.sh
```
