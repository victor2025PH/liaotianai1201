#!/bin/bash
# Session 文件跨服务器部署脚本
# 用法: ./deploy_session_to_server.sh <session_name> <server_host> [options]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
SESSION_NAME=""
SERVER_HOST=""
SERVER_USER="${SSH_USER:-root}"
SERVER_PORT="${SSH_PORT:-22}"
REMOTE_DIR="${REMOTE_DEPLOY_DIR:-/opt/group-ai}"
INCLUDE_CONFIG=true
DECRYPT=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --user)
            SERVER_USER="$2"
            shift 2
            ;;
        --port)
            SERVER_PORT="$2"
            shift 2
            ;;
        --remote-dir)
            REMOTE_DIR="$2"
            shift 2
            ;;
        --no-config)
            INCLUDE_CONFIG=false
            shift
            ;;
        --decrypt)
            DECRYPT=true
            shift
            ;;
        --help)
            echo "用法: $0 <session_name> <server_host> [options]"
            echo ""
            echo "参数:"
            echo "  session_name    Session 文件名（不含扩展名）"
            echo "  server_host     目标服务器地址"
            echo ""
            echo "选项:"
            echo "  --user USER       SSH 用户名（默认: root）"
            echo "  --port PORT       SSH 端口（默认: 22）"
            echo "  --remote-dir DIR  远程部署目录（默认: /opt/group-ai）"
            echo "  --no-config       不包含配置文件"
            echo "  --decrypt         解密后部署（如果已加密）"
            echo "  --help            显示帮助"
            exit 0
            ;;
        *)
            if [ -z "$SESSION_NAME" ]; then
                SESSION_NAME="$1"
            elif [ -z "$SERVER_HOST" ]; then
                SERVER_HOST="$1"
            else
                echo -e "${RED}未知参数: $1${NC}"
                exit 1
            fi
            shift
            ;;
    esac
done

# 检查必需参数
if [ -z "$SESSION_NAME" ] || [ -z "$SERVER_HOST" ]; then
    echo -e "${RED}错误: 请提供 Session 名称和服务器地址${NC}"
    echo "用法: $0 <session_name> <server_host> [options]"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Session 文件跨服务器部署${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Session 名称: $SESSION_NAME"
echo "目标服务器: $SERVER_HOST"
echo "SSH 用户: $SERVER_USER"
echo "远程目录: $REMOTE_DIR"
echo ""

# 1. 验证 Session 文件
echo -e "${YELLOW}步骤 1: 验证 Session 文件...${NC}"
python3 "$SCRIPT_DIR/verify_session.py" "$SESSION_NAME" || {
    echo -e "${RED}Session 文件验证失败${NC}"
    exit 1
}
echo -e "${GREEN}✓ Session 文件验证通过${NC}"

# 2. 导出 Session 文件（通过 API 或直接文件）
echo -e "${YELLOW}步骤 2: 准备部署包...${NC}"

# 检查是否可以通过 API 导出
if command -v curl &> /dev/null && [ -n "$API_BASE_URL" ]; then
    echo "通过 API 导出 Session 文件..."
    # TODO: 实现 API 调用
else
    echo "直接使用本地 Session 文件..."
    # 直接使用本地文件
fi

# 3. 创建部署包
TEMP_DIR=$(mktemp -d)
DEPLOY_PACKAGE="$TEMP_DIR/${SESSION_NAME}_deploy.tar.gz"

echo -e "${YELLOW}步骤 3: 创建部署包...${NC}"
# TODO: 实现打包逻辑

# 4. 上传到服务器
echo -e "${YELLOW}步骤 4: 上传到服务器...${NC}"
scp -P "$SERVER_PORT" "$DEPLOY_PACKAGE" "${SERVER_USER}@${SERVER_HOST}:${REMOTE_DIR}/" || {
    echo -e "${RED}上传失败${NC}"
    exit 1
}
echo -e "${GREEN}✓ 文件已上传${NC}"

# 5. 在服务器上解压和配置
echo -e "${YELLOW}步骤 5: 在服务器上配置...${NC}"
ssh -p "$SERVER_PORT" "${SERVER_USER}@${SERVER_HOST}" << EOF
    cd $REMOTE_DIR
    tar -xzf ${SESSION_NAME}_deploy.tar.gz
    cd ${SESSION_NAME}_deploy
    
    # 创建 sessions 目录
    mkdir -p sessions
    
    # 移动 Session 文件
    mv ${SESSION_NAME}.* sessions/ 2>/dev/null || true
    
    # 设置权限
    chmod 600 sessions/${SESSION_NAME}.*
    
    # 如果包含配置文件，提示用户配置
    if [ -f env.example ]; then
        if [ ! -f .env ]; then
            cp env.example .env
            echo "请编辑 .env 文件并填入实际配置"
        fi
    fi
    
    echo "部署完成！"
    echo "下一步："
    echo "1. 编辑 .env 文件"
    echo "2. 运行: python3 scripts/verify_session.py $SESSION_NAME"
    echo "3. 启动服务: python3 main.py"
EOF

echo -e "${GREEN}✓ 部署完成${NC}"
echo ""
echo -e "${BLUE}部署信息:${NC}"
echo "  服务器: $SERVER_HOST"
echo "  目录: $REMOTE_DIR/${SESSION_NAME}_deploy"
echo "  Session 文件: sessions/${SESSION_NAME}.*"

# 清理临时文件
rm -rf "$TEMP_DIR"

