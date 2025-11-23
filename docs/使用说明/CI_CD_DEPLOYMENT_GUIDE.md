# CI/CD 自动化部署指南

本文档说明如何使用 CI/CD 自动化部署流程。

---

## 概述

项目已配置完整的 CI/CD 自动化部署流程，支持：

- ✅ 自动化测试和构建
- ✅ Docker 镜像构建和推送
- ✅ 多环境部署（开发、预发布、生产）
- ✅ Kubernetes 和 Docker Compose 部署
- ✅ 自动回滚机制
- ✅ 部署通知

---

## 工作流文件

### 1. `deploy.yml` - 主要部署工作流

**功能**:
- 自动化测试和构建验证
- Docker 镜像构建和推送到 GitHub Container Registry
- 自动部署到开发环境（develop 分支）
- 自动部署到生产环境（main 分支）
- 支持手动触发部署

**触发条件**:
- Push 到 `main` 或 `develop` 分支
- 手动触发（workflow_dispatch）

**工作流程**:

1. **测试和构建验证**
   - 运行后端测试
   - 运行前端 lint 和构建
   - 生成版本标签

2. **构建 Docker 镜像**
   - 构建所有服务的 Docker 镜像
   - 推送到 GitHub Container Registry
   - 使用构建缓存加速

3. **部署到开发环境**（develop 分支）
   - 自动部署到 Kubernetes 开发集群
   - 健康检查验证

4. **部署到生产环境**（main 分支）
   - 自动部署到 Kubernetes 生产集群
   - 创建备份
   - 健康检查验证
   - 失败时自动回滚

### 2. `docker-compose-deploy.yml` - Docker Compose 部署

**功能**:
- 使用 Docker Compose 部署
- 支持开发环境和预发布环境
- 支持部署、更新、回滚操作

**触发条件**:
- 手动触发（workflow_dispatch）

---

## 使用方式

### 自动部署

#### 开发环境

```bash
# 推送到 develop 分支，自动触发部署
git checkout develop
git push origin develop
```

#### 生产环境

```bash
# 推送到 main 分支，自动触发部署
git checkout main
git merge develop
git push origin main
```

### 手动部署

1. 访问 GitHub Actions 页面
2. 选择 "Deploy to Environments" 工作流
3. 点击 "Run workflow"
4. 选择：
   - **环境**: development / staging / production
   - **服务**: 留空表示全部，或指定服务（逗号分隔）
   - **跳过测试**: 可选

### 使用部署脚本

```bash
# Docker Compose 部署
./scripts/deployment/deploy.sh --method docker-compose --env development --action deploy

# Kubernetes 部署
./scripts/deployment/deploy.sh --method kubernetes --env production --action deploy

# 更新部署
./scripts/deployment/deploy.sh --method kubernetes --env production --action update

# 回滚
./scripts/deployment/deploy.sh --method kubernetes --env production --action rollback
```

---

## 环境配置

### GitHub Secrets

需要在 GitHub 仓库中配置以下 Secrets：

#### Kubernetes 配置

- `KUBECONFIG_DEV`: 开发环境 kubeconfig（base64 编码）
- `KUBECONFIG_STAGING`: 预发布环境 kubeconfig（base64 编码）
- `KUBECONFIG_PROD`: 生产环境 kubeconfig（base64 编码）

#### 通知配置（可选）

- `SLACK_WEBHOOK_URL`: Slack Webhook URL（用于部署通知）
- `TELEGRAM_BOT_TOKEN`: Telegram Bot Token
- `TELEGRAM_CHAT_ID`: Telegram Chat ID

#### Docker Compose 配置

- `ENV_FILE`: .env 文件内容（用于 Docker Compose 部署）

### 生成 kubeconfig Secret

```bash
# 导出 kubeconfig
kubectl config view --flatten > kubeconfig.yaml

# Base64 编码
cat kubeconfig.yaml | base64 -w 0

# 将输出添加到 GitHub Secrets
```

---

## 版本管理

### 版本标签格式

- **生产环境**: `v1.YYYYMMDD-HHMMSS-<SHORT_SHA>`
- **开发环境**: `dev-YYYYMMDD-HHMMSS-<SHORT_SHA>`
- **最新标签**: `latest`（仅 main 分支）

### 查看版本

```bash
# 查看所有镜像标签
ghcr.io/<owner>/<repo>/admin-backend:*

# 查看特定版本
docker pull ghcr.io/<owner>/<repo>/admin-backend:v1.20250119-120000-abc1234
```

---

## 部署验证

### 检查部署状态

```bash
# Kubernetes
kubectl get pods -n group-ai
kubectl get svc -n group-ai
kubectl rollout status deployment/admin-backend -n group-ai

# Docker Compose
docker-compose -f deploy/docker-compose.yaml ps
docker-compose -f deploy/docker-compose.yaml logs -f
```

### 健康检查

```bash
# 后端 API
curl http://localhost:8000/health

# 详细健康检查
curl http://localhost:8000/health?detailed=true
```

---

## 回滚

### 自动回滚

如果部署失败，工作流会自动回滚到之前的版本。

### 手动回滚

#### Kubernetes

```bash
# 回滚到上一个版本
kubectl rollout undo deployment/admin-backend -n group-ai

# 回滚到指定版本
kubectl rollout undo deployment/admin-backend --to-revision=2 -n group-ai

# 查看回滚历史
kubectl rollout history deployment/admin-backend -n group-ai
```

#### Docker Compose

```bash
# 停止当前服务
docker-compose -f deploy/docker-compose.yaml down

# 使用之前的镜像版本
docker-compose -f deploy/docker-compose.yaml up -d
```

---

## 故障排查

### 部署失败

1. **查看工作流日志**
   - 访问 GitHub Actions 页面
   - 查看失败的步骤日志

2. **检查 Kubernetes 资源**
   ```bash
   kubectl describe pod <pod-name> -n group-ai
   kubectl logs <pod-name> -n group-ai
   ```

3. **检查 Docker Compose**
   ```bash
   docker-compose -f deploy/docker-compose.yaml logs
   docker-compose -f deploy/docker-compose.yaml ps
   ```

### 镜像构建失败

1. **检查 Dockerfile**
   ```bash
   docker build -t test -f admin-backend/Dockerfile admin-backend
   ```

2. **检查构建缓存**
   - 清除 GitHub Actions 缓存
   - 重新运行工作流

### 健康检查失败

1. **检查服务是否启动**
   ```bash
   kubectl get pods -n group-ai
   ```

2. **检查端口转发**
   ```bash
   kubectl port-forward -n group-ai svc/admin-backend-service 8000:8000
   curl http://localhost:8000/health
   ```

---

## 最佳实践

### 1. 分支策略

- **develop**: 开发环境，自动部署
- **main**: 生产环境，自动部署
- **feature/***: 功能分支，不自动部署

### 2. 版本管理

- 使用语义化版本号
- 为重要版本创建 Git 标签
- 保留历史版本镜像

### 3. 部署前检查

- 确保所有测试通过
- 检查代码审查
- 验证环境变量配置

### 4. 监控和告警

- 配置部署通知
- 监控服务健康状态
- 设置告警规则

---

## 相关文档

- [Docker 构建指南](DOCKER_BUILD_GUIDE.md)
- [Kubernetes 部署指南](../部署方案/k8s/README.md)
- [Docker Compose 部署](DOCKER_DEPLOYMENT.md)

---

**文档结束**

