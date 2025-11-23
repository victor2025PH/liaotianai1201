# Kubernetes 部署配置开发完成报告

> **完成日期**: 2025-11-19  
> **优先级**: 🟡 中  
> **状态**: ✅ 已完成

---

## 功能概述

实现了完整的 Kubernetes 部署配置，包括 Deployment、Service、ConfigMap、Secret、Ingress、HPA 等，支持生产环境的高可用部署。

---

## 已完成的工作

### 1. 核心配置文件（10个）

#### ✅ `deploy/k8s/namespace.yaml` - 命名空间

- 创建 `group-ai` 命名空间
- 添加环境标签

#### ✅ `deploy/k8s/configmap.yaml` - 配置管理

**两个 ConfigMap**:
1. `group-ai-config`: 后端应用配置
   - 数据库连接池配置
   - CORS 配置
   - 服务 URL 配置
   - Redis 配置
   - 告警检查配置

2. `group-ai-frontend-config`: 前端应用配置
   - API 基础 URL
   - 环境变量配置

#### ✅ `deploy/k8s/secrets.yaml.example` - 密钥示例

**包含的敏感信息**:
- Telegram API 配置
- OpenAI API Key
- JWT Secret
- 管理员账户
- 数据库连接字符串
- Telegram 告警配置
- Session 加密配置

**安全提示**: 实际使用时通过 `kubectl create secret` 创建，不提交到版本控制。

#### ✅ `deploy/k8s/postgres-deployment.yaml` - PostgreSQL 部署

**特性**:
- PersistentVolumeClaim (20Gi)
- 健康检查（liveness/readiness）
- 资源限制
- Service 暴露

#### ✅ `deploy/k8s/redis-deployment.yaml` - Redis 部署

**特性**:
- 持久化配置（AOF）
- 内存限制策略
- 健康检查
- Service 暴露

#### ✅ `deploy/k8s/admin-backend-deployment.yaml` - 后端部署

**核心特性**:
1. **Deployment**:
   - 副本数: 2（可配置）
   - 环境变量（ConfigMap + Secret）
   - 持久化存储（Session 文件、日志）
   - 健康检查（liveness/readiness）
   - 资源限制

2. **Service**:
   - ClusterIP 类型
   - 端口映射

3. **HorizontalPodAutoscaler (HPA)**:
   - 最小副本: 2
   - 最大副本: 10
   - CPU 阈值: 70%
   - 内存阈值: 80%
   - 扩缩容策略（快速扩容，平滑缩容）

#### ✅ `deploy/k8s/admin-frontend-deployment.yaml` - 前端部署

**包含两个前端**:
1. **admin-frontend** (Vite/React):
   - 副本数: 2
   - Nginx 容器
   - 健康检查

2. **saas-demo** (Next.js):
   - 副本数: 2
   - Node.js 容器
   - 健康检查

**Service**:
- 分别为两个前端创建 Service

#### ✅ `deploy/k8s/ingress.yaml` - 路由配置

**特性**:
- 多域名路由
  - `api.example.com` → 后端 API
  - `admin.example.com` → Vite 前端
  - `app.example.com` → Next.js 前端
- Nginx Ingress Controller 注解
- CORS 配置
- HTTPS 支持（注释，需配置证书）
- 请求大小限制（50MB）

#### ✅ `deploy/k8s/prometheus-deployment.yaml` - Prometheus 监控

**特性**:
- ConfigMap 配置
- 自动服务发现（Kubernetes SD）
- 30 天数据保留
- Service 暴露

#### ✅ `deploy/k8s/README.md` - 部署文档

**包含内容**:
- 前置要求
- 详细部署步骤
- 验证方法
- 更新和回滚
- 故障排查
- 生产环境建议

---

## 技术特性

### 1. 高可用性

- **多副本部署**: 后端和前端都配置了 2 个副本
- **自动故障恢复**: Pod 故障时自动重启
- **健康检查**: liveness 和 readiness 探针
- **滚动更新**: 零停机时间更新

### 2. 自动扩缩容

- **HPA 配置**:
  - CPU 阈值: 70%
  - 内存阈值: 80%
  - 最小副本: 2
  - 最大副本: 10
- **扩缩容策略**:
  - 快速扩容（100% 或 +2 Pods）
  - 平滑缩容（50%，5 分钟稳定窗口）

### 3. 持久化存储

