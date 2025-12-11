#!/bin/bash
# ============================================================
# 诊断 luckyred-api 服务启动失败
# ============================================================
# 功能：检查服务配置、文件路径、权限等，找出启动失败的原因
# 使用方法：bash scripts/server/diagnose-luckyred-api.sh
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "🔍 诊断 luckyred-api 服务启动失败"
echo "============================================================"
echo ""

# 服务配置路径
SERVICE_FILE="/etc/systemd/system/luckyred-api.service"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

echo "📋 检查项目："
echo ""

# 1. 检查服务文件是否存在
echo "[1] 检查服务配置文件..."
if [ -f "$SERVICE_FILE" ]; then
    echo -e "  ${GREEN}✅ 服务文件存在: $SERVICE_FILE${NC}"
else
    echo -e "  ${RED}❌ 服务文件不存在: $SERVICE_FILE${NC}"
    echo "  请先运行部署脚本创建服务文件"
    exit 1
fi
echo ""

# 2. 检查项目目录
echo "[2] 检查项目目录..."
if [ -d "$PROJECT_DIR" ]; then
    echo -e "  ${GREEN}✅ 项目目录存在: $PROJECT_DIR${NC}"
else
    echo -e "  ${RED}❌ 项目目录不存在: $PROJECT_DIR${NC}"
    exit 1
fi

if [ -d "$BACKEND_DIR" ]; then
    echo -e "  ${GREEN}✅ 后端目录存在: $BACKEND_DIR${NC}"
else
    echo -e "  ${RED}❌ 后端目录不存在: $BACKEND_DIR${NC}"
    exit 1
fi
echo ""

# 3. 检查 .env 文件
echo "[3] 检查 .env 文件..."
ENV_FILE="$BACKEND_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "  ${GREEN}✅ .env 文件存在: $ENV_FILE${NC}"
    echo "  文件权限:"
    ls -la "$ENV_FILE" | awk '{print "    " $0}'
    echo "  文件内容（前5行，隐藏敏感信息）:"
    head -5 "$ENV_FILE" | sed 's/=.*/=***/' | awk '{print "    " $0}'
else
    echo -e "  ${RED}❌ .env 文件不存在: $ENV_FILE${NC}"
    echo -e "  ${YELLOW}⚠️  这是导致服务启动失败的主要原因！${NC}"
    echo ""
    echo "  创建 .env 文件..."
    cat > "$ENV_FILE" << 'EOF'
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["http://localhost:3000"]
EOF
    chmod 600 "$ENV_FILE"
    chown ubuntu:ubuntu "$ENV_FILE"
    echo -e "  ${GREEN}✅ 已创建默认 .env 文件${NC}"
    echo -e "  ${YELLOW}⚠️  请编辑 $ENV_FILE 添加正确的配置${NC}"
fi
echo ""

# 4. 检查虚拟环境
echo "[4] 检查虚拟环境..."
VENV_DIR="$BACKEND_DIR/venv"
if [ -d "$VENV_DIR" ]; then
    echo -e "  ${GREEN}✅ 虚拟环境目录存在: $VENV_DIR${NC}"
    
    # 检查 uvicorn
    UVCORN_PATH="$VENV_DIR/bin/uvicorn"
    if [ -f "$UVCORN_PATH" ]; then
        echo -e "  ${GREEN}✅ uvicorn 存在: $UVCORN_PATH${NC}"
    else
        echo -e "  ${RED}❌ uvicorn 不存在: $UVCORN_PATH${NC}"
        echo "  请运行: cd $BACKEND_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi
    
    # 检查 Python
    PYTHON_PATH="$VENV_DIR/bin/python3"
    if [ -f "$PYTHON_PATH" ]; then
        echo -e "  ${GREEN}✅ Python 存在: $PYTHON_PATH${NC}"
        echo "  Python 版本:"
        "$PYTHON_PATH" --version | awk '{print "    " $0}'
    else
        echo -e "  ${RED}❌ Python 不存在: $PYTHON_PATH${NC}"
    fi
else
    echo -e "  ${RED}❌ 虚拟环境目录不存在: $VENV_DIR${NC}"
    echo "  请运行: cd $BACKEND_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi
echo ""

# 5. 检查服务配置中的路径
echo "[5] 检查服务配置中的路径..."
echo "  从服务文件读取的配置:"
grep -E "WorkingDirectory|ExecStart|EnvironmentFile|User" "$SERVICE_FILE" | awk '{print "    " $0}'
echo ""

