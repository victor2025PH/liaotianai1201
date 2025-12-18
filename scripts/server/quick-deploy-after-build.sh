#!/bin/bash
# ============================================================
# 构建完成后的快速部署脚本
# ============================================================
# 
# 功能：
# 1. 创建/检查 ecosystem.config.js
# 2. 启动 PM2 服务
# 3. 配置 PM2 开机自启
# 4. 验证服务状态
# 
# 使用方法：
#   chmod +x scripts/server/quick-deploy-after-build.sh
#   sudo -u deployer bash scripts/server/quick-deploy-after-build.sh
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
step_msg() { echo -e "${BLUE}📌 $1${NC}"; }

# 配置变量
PROJECT_DIR="/home/deployer/telegram-ai-system"
ECOSYSTEM_FILE="$PROJECT_DIR/ecosystem.config.js"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 快速部署脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查是否为 deployer 用户
if [ "$USER" != "deployer" ]; then
    error_msg "请使用 deployer 用户运行此脚本"
    info_msg "使用方法: sudo -u deployer bash $0"
    exit 1
fi

# 进入项目目录
cd "$PROJECT_DIR" || {
    error_msg "无法进入项目目录: $PROJECT_DIR"
    exit 1
}

# ============================================================
# 步骤 1: 创建 ecosystem.config.js
# ============================================================
step_msg "步骤 1/4: 检查 ecosystem.config.js..."

# 检查文件是否存在，以及是否包含正确的路径
NEED_RECREATE=false

if [ -f "$ECOSYSTEM_FILE" ]; then
    # 检查是否包含错误的路径（/home/ubuntu）
    if grep -q "/home/ubuntu" "$ECOSYSTEM_FILE"; then
        info_msg "ecosystem.config.js 存在但包含错误的路径 (/home/ubuntu)，需要重新创建"
        NEED_RECREATE=true
        # 备份旧文件
        mv "$ECOSYSTEM_FILE" "${ECOSYSTEM_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    elif grep -q "/home/deployer" "$ECOSYSTEM_FILE"; then
        info_msg "ecosystem.config.js 已存在且路径正确"
    else
        info_msg "ecosystem.config.js 存在但路径不明确，重新创建以确保正确"
        NEED_RECREATE=true
        mv "$ECOSYSTEM_FILE" "${ECOSYSTEM_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
else
    NEED_RECREATE=true
fi

if [ "$NEED_RECREATE" = true ]; then
    info_msg "创建 ecosystem.config.js..."
    cat > "$ECOSYSTEM_FILE" << 'EOF'
module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "/home/deployer/telegram-ai-system/admin-backend",
      script: "/home/deployer/telegram-ai-system/admin-backend/venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        PORT: 8000,
        PYTHONPATH: "/home/deployer/telegram-ai-system/admin-backend",
        PYTHONUNBUFFERED: "1",
        NODE_ENV: "production"
      },
      error_file: "/home/deployer/telegram-ai-system/logs/backend-error.log",
      out_file: "/home/deployer/telegram-ai-system/logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      instances: 1,
      exec_mode: "fork"
    },
    {
      name: "frontend",
      cwd: "/home/deployer/telegram-ai-system/saas-demo",
      script: "/usr/bin/node",
      args: ".next/standalone/server.js",
      env: {
        PORT: 3000,
        NODE_ENV: "production",
        NODE_OPTIONS: "--max-old-space-size=1024"
      },
      error_file: "/home/deployer/telegram-ai-system/logs/frontend-error.log",
      out_file: "/home/deployer/telegram-ai-system/logs/frontend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      instances: 1,
      exec_mode: "fork"
    }
  ]
};
EOF
    
    # 验证配置文件语法
    if node -c "$ECOSYSTEM_FILE" 2>/dev/null; then
        success_msg "ecosystem.config.js 创建成功"
    else
        error_msg "ecosystem.config.js 语法错误"
        exit 1
    fi
fi

# ============================================================
# 步骤 2: 停止旧服务（如果存在）
# ============================================================
step_msg "步骤 2/4: 检查并停止旧服务..."

if pm2 list | grep -q "backend\|frontend"; then
    info_msg "发现现有 PM2 服务，正在停止..."
    pm2 stop all 2>/dev/null || true
    pm2 delete all 2>/dev/null || true
    success_msg "旧服务已停止"
else
    info_msg "未发现现有服务"
fi

# ============================================================
# 步骤 3: 启动 PM2 服务
# ============================================================
step_msg "步骤 3/4: 启动 PM2 服务..."

# 确保日志目录存在
mkdir -p "$PROJECT_DIR/logs"

# 启动服务
pm2 start "$ECOSYSTEM_FILE"

# 等待服务启动
sleep 5

# 检查服务状态
if pm2 list | grep -q "backend.*online"; then
    success_msg "后端服务已启动"
else
    error_msg "后端服务启动失败"
    pm2 logs backend --err --lines 20
    exit 1
fi

if pm2 list | grep -q "frontend.*online"; then
    success_msg "前端服务已启动"
else
    error_msg "前端服务启动失败"
    pm2 logs frontend --err --lines 20
    exit 1
fi

# ============================================================
# 步骤 4: 配置 PM2 开机自启
# ============================================================
step_msg "步骤 4/4: 配置 PM2 开机自启..."

# 保存 PM2 进程列表
pm2 save

# 检查是否已配置开机自启
if pm2 startup 2>&1 | grep -q "already setup"; then
    info_msg "PM2 开机自启已配置"
else
    info_msg "需要配置 PM2 开机自启"
    STARTUP_CMD=$(pm2 startup | grep "sudo")
    if [ -n "$STARTUP_CMD" ]; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "⚠️  请执行以下命令配置开机自启："
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$STARTUP_CMD"
        echo ""
        echo "然后重新运行此脚本或执行: pm2 save"
        echo ""
    fi
fi

# ============================================================
# 验证服务状态
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 服务状态验证"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# PM2 状态
echo "PM2 服务列表："
pm2 status
echo ""

# 端口监听检查
echo "端口监听状态："
if ss -tlnp 2>/dev/null | grep -q ":3000"; then
    success_msg "端口 3000 (前端) 正在监听"
else
    error_msg "端口 3000 (前端) 未监听"
fi

if ss -tlnp 2>/dev/null | grep -q ":8000"; then
    success_msg "端口 8000 (后端) 正在监听"
else
    error_msg "端口 8000 (后端) 未监听"
fi
echo ""

# 健康检查
echo "服务健康检查："
if curl -s http://localhost:8000/health >/dev/null 2>&1 || curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
    success_msg "后端健康检查通过"
else
    info_msg "后端健康检查失败（可能端点不同）"
fi

if curl -s -I http://localhost:3000 | head -1 | grep -q "200\|301\|302"; then
    success_msg "前端服务响应正常"
else
    error_msg "前端服务响应异常"
fi
echo ""

# ============================================================
# 完成
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success_msg "部署完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "常用命令："
echo "  查看服务状态: pm2 status"
echo "  查看日志:     pm2 logs"
echo "  重启服务:     pm2 restart all"
echo "  停止服务:     pm2 stop all"
echo ""
echo "下一步："
echo "  1. 配置 Nginx: 参考 docs/DEPLOYMENT_COMPLETE_GUIDE.md"
echo "  2. 配置 GitHub Actions: 参考 docs/SETUP_GITHUB_ACTIONS_SSH.md"
echo ""