- **PostgreSQL**: 20Gi PVC
- **Session 文件**: 10Gi PVC（ReadWriteMany）
- **日志**: EmptyDir（可选持久化）

### 4. 配置管理

- **ConfigMap**: 非敏感配置
- **Secret**: 敏感信息（加密存储）
- **环境变量**: 从 ConfigMap/Secret 注入

### 5. 服务发现

- **Service**: ClusterIP 类型
- **DNS**: Kubernetes 内部 DNS 解析
- **负载均衡**: Service 自动负载均衡

### 6. 网络配置

- **Ingress**: 外部访问路由
- **CORS**: Ingress 级别 CORS 配置
- **HTTPS**: 支持 TLS 终止（需配置证书）

---

## 部署架构

```
Internet
   │
   ▼
Ingress Controller
   │
   ├─── api.example.com ───► admin-backend-service ───► admin-backend (2+ Pods)
   │
   ├─── admin.example.com ──► admin-frontend-service ──► admin-frontend (2 Pods)
   │
   └─── app.example.com ─────► saas-demo-service ──────► saas-demo (2 Pods)

内部服务:
   ├─── postgres-service ────► postgres (1 Pod)
   ├─── redis-service ───────► redis (1 Pod)
   └─── prometheus-service ──► prometheus (1 Pod)

存储:
   ├─── postgres-pvc (20Gi)
   └─── sessions-pvc (10Gi)
```

---

## 使用指南

### 1. 前置准备

```bash
# 检查 Kubernetes 集群
kubectl cluster-info

# 检查存储类
kubectl get storageclass

# 检查 Ingress Controller
kubectl get ingressclass
```

### 2. 创建 Secret

```bash
kubectl create secret generic group-ai-secrets \
  --from-literal=telegram-api-id='YOUR_API_ID' \
  --from-literal=telegram-api-hash='YOUR_API_HASH' \
  --from-literal=openai-api-key='YOUR_OPENAI_KEY' \
  --from-literal=jwt-secret='YOUR_JWT_SECRET' \
  --from-literal=admin-email='admin@example.com' \
  --from-literal=admin-password='YOUR_PASSWORD' \
  --from-literal=database-url='postgresql://user:pass@postgres-service:5432/dbname' \
  --from-literal=postgres-password='YOUR_POSTGRES_PASSWORD' \
  --from-literal=telegram-bot-token='YOUR_BOT_TOKEN' \
  --from-literal=telegram-chat-id='YOUR_CHAT_ID' \
  --namespace=group-ai
```

### 3. 部署步骤

```bash
# 1. 创建命名空间
kubectl apply -f deploy/k8s/namespace.yaml

# 2. 创建配置
kubectl apply -f deploy/k8s/configmap.yaml

# 3. 部署数据库
kubectl apply -f deploy/k8s/postgres-deployment.yaml
kubectl apply -f deploy/k8s/redis-deployment.yaml

# 4. 构建和推送镜像（替换为实际镜像地址）
docker build -t registry.example.com/group-ai/admin-backend:latest admin-backend
docker push registry.example.com/group-ai/admin-backend:latest

# 5. 更新 deployment.yaml 中的镜像地址，然后部署
kubectl apply -f deploy/k8s/admin-backend-deployment.yaml
kubectl apply -f deploy/k8s/admin-frontend-deployment.yaml

# 6. 部署 Prometheus（可选）
kubectl apply -f deploy/k8s/prometheus-deployment.yaml

# 7. 配置 Ingress（可选，需要更新域名）
kubectl apply -f deploy/k8s/ingress.yaml
```

### 4. 验证部署

```bash
# 检查 Pod 状态
kubectl get pods -n group-ai

# 检查服务
kubectl get svc -n group-ai

# 检查 HPA
kubectl get hpa -n group-ai

# 查看日志
kubectl logs -f deployment/admin-backend -n group-ai
```

### 5. 端口转发（本地测试）

```bash
# 后端 API
kubectl port-forward -n group-ai svc/admin-backend-service 8000:8000

# 前端（Vite）
kubectl port-forward -n group-ai svc/admin-frontend-service 5173:80

# 前端（Next.js）
kubectl port-forward -n group-ai svc/saas-demo-service 3000:3000

# Prometheus
kubectl port-forward -n group-ai svc/prometheus-service 9090:9090
```

---

## 生产环境建议

