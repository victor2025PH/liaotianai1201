# Kubernetes 部署指南

本文档说明如何使用 Kubernetes 部署 Group AI 系统。

## 前置要求

1. Kubernetes 集群（版本 1.20+）
2. kubectl 命令行工具
3. 存储类（StorageClass）配置
4. Ingress Controller（可选，用于外部访问）

## 部署步骤

### 1. 创建命名空间

```bash
kubectl apply -f namespace.yaml
```

### 2. 创建配置

```bash
# 创建 ConfigMap
kubectl apply -f configmap.yaml
```

### 3. 创建 Secret

**重要**: 首先需要创建 Secret，包含敏感信息。

```bash
# 方式 1: 使用 kubectl 命令创建
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

# 方式 2: 使用示例文件（需要编辑 secrets.yaml.example）
# 编辑 secrets.yaml.example，然后：
kubectl apply -f secrets.yaml.example
```

### 4. 部署数据库和 Redis

```bash
# 部署 PostgreSQL
kubectl apply -f postgres-deployment.yaml

# 部署 Redis
kubectl apply -f redis-deployment.yaml
```

### 5. 构建和推送 Docker 镜像

```bash
# 构建后端镜像
docker build -t group-ai/admin-backend:latest -f admin-backend/Dockerfile admin-backend

# 构建前端镜像（Vite）
docker build -t group-ai/admin-frontend:latest -f admin-frontend/Dockerfile admin-frontend

# 构建前端镜像（Next.js）
docker build -t group-ai/saas-demo:latest -f saas-demo/Dockerfile saas-demo

# 推送到镜像仓库（替换为实际仓库地址）
docker tag group-ai/admin-backend:latest registry.example.com/group-ai/admin-backend:latest
docker push registry.example.com/group-ai/admin-backend:latest

# 更新 deployment.yaml 中的镜像地址
```

### 6. 部署应用

```bash
# 部署后端
kubectl apply -f admin-backend-deployment.yaml

# 部署前端
kubectl apply -f admin-frontend-deployment.yaml
```

### 7. 部署 Prometheus（可选）

```bash
kubectl apply -f prometheus-deployment.yaml
```

### 8. 配置 Ingress（可选）

```bash
# 编辑 ingress.yaml，更新域名
kubectl apply -f ingress.yaml
```

## 验证部署

### 检查 Pod 状态

```bash
kubectl get pods -n group-ai
```

所有 Pod 应该处于 `Running` 状态。

### 检查服务

```bash
kubectl get svc -n group-ai
```

### 查看日志

```bash
# 后端日志
kubectl logs -f deployment/admin-backend -n group-ai

# 前端日志
kubectl logs -f deployment/admin-frontend -n group-ai
```

### 端口转发（用于本地测试）

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

## 自动扩缩容

系统已配置 HorizontalPodAutoscaler (HPA)，会根据 CPU 和内存使用率自动调整 Pod 数量。

查看 HPA 状态：

```bash
kubectl get hpa -n group-ai
```

## 持久化存储

Session 文件和数据库数据使用 PersistentVolumeClaim (PVC) 持久化存储。

查看 PVC 状态：

```bash
kubectl get pvc -n group-ai
```

## 更新部署

### 更新镜像

```bash
# 方式 1: 更新 Deployment 中的镜像标签
kubectl set image deployment/admin-backend admin-backend=group-ai/admin-backend:v1.1.0 -n group-ai

# 方式 2: 编辑 deployment.yaml，然后重新应用
kubectl apply -f admin-backend-deployment.yaml
```

### 滚动更新

Kubernetes 会自动执行滚动更新，确保零停机时间。

查看更新状态：

```bash
kubectl rollout status deployment/admin-backend -n group-ai
```

### 回滚

如果更新出现问题，可以回滚到之前的版本：

```bash
kubectl rollout undo deployment/admin-backend -n group-ai
```

## 故障排查

### Pod 无法启动

```bash
# 查看 Pod 详情
kubectl describe pod <pod-name> -n group-ai

# 查看日志
kubectl logs <pod-name> -n group-ai
```

### 服务无法访问

```bash
# 检查 Service
kubectl get svc -n group-ai

# 检查 Endpoints
kubectl get endpoints -n group-ai

# 测试服务连接
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# 在容器内测试连接
wget -O- http://admin-backend-service:8000/health
```

### 存储问题

```bash
# 检查 PVC
kubectl get pvc -n group-ai

# 检查 PV
kubectl get pv
```

## 清理部署

```bash
# 删除所有资源
kubectl delete namespace group-ai

# 或者逐个删除
kubectl delete -f ingress.yaml
kubectl delete -f admin-frontend-deployment.yaml
kubectl delete -f admin-backend-deployment.yaml
kubectl delete -f prometheus-deployment.yaml
kubectl delete -f redis-deployment.yaml
kubectl delete -f postgres-deployment.yaml
kubectl delete -f configmap.yaml
kubectl delete -f namespace.yaml
```

## 生产环境建议

1. **使用私有镜像仓库**: 不要使用 `latest` 标签，使用版本标签
2. **配置资源限制**: 根据实际需求调整 resources 配置
3. **启用 HTTPS**: 配置 TLS 证书和 Ingress
4. **备份策略**: 定期备份数据库和 Session 文件
5. **监控告警**: 配置 Prometheus 和 Grafana
6. **日志聚合**: 使用 ELK 或 Loki 收集日志
7. **安全加固**: 使用 NetworkPolicy 限制网络访问

## 相关文档

- [Docker Compose 部署](../docker-compose.yaml)
- [部署指南](../../docs/使用说明/DEPLOYMENT_GUIDE.md)
- [环境变量配置](../../docs/env.example)

