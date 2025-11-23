# Docker 部署指南

> **更新日期**: 2025-01-17  
> **适用版本**: v1.0+

---

## 📋 目录

1. [快速开始](#快速开始)
2. [Docker Compose 部署](#docker-compose-部署)
3. [单独容器部署](#单独容器部署)
4. [生产环境配置](#生产环境配置)
5. [常见问题](#常见问题)

---

## 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 20GB 可用磁盘空间

### 一键启动（推荐）

```bash
# 克隆项目（如果尚未克隆）
git clone <repository-url>
cd 聊天AI群聊程序

# 配置环境变量
cp docs/env.example .env
# 编辑 .env 文件，填入必填环境变量

# 启动所有服务
docker-compose -f admin-backend/docker-compose.yml up -d

# 查看日志
docker-compose -f admin-backend/docker-compose.yml logs -f
```

---

## Docker Compose 部署

### 配置文件位置

- `admin-backend/docker-compose.yml` - 后端服务配置

### 服务说明

#### 1. admin-backend（后端 API 服务）

- **端口**: 8000
- **镜像**: 自动构建（基于 `admin-backend/Dockerfile`）
- **依赖**: Redis

#### 2. redis（Redis 缓存服务）

- **端口**: 6379
- **镜像**: `redis:7-alpine`
- **用途**: 缓存、队列（可选）

### 启动步骤

#### 1. 准备环境变量

创建 `.env` 文件（`admin-backend/.env`）：

```env
# 数据库配置
DATABASE_URL=sqlite:///./admin.db
# 或 PostgreSQL: postgresql://user:password@postgres:5432/dbname

# Redis 配置
REDIS_URL=redis://redis:6379/0

# JWT 配置（⚠️ 生产环境必须修改！）
JWT_SECRET=your_strong_random_secret_here
JWT_ALGORITHM=HS256

# 管理员配置（⚠️ 生产环境必须修改！）
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=your_strong_password_here

# 其他配置
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

#### 2. 构建并启动

```bash
cd admin-backend

# 构建镜像（首次或更新代码后）
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f admin-backend
```

#### 3. 初始化数据库

```bash
# 进入容器
docker-compose exec admin-backend bash

# 运行数据库迁移（自动备份 + 迁移）
poetry run python -m scripts.run_migrations

# 或直接使用 Alembic
poetry run alembic upgrade head
```

#### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health
# 预期: {"status":"ok"}

# Kubernetes 健康检查
curl http://localhost:8000/healthz
# 预期: {"status":"ok"}

# API 文档
open http://localhost:8000/docs
```

### 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [service_name]

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器和卷（⚠️ 会删除数据）
docker-compose down -v

# 重启服务
docker-compose restart [service_name]

# 进入容器
docker-compose exec admin-backend bash
```

---

## 单独容器部署

### 构建后端镜像

```bash
cd admin-backend

# 构建镜像
docker build -t group-ai-backend:latest .

# 查看镜像
docker images | grep group-ai-backend
```

### 运行容器

```bash
# 运行后端容器
docker run -d \
  --name group-ai-backend \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./admin.db \
  -e REDIS_URL=redis://redis:6379/0 \
  -e JWT_SECRET=your_secret_here \
  -v $(pwd)/admin.db:/app/admin.db \
  --restart unless-stopped \
  group-ai-backend:latest

# 查看日志
docker logs -f group-ai-backend

# 停止容器
docker stop group-ai-backend

# 删除容器
docker rm group-ai-backend
```

### 使用外部 Redis

```bash
# 运行 Redis 容器
docker run -d \
  --name redis \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:7-alpine

# 运行后端容器（连接到外部 Redis）
docker run -d \
  --name group-ai-backend \
  -p 8000:8000 \
  --link redis:redis \
  -e REDIS_URL=redis://redis:6379/0 \
  group-ai-backend:latest
```

---

## 生产环境配置

### 1. 使用 PostgreSQL 数据库

#### 使用 Docker Compose

修改 `docker-compose.yml`：

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: group_ai
      POSTGRES_USER: group_ai
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  admin-backend:
    build: .
    environment:
      DATABASE_URL: postgresql://group_ai:${DB_PASSWORD}@postgres:5432/group_ai
      # ... 其他环境变量
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

#### 环境变量

```env
DATABASE_URL=postgresql://group_ai:strong_password@postgres:5432/group_ai
```

#### 初始化数据库

```bash
# 等待 PostgreSQL 启动
sleep 10

# 运行迁移
docker-compose exec admin-backend poetry run python -m scripts.run_migrations
```

### 2. 使用 HTTPS（Nginx 反向代理）

#### Nginx 配置示例

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://admin-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查
    location /health {
        proxy_pass http://admin-backend:8000/health;
        access_log off;
    }

    location /healthz {
        proxy_pass http://admin-backend:8000/healthz;
        access_log off;
    }
}
```

### 3. 数据持久化

#### 数据库数据

使用 Docker 卷持久化数据：

```yaml
services:
  admin-backend:
    volumes:
      - ./admin.db:/app/admin.db  # SQLite
      # 或
      - ./data:/app/data  # 数据目录

  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### 备份数据

```bash
# 备份 SQLite 数据库
docker cp admin-backend:/app/admin.db ./backup/admin_backup_$(date +%Y%m%d_%H%M%S).db

# 备份 PostgreSQL 数据库
docker-compose exec postgres pg_dump -U group_ai group_ai > backup/backup_$(date +%Y%m%d_%H%M%S).sql
```

### 4. 监控和日志

#### 日志配置

```yaml
services:
  admin-backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### 查看日志

```bash
# 实时日志
docker-compose logs -f admin-backend

# 最近 100 行日志
docker-compose logs --tail=100 admin-backend

# 特定时间范围的日志
docker-compose logs --since 30m admin-backend
```

### 5. 资源限制

```yaml
services:
  admin-backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 6. 健康检查

Docker Compose 自动健康检查：

```yaml
services:
  admin-backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## 常见问题

### 1. 容器启动失败

**问题**: 容器立即退出

**解决方法**:
```bash
# 查看日志
docker-compose logs admin-backend

# 检查环境变量
docker-compose config

# 手动运行容器调试
docker-compose run --rm admin-backend bash
```

### 2. 数据库连接失败

**问题**: 无法连接到数据库

**解决方法**:
- 检查 `DATABASE_URL` 环境变量
- 确保数据库服务已启动：`docker-compose ps`
- 检查网络连接：`docker-compose exec admin-backend ping postgres`

### 3. 迁移失败

**问题**: Alembic 迁移失败

**解决方法**:
```bash
# 进入容器
docker-compose exec admin-backend bash

# 检查当前迁移版本
poetry run alembic current

# 查看迁移历史
poetry run alembic history

# 手动回滚（如果需要）
poetry run alembic downgrade -1
```

### 4. 端口冲突

**问题**: 端口 8000 已被占用

**解决方法**:
- 修改 `docker-compose.yml` 中的端口映射：
  ```yaml
  ports:
    - "8001:8000"  # 外部端口:内部端口
  ```

### 5. 权限问题

**问题**: 无法写入数据库文件

**解决方法**:
```bash
# 检查文件权限
ls -la admin.db

# 修复权限
sudo chown $USER:$USER admin.db
chmod 644 admin.db
```

---

## 最佳实践

### 1. 环境变量管理

- ✅ 使用 `.env` 文件管理环境变量
- ✅ 不要将 `.env` 文件提交到 Git
- ✅ 生产环境使用密钥管理服务（如 AWS Secrets Manager、Azure Key Vault）

### 2. 数据备份

- ✅ 定期备份数据库（每日）
- ✅ 使用自动化备份脚本
- ✅ 备份存储在不同位置（异地备份）

### 3. 监控和告警

- ✅ 监控容器健康状态
- ✅ 设置资源使用告警
- ✅ 监控 API 响应时间

### 4. 安全

- ✅ 使用强密码和随机密钥
- ✅ 限制容器网络访问
- ✅ 定期更新镜像和依赖
- ✅ 使用 HTTPS（生产环境）

### 5. 性能优化

- ✅ 使用 PostgreSQL（生产环境）
- ✅ 配置 Redis 缓存
- ✅ 设置合理的资源限制
- ✅ 使用负载均衡（多实例）

---

## 相关文档

- `admin-backend/docs/MIGRATION_GUIDE.md` - 数据库迁移指南
- `docs/env.example` - 环境变量示例
- `admin-backend/README.md` - 后端 README
- `docs/使用说明/DEPLOYMENT_GUIDE.md` - 完整部署指南

---

**文档维护**: 如有问题或建议，请提交 Issue 或 Pull Request。

