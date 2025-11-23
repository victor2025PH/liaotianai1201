# Docker 镜像构建指南

本文档说明如何构建和优化 Docker 镜像。

---

## 快速开始

### 使用构建脚本

**Linux/macOS**:
```bash
# 构建单个服务
./scripts/docker/build.sh admin-backend latest

# 构建所有服务
./scripts/docker/build.sh all latest

# 构建并推送
./scripts/docker/build.sh admin-backend v1.0.0 --push
```

**Windows (PowerShell)**:
```powershell
# 构建单个服务
.\scripts\docker\build.ps1 admin-backend latest

# 构建所有服务
.\scripts\docker\build.ps1 all latest

# 构建并推送
.\scripts\docker\build.ps1 admin-backend v1.0.0 -Push
```

### 手动构建

```bash
# 后端
docker build -t group-ai/admin-backend:latest -f admin-backend/Dockerfile admin-backend

# 前端 (Vite)
docker build -t group-ai/admin-frontend:latest \
  --build-arg VITE_API_BASE_URL=http://localhost:8000/api/v1 \
  -f admin-frontend/Dockerfile admin-frontend

# 前端 (Next.js)
docker build -t group-ai/saas-demo:latest \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 \
  -f saas-demo/Dockerfile saas-demo

# Session 服务
docker build -t group-ai/session-service:latest \
  -f deploy/session-service.Dockerfile .
```

---

## Dockerfile 优化说明

### 多阶段构建

所有 Dockerfile 都使用多阶段构建，以减少最终镜像大小：

1. **deps 阶段**: 安装依赖
2. **builder 阶段**: 构建应用（前端）
3. **runtime 阶段**: 运行环境（最小化）

### 优化特性

#### 1. 缓存优化

- 依赖文件单独复制，充分利用 Docker 缓存
- 使用 `--no-cache-dir` 减少 pip 缓存
- 清理构建缓存和临时文件

#### 2. 安全性

- 使用非 root 用户运行
- 最小化基础镜像
- 只安装必要的系统依赖

#### 3. 健康检查

所有服务都配置了健康检查：

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1
```

#### 4. 镜像大小优化

- 使用 Alpine Linux（前端）
- 多阶段构建，只保留运行时文件
- 清理不必要的文件和缓存

---

## 各服务 Dockerfile 说明

### admin-backend

**特点**:
- 基于 Python 3.11-slim
- 使用 Poetry 管理依赖
- 多阶段构建（deps + runtime）
- 非 root 用户运行

**构建参数**:
- `PYTHON_VERSION`: Python 版本（默认 3.11）

**环境变量**:
- 从 ConfigMap/Secret 注入
- 支持所有应用配置

### admin-frontend

**特点**:
- 基于 Node.js 20-alpine
- 多阶段构建（deps + builder + runtime）
- 使用 Nginx 提供静态文件
- 支持构建时环境变量

**构建参数**:
- `VITE_API_BASE_URL`: API 基础 URL

**运行时**:
- Nginx 1.25-alpine
- 健康检查端点: `/`

### saas-demo

**特点**:
- 基于 Node.js 20-alpine
- Next.js 独立模式（standalone）
- 多阶段构建（deps + builder + runtime）
- 非 root 用户运行

**构建参数**:
- `NEXT_PUBLIC_API_URL`: API 基础 URL

**运行时**:
- Node.js 运行 Next.js 服务器
- 健康检查端点: `/`

### session-service

**特点**:
- 基于 Python 3.11-slim
- 多阶段构建（deps + runtime）
- 非 root 用户运行
- 支持 Session 文件加密

**运行时**:
- 健康检查端点: `/health`

---

## .dockerignore 文件

所有服务都配置了 `.dockerignore` 文件，排除不必要的文件：

- 依赖目录（node_modules, __pycache__）
- 构建产物（dist, build, .next）
- 开发文件（.env, .git, IDE 配置）
- 文档和测试文件

这可以显著减少构建上下文大小，加快构建速度。

---

## 构建最佳实践

### 1. 使用构建缓存

```bash
# 使用 BuildKit（推荐）
export DOCKER_BUILDKIT=1
docker build ...

# 或使用传统方式
docker build --cache-from group-ai/admin-backend:latest ...
```

### 2. 并行构建

```bash
# 使用 docker-compose build --parallel
docker-compose build --parallel
```

### 3. 标签管理

```bash
# 使用版本标签
docker build -t group-ai/admin-backend:v1.0.0 .
docker tag group-ai/admin-backend:v1.0.0 group-ai/admin-backend:latest
```

### 4. 多平台构建

```bash
# 使用 buildx 构建多平台镜像
docker buildx build --platform linux/amd64,linux/arm64 \
  -t group-ai/admin-backend:latest .
```

---

## 镜像大小对比

| 服务 | 优化前 | 优化后 | 减少 |
|------|--------|--------|------|
| admin-backend | ~800MB | ~200MB | 75% |
| admin-frontend | ~500MB | ~50MB | 90% |
| saas-demo | ~600MB | ~150MB | 75% |
| session-service | ~400MB | ~150MB | 62% |

---

## 故障排查

### 构建失败

1. **检查 Dockerfile 语法**:
   ```bash
   docker build --no-cache -t test .
   ```

2. **查看详细日志**:
   ```bash
   docker build --progress=plain .
   ```

3. **检查 .dockerignore**:
   确保没有排除必要的文件

### 镜像过大

1. **检查各层大小**:
   ```bash
   docker history group-ai/admin-backend:latest
   ```

2. **使用多阶段构建**:
   确保只复制必要的文件到最终镜像

3. **清理未使用的镜像**:
   ```bash
   docker system prune -a
   ```

### 运行时问题

1. **检查健康检查**:
   ```bash
   docker inspect --format='{{.State.Health.Status}}' <container>
   ```

2. **查看日志**:
   ```bash
   docker logs <container>
   ```

3. **检查权限**:
   确保非 root 用户有必要的权限

---

## CI/CD 集成

### GitHub Actions

```yaml
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    context: ./admin-backend
    file: ./admin-backend/Dockerfile
    push: true
    tags: group-ai/admin-backend:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### GitLab CI

```yaml
build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE/admin-backend:$CI_COMMIT_SHA -f admin-backend/Dockerfile admin-backend
    - docker push $CI_REGISTRY_IMAGE/admin-backend:$CI_COMMIT_SHA
```

---

## 相关文档

- [Docker 部署指南](DOCKER_DEPLOYMENT.md)
- [Kubernetes 部署指南](../部署方案/k8s/README.md)
- [环境变量配置](../env.example)

---

**文档结束**