# 验证路径是否存在
WORKING_DIR=$(grep "^WorkingDirectory=" "$SERVICE_FILE" | cut -d'=' -f2)
EXEC_START=$(grep "^ExecStart=" "$SERVICE_FILE" | cut -d'=' -f2 | awk '{print $1}')
ENV_FILE_CONFIG=$(grep "^EnvironmentFile=" "$SERVICE_FILE" | cut -d'=' -f2)

if [ -d "$WORKING_DIR" ]; then
    echo -e "  ${GREEN}✅ WorkingDirectory 存在: $WORKING_DIR${NC}"
else
    echo -e "  ${RED}❌ WorkingDirectory 不存在: $WORKING_DIR${NC}"
fi

if [ -f "$EXEC_START" ]; then
    echo -e "  ${GREEN}✅ ExecStart 文件存在: $EXEC_START${NC}"
else
    echo -e "  ${RED}❌ ExecStart 文件不存在: $EXEC_START${NC}"
fi

if [ -f "$ENV_FILE_CONFIG" ]; then
    echo -e "  ${GREEN}✅ EnvironmentFile 存在: $ENV_FILE_CONFIG${NC}"
else
    echo -e "  ${RED}❌ EnvironmentFile 不存在: $ENV_FILE_CONFIG${NC}"
fi
echo ""

# 6. 检查 Python 语法
echo "[6] 检查 Python 语法..."
if [ -f "$BACKEND_DIR/app/api/group_ai/servers.py" ]; then
    if "$PYTHON_PATH" -m py_compile "$BACKEND_DIR/app/api/group_ai/servers.py" 2>&1; then
        echo -e "  ${GREEN}✅ servers.py 语法正确${NC}"
    else
        echo -e "  ${RED}❌ servers.py 有语法错误${NC}"
        "$PYTHON_PATH" -m py_compile "$BACKEND_DIR/app/api/group_ai/servers.py" 2>&1 || true
    fi
else
    echo -e "  ${YELLOW}⚠️  servers.py 文件不存在${NC}"
fi
echo ""

# 7. 检查服务状态
echo "[7] 检查服务状态..."
systemctl status luckyred-api --no-pager -l | head -20 || true
echo ""

# 8. 查看服务日志
echo "[8] 查看服务日志（最后 30 行）..."
journalctl -u luckyred-api -n 30 --no-pager || true
echo ""

# 9. 检查端口占用
echo "[9] 检查端口占用..."
if ss -tlnp | grep -q ':8000'; then
    echo -e "  ${YELLOW}⚠️  端口 8000 已被占用:${NC}"
    ss -tlnp | grep ':8000' | awk '{print "    " $0}'
else
    echo -e "  ${GREEN}✅ 端口 8000 未被占用${NC}"
fi
echo ""

# 10. 检查权限
echo "[10] 检查文件权限..."
if [ -d "$BACKEND_DIR" ]; then
    OWNER=$(stat -c '%U:%G' "$BACKEND_DIR")
    echo "  后端目录所有者: $OWNER"
    if [ "$OWNER" = "ubuntu:ubuntu" ]; then
        echo -e "  ${GREEN}✅ 权限正确${NC}"
    else
        echo -e "  ${YELLOW}⚠️  权限可能不正确，建议运行: sudo chown -R ubuntu:ubuntu $BACKEND_DIR${NC}"
    fi
fi
echo ""

# 总结
echo "============================================================"
echo "📊 诊断总结"
echo "============================================================"
echo ""

# 检查关键问题
ISSUES=0

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ 问题 1: .env 文件不存在${NC}"
    ISSUES=$((ISSUES + 1))
fi

if [ ! -f "$UVCORN_PATH" ]; then
    echo -e "${RED}❌ 问题 2: uvicorn 不存在${NC}"
    ISSUES=$((ISSUES + 1))
fi

if [ ! -f "$EXEC_START" ]; then
    echo -e "${RED}❌ 问题 3: ExecStart 路径不存在${NC}"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ 所有关键检查通过${NC}"
    echo ""
    echo "如果服务仍然无法启动，请查看上面的日志获取详细信息"
    echo ""
    echo "尝试手动启动测试:"
    echo "  cd $BACKEND_DIR"
    echo "  source venv/bin/activate"
    echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000"
else
    echo ""
    echo -e "${YELLOW}⚠️  发现 $ISSUES 个问题，请先修复这些问题${NC}"
fi

echo ""
echo "============================================================"

