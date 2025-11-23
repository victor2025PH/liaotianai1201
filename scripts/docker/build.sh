#!/bin/bash
# Docker 镜像构建脚本
# 用法: ./build.sh [service] [tag] [--push]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认配置
REGISTRY="${DOCKER_REGISTRY:-group-ai}"
DEFAULT_TAG="latest"
PUSH=false

# 解析参数
SERVICE=$1
TAG=${2:-$DEFAULT_TAG}
if [[ "$*" == *"--push"* ]]; then
    PUSH=true
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 构建函数
build_image() {
    local service=$1
    local tag=$2
    local context=""
    local dockerfile=""
    local build_args=""
    
    case $service in
        "admin-backend"|"backend")
            context="$PROJECT_ROOT/admin-backend"
            dockerfile="$PROJECT_ROOT/admin-backend/Dockerfile"
            ;;
        "admin-frontend"|"frontend")
            context="$PROJECT_ROOT/admin-frontend"
            dockerfile="$PROJECT_ROOT/admin-frontend/Dockerfile"
            build_args="--build-arg VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://localhost:8000/api/v1}"
            ;;
        "saas-demo"|"demo")
            context="$PROJECT_ROOT/saas-demo"
            dockerfile="$PROJECT_ROOT/saas-demo/Dockerfile"
            build_args="--build-arg NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}"
            ;;
        "session-service"|"session")
            context="$PROJECT_ROOT"
            dockerfile="$PROJECT_ROOT/deploy/session-service.Dockerfile"
            ;;
        "all")
            echo -e "${YELLOW}构建所有服务...${NC}"
            build_image "admin-backend" "$tag"
            build_image "admin-frontend" "$tag"
            build_image "saas-demo" "$tag"
            build_image "session-service" "$tag"
            return 0
            ;;
        *)
            echo -e "${RED}错误: 未知的服务 '$service'${NC}"
            echo "可用服务: admin-backend, admin-frontend, saas-demo, session-service, all"
            exit 1
            ;;
    esac
    
    local image_name="$REGISTRY/$service:$tag"
    
    echo -e "${GREEN}构建镜像: $image_name${NC}"
    echo "Context: $context"
    echo "Dockerfile: $dockerfile"
    
    # 构建镜像
    docker build \
        -f "$dockerfile" \
        -t "$image_name" \
        $build_args \
        "$context"
    
    # 如果指定了推送，则推送镜像
    if [ "$PUSH" = true ]; then
        echo -e "${YELLOW}推送镜像: $image_name${NC}"
        docker push "$image_name"
    fi
    
    echo -e "${GREEN}✓ 构建完成: $image_name${NC}"
}

# 主函数
main() {
    if [ -z "$SERVICE" ]; then
        echo -e "${RED}错误: 请指定要构建的服务${NC}"
        echo "用法: $0 [service] [tag] [--push]"
        echo ""
        echo "服务:"
        echo "  admin-backend    - 后端 API 服务"
        echo "  admin-frontend   - 前端管理界面 (Vite)"
        echo "  saas-demo       - SaaS Demo 前端 (Next.js)"
        echo "  session-service - Session 服务"
        echo "  all             - 构建所有服务"
        echo ""
        echo "示例:"
        echo "  $0 admin-backend latest"
        echo "  $0 admin-backend v1.0.0 --push"
        echo "  $0 all latest"
        exit 1
    fi
    
    build_image "$SERVICE" "$TAG"
}

main

