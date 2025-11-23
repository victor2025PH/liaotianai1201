#!/bin/bash
# 部署脚本 - 支持 Docker Compose 和 Kubernetes

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEPLOY_METHOD="${DEPLOY_METHOD:-docker-compose}"
ENVIRONMENT="${ENVIRONMENT:-development}"
ACTION="${ACTION:-deploy}"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --method)
            DEPLOY_METHOD="$2"
            shift 2
            ;;
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --action)
            ACTION="$2"
            shift 2
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --method METHOD    部署方法 (docker-compose|kubernetes)"
            echo "  --env ENV          环境 (development|staging|production)"
            echo "  --action ACTION    操作 (deploy|update|rollback)"
            echo "  --help             显示帮助"
            exit 0
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}部署配置${NC}"
echo -e "${BLUE}========================================${NC}"
echo "部署方法: $DEPLOY_METHOD"
echo "环境: $ENVIRONMENT"
echo "操作: $ACTION"
echo ""

# Docker Compose 部署
deploy_docker_compose() {
    echo -e "${GREEN}使用 Docker Compose 部署...${NC}"
    
    cd "$PROJECT_ROOT"
    
    COMPOSE_FILE="deploy/docker-compose.yaml"
    if [ "$ENVIRONMENT" != "development" ]; then
        COMPOSE_FILE="deploy/docker-compose.${ENVIRONMENT}.yaml"
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${YELLOW}警告: $COMPOSE_FILE 不存在，使用默认配置${NC}"
        COMPOSE_FILE="deploy/docker-compose.yaml"
    fi
    
    case $ACTION in
        deploy)
            echo -e "${GREEN}部署服务...${NC}"
            docker-compose -f "$COMPOSE_FILE" up -d --build
            ;;
        update)
            echo -e "${GREEN}更新服务...${NC}"
            docker-compose -f "$COMPOSE_FILE" pull
            docker-compose -f "$COMPOSE_FILE" up -d
            ;;
        rollback)
            echo -e "${YELLOW}回滚服务...${NC}"
            docker-compose -f "$COMPOSE_FILE" down
            # 恢复到之前的版本
            ;;
        *)
            echo -e "${RED}未知操作: $ACTION${NC}"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}等待服务启动...${NC}"
    sleep 10
    
    echo -e "${GREEN}检查服务状态...${NC}"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo -e "${GREEN}健康检查...${NC}"
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 部署成功${NC}"
    else
        echo -e "${RED}✗ 健康检查失败${NC}"
        docker-compose -f "$COMPOSE_FILE" logs --tail=50
        exit 1
    fi
}

# Kubernetes 部署
deploy_kubernetes() {
    echo -e "${GREEN}使用 Kubernetes 部署...${NC}"
    
    cd "$PROJECT_ROOT/deploy/k8s"
    
    # 检查 kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}错误: kubectl 未安装${NC}"
        exit 1
    fi
    
    # 检查 kubeconfig
    if [ -z "$KUBECONFIG" ] && [ ! -f "$HOME/.kube/config" ]; then
        echo -e "${RED}错误: 未找到 kubeconfig${NC}"
        exit 1
    fi
    
    case $ACTION in
        deploy)
            echo -e "${GREEN}部署到 Kubernetes...${NC}"
            kubectl apply -f namespace.yaml
            kubectl apply -f configmap.yaml
            kubectl apply -f postgres-deployment.yaml
            kubectl apply -f redis-deployment.yaml
            kubectl apply -f admin-backend-deployment.yaml
            kubectl apply -f admin-frontend-deployment.yaml
            
            echo -e "${GREEN}等待部署完成...${NC}"
            kubectl rollout status deployment/admin-backend -n group-ai --timeout=10m
            kubectl rollout status deployment/admin-frontend -n group-ai --timeout=10m
            kubectl rollout status deployment/saas-demo -n group-ai --timeout=10m
            ;;
        update)
            echo -e "${GREEN}更新部署...${NC}"
            kubectl set image deployment/admin-backend admin-backend=$IMAGE_TAG -n group-ai
            kubectl set image deployment/admin-frontend admin-frontend=$IMAGE_TAG -n group-ai
            kubectl set image deployment/saas-demo saas-demo=$IMAGE_TAG -n group-ai
            
            kubectl rollout status deployment/admin-backend -n group-ai --timeout=10m
            kubectl rollout status deployment/admin-frontend -n group-ai --timeout=10m
            kubectl rollout status deployment/saas-demo -n group-ai --timeout=10m
            ;;
        rollback)
            echo -e "${YELLOW}回滚部署...${NC}"
            kubectl rollout undo deployment/admin-backend -n group-ai
            kubectl rollout undo deployment/admin-frontend -n group-ai
            kubectl rollout undo deployment/saas-demo -n group-ai
            
            kubectl rollout status deployment/admin-backend -n group-ai --timeout=10m
            kubectl rollout status deployment/admin-frontend -n group-ai --timeout=10m
            kubectl rollout status deployment/saas-demo -n group-ai --timeout=10m
            ;;
        *)
            echo -e "${RED}未知操作: $ACTION${NC}"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}检查 Pod 状态...${NC}"
    kubectl get pods -n group-ai
    
    echo -e "${GREEN}检查服务状态...${NC}"
    kubectl get svc -n group-ai
}

# 主函数
main() {
    case $DEPLOY_METHOD in
        docker-compose)
            deploy_docker_compose
            ;;
        kubernetes|k8s)
            deploy_kubernetes
            ;;
        *)
            echo -e "${RED}未知的部署方法: $DEPLOY_METHOD${NC}"
            echo "支持的部署方法: docker-compose, kubernetes"
            exit 1
            ;;
    esac
}

main