### 1. 镜像管理

- ✅ 使用版本标签（不要使用 `latest`）
- ✅ 使用私有镜像仓库
- ✅ 定期扫描镜像漏洞

### 2. 资源限制

- ✅ 根据实际负载调整 resources
- ✅ 监控资源使用情况
- ✅ 配置合理的 HPA 阈值

### 3. 安全加固

- ✅ 使用 NetworkPolicy 限制网络访问
- ✅ 启用 Pod Security Policy
- ✅ 定期更新基础镜像
- ✅ 使用 RBAC 限制权限

### 4. 监控告警

- ✅ 配置 Prometheus 告警规则
- ✅ 集成 Grafana Dashboard
- ✅ 设置告警通知（Telegram）

### 5. 备份策略

- ✅ 定期备份数据库（PostgreSQL）
- ✅ 备份 Session 文件（PVC）
- ✅ 测试恢复流程

### 6. HTTPS 配置

```yaml
# 在 ingress.yaml 中取消注释 TLS 配置
tls:
- hosts:
  - api.example.com
  - admin.example.com
  - app.example.com
  secretName: group-ai-tls
```

使用 cert-manager 自动管理证书：

```bash
# 安装 cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# 创建 ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

---

## 故障排查

### Pod 无法启动

```bash
# 查看 Pod 详情
kubectl describe pod <pod-name> -n group-ai

# 查看日志
kubectl logs <pod-name> -n group-ai

# 检查事件
kubectl get events -n group-ai --sort-by='.lastTimestamp'
```

### 服务无法访问

```bash
# 检查 Service
kubectl get svc -n group-ai

# 检查 Endpoints
kubectl get endpoints -n group-ai

# 测试服务连接
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
wget -O- http://admin-backend-service:8000/health
```

### 存储问题

```bash
# 检查 PVC
kubectl get pvc -n group-ai

# 检查 PV
kubectl get pv

# 查看 PVC 详情
kubectl describe pvc <pvc-name> -n group-ai
```

### HPA 不工作

```bash
# 检查 HPA 状态
kubectl describe hpa admin-backend-hpa -n group-ai

# 检查 metrics-server
kubectl get deployment metrics-server -n kube-system

# 查看 Pod 资源使用
kubectl top pods -n group-ai
```

---

## 更新和回滚

### 更新部署

```bash
# 方式 1: 更新镜像
kubectl set image deployment/admin-backend admin-backend=group-ai/admin-backend:v1.1.0 -n group-ai

# 方式 2: 编辑并重新应用
kubectl edit deployment/admin-backend -n group-ai
# 或
kubectl apply -f deploy/k8s/admin-backend-deployment.yaml
```

### 查看更新状态

```bash
kubectl rollout status deployment/admin-backend -n group-ai
```

### 回滚

```bash
# 回滚到上一个版本
kubectl rollout undo deployment/admin-backend -n group-ai

# 查看历史版本
kubectl rollout history deployment/admin-backend -n group-ai

# 回滚到指定版本
kubectl rollout undo deployment/admin-backend --to-revision=2 -n group-ai
```

---

## 相关文件

- `deploy/k8s/namespace.yaml` - 命名空间
- `deploy/k8s/configmap.yaml` - 配置管理
- `deploy/k8s/secrets.yaml.example` - Secret 示例
- `deploy/k8s/postgres-deployment.yaml` - PostgreSQL
- `deploy/k8s/redis-deployment.yaml` - Redis
- `deploy/k8s/admin-backend-deployment.yaml` - 后端部署
- `deploy/k8s/admin-frontend-deployment.yaml` - 前端部署
- `deploy/k8s/ingress.yaml` - Ingress 路由
- `deploy/k8s/prometheus-deployment.yaml` - Prometheus
- `deploy/k8s/README.md` - 部署文档

---

## 总结

Kubernetes 部署配置已成功实现，提供了：

- ✅ 完整的 Kubernetes 部署配置（10 个文件）
- ✅ 高可用性（多副本、健康检查、自动恢复）
- ✅ 自动扩缩容（HPA）
- ✅ 持久化存储（PVC）
- ✅ 配置管理（ConfigMap/Secret）
- ✅ 服务发现和负载均衡
- ✅ 详细的部署文档

系统已具备生产环境 Kubernetes 部署能力，支持高可用、自动扩缩容和滚动更新。

---

**报告结束**

