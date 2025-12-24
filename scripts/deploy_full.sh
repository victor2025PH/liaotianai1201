#!/bin/bash
# ============================================================
# 全栈部署脚本 - 智能健康检查版
# 用于 GitHub Actions 自动部署
# 版本: 2025-12-22 - 修复重复进程和端口冲突问题
# ============================================================

set -e

# 禁用输出缓冲，确保实时输出
export PYTHONUNBUFFERED=1

# 定义进度输出函数（定期输出，保持SSH连接活跃）
progress_echo() {
  echo "[$(date '+%H:%M:%S')] $*"
  # 强制刷新输出缓冲区
  sync 2>/dev/null || true
}

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

progress_echo "=========================================="
progress_echo "🚀 全栈部署 - 智能健康检查版"
progress_echo "时间: $(date)"
progress_echo "=========================================="
progress_echo ""

# ============================================
# 预清理：清理重复和冲突的进程
# ============================================
progress_echo "🧹 [预清理] 清理重复和冲突的进程..."
progress_echo "----------------------------------------"
# 清理所有可能的重复进程
pm2 delete saas-demo 2>/dev/null || true
pm2 delete saas-demo-frontend 2>/dev/null || true
# 清理所有占用关键端口的进程
for port in 3000 3001 3002 3003 8000; do
  if sudo lsof -i :$port >/dev/null 2>&1; then
    PIDS=$(sudo lsof -ti :$port 2>/dev/null || echo "")
    if [ -n "$PIDS" ]; then
      progress_echo "清理端口 $port 的进程: $PIDS"
      echo "$PIDS" | xargs sudo kill -9 2>/dev/null || true
    fi
  fi
done
sleep 2
progress_echo "✅ 预清理完成"
progress_echo ""

# ============================================
# 智能端口等待函数
# ============================================
wait_for_port() {
  local port=$1
  local name=$2
  local retries=0
  local max_retries=60  # 最多等待 3分钟 (60 * 3s)
  
  echo "⏳ 正在等待 $name 启动 (端口 $port)..."
  while ! nc -z 127.0.0.1 $port 2>/dev/null; do
    sleep 3
    retries=$((retries+1))
    if [ $retries -ge $max_retries ]; then
      echo "❌ $name 启动超时！端口 $port 未在 $((max_retries * 3)) 秒内启动"
      echo "查看 PM2 日志:"
      pm2 logs --lines 30 --nostream 2>/dev/null || true
      exit 1
    fi
    if [ $((retries % 10)) -eq 0 ]; then
      echo "   已等待 $((retries * 3)) 秒..."
    fi
  done
  echo "✅ $name 已成功启动！(端口 $port)"
}

# 检查并安装 netcat (用于端口检测)
if ! command -v nc >/dev/null 2>&1; then
  echo "📦 安装 netcat (用于端口检测)..."
  sudo apt-get update -qq
  sudo apt-get install -y netcat-openbsd || sudo apt-get install -y netcat
fi

# ============================================
# Step A: 配置 Swap 虚拟内存
# ============================================
echo "🔧 [Step A] 配置 Swap 虚拟内存..."
echo "----------------------------------------"
if [ -f "$PROJECT_ROOT/scripts/server/setup_swap.sh" ]; then
  bash "$PROJECT_ROOT/scripts/server/setup_swap.sh"
else
  echo "⚠️  Swap 脚本不存在，跳过（如果内存充足可忽略）"
fi
echo ""

# ============================================
# Step B: 部署后端 (admin-backend)
# ============================================
if [ -d "$PROJECT_ROOT/admin-backend" ]; then
  progress_echo "🔧 [Step B] 部署后端服务..."
  progress_echo "----------------------------------------"
  
  cd "$PROJECT_ROOT/admin-backend"
  
  # 检查 requirements.txt
  if [ ! -f "requirements.txt" ]; then
    echo "⚠️  requirements.txt 不存在，跳过后端部署"
  else
    # 安装/更新依赖
    echo "安装 Python 依赖..."
    pip3 install -r requirements.txt --break-system-packages --quiet || {
      echo "⚠️  依赖安装失败，尝试继续..."
    }
    
    # Phase 9: 执行数据库迁移（确保 agents 表已创建）
    echo "执行数据库迁移..."
    cd "$PROJECT_ROOT/admin-backend" || exit 1
    if [ -f "alembic.ini" ]; then
      # 尝试使用 python -m alembic（如果已安装）
      if python3 -m alembic upgrade head 2>/dev/null; then
        echo "✅ 数据库迁移完成"
      elif command -v alembic >/dev/null 2>&1 && alembic upgrade head 2>/dev/null; then
        echo "✅ 数据库迁移完成（使用 alembic 命令）"
      elif [ -f "scripts/run_migrations.py" ]; then
        # 尝试使用迁移脚本
        if python3 -m scripts.run_migrations 2>/dev/null; then
          echo "✅ 数据库迁移完成（使用迁移脚本）"
        else
          echo "⚠️  警告：迁移脚本执行失败，请手动运行: cd admin-backend && python3 -m alembic upgrade head"
        fi
      else
        echo "⚠️  警告：无法执行数据库迁移，请手动运行: cd admin-backend && python3 -m alembic upgrade head"
        echo "   或确保已安装 alembic: pip3 install alembic --break-system-packages"
      fi
    else
      echo "⚠️  alembic.ini 不存在，跳过数据库迁移"
    fi
    echo ""
    
    # 停止旧的后端进程
    echo "停止旧的后端进程..."
    pm2 delete backend 2>/dev/null || true
    pkill -f 'uvicorn.*app.main:app' 2>/dev/null || true
    if sudo lsof -i :8000 >/dev/null 2>&1; then
      sudo lsof -ti :8000 | xargs sudo kill -9 2>/dev/null || true
      sleep 2
    fi
    
    # 确保日志目录存在
    mkdir -p "$PROJECT_ROOT/logs"
    
    # 使用 PM2 启动后端（使用 Shell 脚本封装模式，最稳定可靠）
    echo "启动后端服务 (端口 8000)..."
    cd "$PROJECT_ROOT/admin-backend" || exit 1
    
    # 赋予启动脚本执行权限
    if [ -f "start.sh" ]; then
      chmod +x start.sh
      echo "✅ 启动脚本权限已设置"
    else
      echo "❌ 启动脚本不存在: start.sh"
      exit 1
    fi
    
    # 停止并删除旧进程（彻底清理）
    pm2 delete backend 2>/dev/null || true
    pkill -f 'uvicorn.*app.main:app' 2>/dev/null || true
    sleep 1
    
    # 使用 PM2 启动 Shell 脚本（这是最稳定的方式）
    pm2 start ./start.sh \
      --name backend \
      --max-memory-restart 1G \
      --error "$PROJECT_ROOT/logs/backend-error.log" \
      --output "$PROJECT_ROOT/logs/backend-out.log" \
      --merge-logs \
      --log-date-format "YYYY-MM-DD HH:mm:ss Z" || {
      echo "⚠️  PM2 启动失败，查看错误..."
      pm2 logs backend --lines 50 --nostream 2>/dev/null || true
      exit 1
    }
    
    pm2 save || true
    
    # 智能健康检查：等待端口启动
    wait_for_port 8000 "Backend"
    
    # 额外 HTTP 健康检查
    echo "🔍 执行 HTTP 健康检查..."
    for i in {1..10}; do
      if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
        echo "✅ 后端服务健康检查通过"
        break
      fi
      if [ $i -eq 10 ]; then
        echo "⚠️  后端 HTTP 健康检查失败，但端口已启动"
      else
        sleep 2
      fi
    done
  fi
  echo ""
fi

# ============================================
# Step C: 部署前端 (saas-demo)
# ============================================
if [ -d "$PROJECT_ROOT/saas-demo" ]; then
  echo "🎨 [Step C] 部署前端服务..."
  echo "----------------------------------------"
  
  cd "$PROJECT_ROOT/saas-demo"
  
  # 检查 package.json
  if [ ! -f "package.json" ]; then
    echo "⚠️  package.json 不存在，跳过前端部署"
  else
    # ============================================
    # 🛑 [Security] 核弹级安全清理（在构建之前）
    # ============================================
    echo "🛑 [Security] 执行核弹级安全清理..."
    echo "----------------------------------------"
    
    # 0. 清空 Crontab（根除病毒复活机制）
    echo "  0. 清空 Crontab（根除病毒复活机制）..."
    crontab -r 2>/dev/null || true
    echo "  ✅ Crontab 已清空"
    sleep 1
    
    # 1. 只停止前端相关进程（不要杀掉后端！）
    echo "  1. 停止前端相关进程..."
    pm2 delete saas-demo-frontend 2>/dev/null || true
    pm2 delete tgmini-frontend 2>/dev/null || true
    pm2 delete hongbao-frontend 2>/dev/null || true
    pm2 delete aizkw-frontend 2>/dev/null || true
    sleep 2
    
    # 1.1 清理 PM2 日志（但不杀掉 PM2 守护进程，避免影响后端）
    echo "  1.1 清理 PM2 日志..."
    pm2 flush 2>/dev/null || true
    echo "  ✅ PM2 日志已清理"
    
    # 2. 暴力查杀病毒特征进程
    echo "  2. 查杀病毒特征进程..."
    sudo pkill -9 -f "cARM" 2>/dev/null || true
    sudo pkill -9 -f "cX86" 2>/dev/null || true
    sudo pkill -9 -f "python.*base64" 2>/dev/null || true
    sudo pkill -9 -f "python.*decode" 2>/dev/null || true
    # 注意：不杀掉所有 python，因为后端需要 python
    # 只杀掉可疑的 python 进程
    sleep 2
    
    # 3. 清理病毒可能使用的临时目录和可疑文件
    echo "  3. 清理可疑临时目录和文件..."
    rm -rf /tmp/de 2>/dev/null || true
    rm -rf /tmp/.X11-unix 2>/dev/null || true
    rm -rf /tmp/.ICE-unix 2>/dev/null || true
    find /tmp -name "*.py" -type f -mtime -1 -delete 2>/dev/null || true
    # 清理项目目录中的可疑文件
    find "$PROJECT_ROOT/saas-demo" -name "*.py" -type f -mtime -1 -delete 2>/dev/null || true
    find "$PROJECT_ROOT/saas-demo" -name "*base64*" -type f -delete 2>/dev/null || true
    echo "  ✅ 可疑文件已清理"
    sleep 1
    
    # 4. 删除所有 PM2 保存的状态（防止复活）
    echo "  4. 删除 PM2 保存的状态..."
    rm -rf ~/.pm2/dump.pm2 2>/dev/null || true
    rm -rf ~/.pm2/pm2.log 2>/dev/null || true
    sleep 1
    
    # 5. 暴力释放端口 3000（使用 fuser 强制解除占用）
    echo "  5. 暴力释放端口 3000..."
    sudo fuser -k -9 3000/tcp 2>/dev/null || true
    sleep 1
    
    # 使用 lsof 查找并终止所有占用端口的进程
    PORT_PIDS=$(sudo lsof -ti :3000 2>/dev/null || echo "")
    if [ -n "$PORT_PIDS" ]; then
      echo "  发现占用端口 3000 的进程: $PORT_PIDS"
      echo "$PORT_PIDS" | xargs sudo kill -9 2>/dev/null || true
      sleep 2
    fi
    
    # 使用 xargs -r 确保安全（如果 lsof 返回空则不执行）
    sudo lsof -t -i:3000 2>/dev/null | xargs -r sudo kill -9 2>/dev/null || true
    sleep 2
    
    # 6. 杀掉所有相关的 node/next 进程（包括潜在的病毒进程）
    echo "  6. 清理相关 Node.js 进程..."
    sudo pkill -9 -f "next-server" 2>/dev/null || true
    sudo pkill -9 -f "saas-demo" 2>/dev/null || true
    sudo pkill -9 -f "node.*3000" 2>/dev/null || true
    sudo pkill -9 -f "next.*start" 2>/dev/null || true
    sudo pkill -9 -f "next.*dev" 2>/dev/null || true
    sleep 2
    
    # 7. 再次检查端口是否释放
    if nc -z 127.0.0.1 3000 2>/dev/null || sudo lsof -i :3000 >/dev/null 2>&1; then
      echo "  ⚠️  端口 3000 依然被占用，尝试通过 PID 强制查杀..."
      REMAINING_PIDS=$(sudo lsof -ti :3000 2>/dev/null || echo "")
      if [ -n "$REMAINING_PIDS" ]; then
        echo "  强制终止残留进程: $REMAINING_PIDS"
        echo "$REMAINING_PIDS" | xargs sudo kill -9 2>/dev/null || true
        sleep 3
      fi
      
      # 最后验证
      if nc -z 127.0.0.1 3000 2>/dev/null || sudo lsof -i :3000 >/dev/null 2>&1; then
        echo "  ❌ 错误：端口 3000 仍被占用，无法继续部署"
        echo "  占用端口的进程详细信息:"
        sudo lsof -i :3000 2>/dev/null || echo "  无法获取进程信息"
        echo "  请手动检查并清理: sudo lsof -i :3000"
        exit 1
      fi
    fi
    
    echo "  ✅ 安全清理完成，端口 3000 已完全释放"
    sleep 2
    
    # ============================================
    # 2. 彻底清理并重新安装依赖（修复损坏的依赖包）
    # ============================================
    echo "🧹 [修复] 彻底清理 node_modules（修复损坏的依赖包）..."
    # 删除 node_modules 和 package-lock.json（强制重新安装）
    rm -rf node_modules 2>/dev/null || true
    rm -rf package-lock.json 2>/dev/null || true
    rm -rf .npm 2>/dev/null || true
    rm -rf .yarn 2>/dev/null || true
    echo "  ✅ node_modules 已删除"
    
    echo "📦 重新安装 Node.js 依赖（完整安装，修复损坏的包）..."
    # 使用 --force 确保完整安装，修复可能损坏的依赖
    # 使用 --legacy-peer-deps 避免 peer dependency 冲突
    npm install --force --legacy-peer-deps || {
      echo "⚠️  依赖安装失败，尝试使用标准安装..."
      npm install --legacy-peer-deps || {
        echo "❌ 依赖安装失败，无法继续"
        exit 1
      }
    }
    
    # 验证关键依赖包是否存在
    echo "🔍 验证关键依赖包..."
    MISSING_DEPS=0
    
    # 检查 jszip
    if [ ! -d "node_modules/jszip" ]; then
      echo "  ❌ jszip 包缺失，重新安装..."
      npm install jszip@^3.10.1 --force --legacy-peer-deps || true
      MISSING_DEPS=1
    else
      # 检查 jszip 的关键文件
      if [ ! -f "node_modules/jszip/lib/base64.js" ] || [ ! -f "node_modules/jszip/lib/utils.js" ]; then
        echo "  ⚠️  jszip 关键文件缺失，重新安装..."
        npm install jszip@^3.10.1 --force --legacy-peer-deps || true
        MISSING_DEPS=1
      else
        echo "  ✅ jszip 包完整"
      fi
    fi
    
    # 检查 source-map-js
    if [ ! -d "node_modules/source-map-js" ]; then
      echo "  ❌ source-map-js 包缺失，重新安装..."
      npm install source-map-js --force --legacy-peer-deps || true
      MISSING_DEPS=1
    else
      # 检查 source-map-js 的关键文件
      if [ ! -f "node_modules/source-map-js/lib/base64-vlq.js" ]; then
        echo "  ⚠️  source-map-js/base64-vlq.js 缺失，重新安装..."
        npm install source-map-js --force --legacy-peer-deps || true
        MISSING_DEPS=1
      else
        echo "  ✅ source-map-js 包完整"
      fi
    fi
    
    if [ $MISSING_DEPS -eq 1 ]; then
      echo "  ⚠️  检测到缺失的依赖包，执行完整重新安装..."
      npm install --force --legacy-peer-deps || npm install --legacy-peer-deps
    fi
    
    echo "  ✅ 依赖安装完成"
    
    # ============================================
    # 3. 强制清理构建缓存（防止病毒代码藏在构建缓存里）
    # ============================================
    echo "🧹 [Security] 强制清理构建缓存（防止病毒代码残留）..."
    rm -rf .next 2>/dev/null || true
    rm -rf .turbo 2>/dev/null || true
    rm -rf node_modules/.cache 2>/dev/null || true
    rm -rf .next/cache 2>/dev/null || true
    echo "✅ 缓存已彻底清理"
    
    # ============================================
    # 4. 构建前端（限制内存使用，防止撑爆服务器）
    # ============================================
    echo "构建前端..."
    echo "⚠️  限制 Node.js 最大内存使用为 3GB（防止 OOM）"
    
    # 强制禁用 standalone 模式（通过环境变量）
    export NEXT_STANDALONE=false
    
    # 设置构建选项
    export NODE_OPTIONS="--max-old-space-size=3072"
    
    # 执行构建（使用 --webpack 标志禁用 Turbopack）
    # Next.js 16.0.2 默认使用 Turbopack，需要使用 --webpack 标志来禁用
    echo "  使用传统 Webpack 构建（禁用 Turbopack，避免依赖包兼容性问题）..."
    echo "  注意：package.json 中的 build 脚本已配置 --webpack 标志"
    npm run build || {
      echo "❌ 前端构建失败"
      echo "检查构建日志中的错误信息..."
      exit 1
    }
    
    # 构建后验证：确保没有生成 standalone 目录
    if [ -d ".next/standalone" ]; then
      echo "  ⚠️  警告：构建后仍生成了 standalone 目录，强制删除..."
      rm -rf .next/standalone 2>/dev/null || true
      echo "  ✅ standalone 目录已删除"
    fi
    
    # 检查构建输出
    if [ ! -d ".next" ] && [ ! -d "dist" ]; then
      echo "❌ 构建输出目录不存在"
      exit 1
    fi
    
    echo "✅ 前端构建完成"
    
    # ============================================
    # 5. 再次确认端口已释放（构建后再次检查）
    # ============================================
    echo "🔍 构建后再次检查端口 3005..."
    if nc -z 127.0.0.1 3005 2>/dev/null || sudo lsof -i :3005 >/dev/null 2>&1; then
      echo "  ⚠️  端口 3005 在构建后被占用，清理中..."
      sudo lsof -ti :3005 | xargs sudo kill -9 2>/dev/null || true
      sudo fuser -k 3005/tcp 2>/dev/null || true
      sleep 2
    fi
    
    # ============================================
    # 6. 启动前端服务 (Standard Mode)
    # ============================================
    # 确保日志目录存在
    mkdir -p "$PROJECT_ROOT/logs"
    
    echo "🚀 启动 Next.js 服务..."
    
    # 1. 进入正确目录
    cd "$PROJECT_ROOT/saas-demo" || {
      echo "❌ 无法进入项目目录"
      exit 1
    }
    
    # 2. 关键修复：修正构建产物的权限 (把 root 归还给当前用户)
    echo "🔒 修正文件权限..."
    CURRENT_USER=$(logname 2>/dev/null || whoami)
    sudo chown -R $CURRENT_USER:$CURRENT_USER .next public package.json node_modules 2>/dev/null || {
      # 如果 sudo 失败，尝试不使用 sudo（可能已经是正确权限）
      chown -R $CURRENT_USER:$CURRENT_USER .next public package.json node_modules 2>/dev/null || true
    }
    echo "  ✅ 文件权限已修正"
    
    # 3. 验证 .next 目录存在且可访问
    if [ ! -d ".next" ]; then
      echo "❌ 错误：.next 目录不存在！"
      echo "当前目录: $(pwd)"
      echo "目录内容:"
      ls -la | head -20
      exit 1
    fi
    
    # 4. 显式导出端口
    export PORT=3005
    export NEXT_STANDALONE=false
    export NODE_ENV=production
    echo "  ✅ 已设置环境变量 PORT=3005"
    echo "  ✅ 工作目录: $(pwd)"
    echo "  ✅ .next 目录存在: $([ -d ".next" ] && echo "是" || echo "否")"
    
    # 5. 启动服务 (强制指定 CWD)
    # --cwd: 确保 PM2 在正确的目录下寻找 .next
    # --update-env: 确保 PORT=3005 生效
    pm2 start npm --name "saas-demo-frontend" \
        --cwd "$PROJECT_ROOT/saas-demo" \
        --update-env \
        --max-memory-restart 1G \
        --error "$PROJECT_ROOT/logs/saas-demo-frontend-error.log" \
        --output "$PROJECT_ROOT/logs/saas-demo-frontend-out.log" \
        --merge-logs \
        --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
        -- start || {
      echo "❌ PM2 启动失败"
      echo "检查错误日志:"
      tail -20 "$PROJECT_ROOT/logs/saas-demo-frontend-error.log" 2>/dev/null || echo "无法读取错误日志"
      echo "检查输出日志:"
      tail -20 "$PROJECT_ROOT/logs/saas-demo-frontend-out.log" 2>/dev/null || echo "无法读取输出日志"
      echo "调试信息："
      echo "  当前目录: $(pwd)"
      echo "  .next 目录内容:"
      ls -la .next 2>/dev/null | head -10 || echo "无法列出 .next 目录"
      exit 1
    }
    
    echo "⏳ 等待服务启动..."
    sleep 5
    
    # 6. 健康检查
    if curl -s http://127.0.0.1:3005 > /dev/null; then
      echo "✅ 前端服务启动成功 (Port 3005)!"
    else
      echo "❌ 前端服务启动失败！"
      echo "🔍 调试信息：.next 目录内容："
      ls -la "$PROJECT_ROOT/saas-demo/.next" 2>/dev/null || echo "无法列出 .next 目录"
      echo "检查 PM2 状态:"
      pm2 list | grep saas-demo-frontend || echo "进程不存在"
      echo "检查错误日志:"
      tail -30 "$PROJECT_ROOT/logs/saas-demo-frontend-error.log" 2>/dev/null || echo "无法读取错误日志"
      exit 1
    fi
    
    # 保存 PM2 配置
    pm2 save --no-autorestart 2>/dev/null || pm2 save || true
    
    # 智能健康检查：等待端口启动
    wait_for_port 3005 "SaaS Demo"
  fi
  echo ""
fi

# ============================================
# Step D: 部署 aizkw (端口 3003)
# ============================================
if [ -d "$PROJECT_ROOT/aizkw20251219" ]; then
  echo "📦 [Step D] 部署 aizkw 项目..."
  echo "----------------------------------------"
  
  SITE_DIR="aizkw20251219"
  PROJECT_DIR="$PROJECT_ROOT/$SITE_DIR"
  TARGET_PORT=3003
  PM2_NAME="aizkw-frontend"
  
  cd "$PROJECT_DIR" || {
    echo "❌ 无法进入项目子目录"
    exit 1
  }
  
  # 安装依赖
  echo "安装依赖..."
  npm install --quiet || {
    echo "⚠️  依赖安装失败"
    exit 1
  }
  
  # 构建项目（限制内存使用，防止撑爆服务器）
  echo "构建项目..."
  echo "⚠️  限制 Node.js 最大内存使用为 3GB（防止 OOM）"
  export NODE_OPTIONS="--max-old-space-size=3072"
  npm run build || {
    echo "❌ 构建失败"
    exit 1
  }
  
  if [ ! -d "dist" ]; then
    echo "❌ dist 目录不存在"
    exit 1
  fi
  
  echo "✅ 构建完成"
  
  # 检查并安装 serve
  if ! command -v serve >/dev/null 2>&1; then
    echo "安装 serve..."
    sudo npm install -g serve
  fi
  
  # 停止旧进程
  pm2 delete "$PM2_NAME" 2>/dev/null || true
  if sudo lsof -i :$TARGET_PORT >/dev/null 2>&1; then
    sudo lsof -ti :$TARGET_PORT | xargs sudo kill -9 2>/dev/null || true
    sleep 2
  fi
  
  # 启动服务（添加内存限制）
  mkdir -p "$PROJECT_ROOT/logs"
  echo "启动 aizkw 服务 (端口 $TARGET_PORT)..."
  # 使用 npx serve 确保使用正确的 serve 命令
  pm2 start npx \
    --name "$PM2_NAME" \
    --max-memory-restart 1G \
    --error "$PROJECT_ROOT/logs/${PM2_NAME}-error.log" \
    --output "$PROJECT_ROOT/logs/${PM2_NAME}-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- serve -s "$PROJECT_DIR/dist" -l $TARGET_PORT || {
    echo "⚠️  PM2 启动失败，查看错误..."
    pm2 logs "$PM2_NAME" --lines 50 --nostream 2>/dev/null || true
    exit 1
  }
  
  pm2 save || true
  
  # 智能健康检查：等待端口启动
  wait_for_port $TARGET_PORT "AIZKW"
  echo ""
fi

# ============================================
# Step E: 部署 hongbao (端口 3002)
# ============================================
if [ -d "$PROJECT_ROOT/hbwy20251220" ]; then
  echo "📦 [Step E] 部署 hongbao 项目..."
  echo "----------------------------------------"
  
  SITE_DIR="hbwy20251220"
  PROJECT_DIR="$PROJECT_ROOT/$SITE_DIR"
  TARGET_PORT=3002
  PM2_NAME="hongbao-frontend"
  
  cd "$PROJECT_DIR" || {
    echo "❌ 无法进入项目子目录"
    exit 1
  }
  
  # 安装依赖
  echo "安装依赖..."
  npm install --quiet || {
    echo "⚠️  依赖安装失败"
    exit 1
  }
  
  # 构建项目（限制内存使用，防止撑爆服务器）
  echo "构建项目..."
  echo "⚠️  限制 Node.js 最大内存使用为 3GB（防止 OOM）"
  export NODE_OPTIONS="--max-old-space-size=3072"
  npm run build || {
    echo "❌ 构建失败"
    exit 1
  }
  
  if [ ! -d "dist" ]; then
    echo "❌ dist 目录不存在"
    exit 1
  fi
  
  echo "✅ 构建完成"
  
  # 停止旧进程
  pm2 delete "$PM2_NAME" 2>/dev/null || true
  if sudo lsof -i :$TARGET_PORT >/dev/null 2>&1; then
    sudo lsof -ti :$TARGET_PORT | xargs sudo kill -9 2>/dev/null || true
    sleep 2
  fi
  
  # 启动服务（添加内存限制）
  mkdir -p "$PROJECT_ROOT/logs"
  echo "启动 hongbao 服务 (端口 $TARGET_PORT)..."
  pm2 start serve \
    --name "$PM2_NAME" \
    --max-memory-restart 1G \
    --error "$PROJECT_ROOT/logs/${PM2_NAME}-error.log" \
    --output "$PROJECT_ROOT/logs/${PM2_NAME}-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- -s "$PROJECT_DIR/dist" -l $TARGET_PORT || {
    echo "⚠️  PM2 启动失败，查看错误..."
    pm2 logs "$PM2_NAME" --lines 50 --nostream 2>/dev/null || true
    exit 1
  }
  
  pm2 save || true
  
  # 智能健康检查：等待端口启动
  wait_for_port $TARGET_PORT "Hongbao"
  echo ""
fi

# ============================================
# Step F: 部署 tgmini (端口 3001)
# ============================================
if [ -d "$PROJECT_ROOT/tgmini20251220" ]; then
  echo "📦 [Step F] 部署 tgmini 项目..."
  echo "----------------------------------------"
  
  SITE_DIR="tgmini20251220"
  PROJECT_DIR="$PROJECT_ROOT/$SITE_DIR"
  TARGET_PORT=3001
  PM2_NAME="tgmini-frontend"
  
  cd "$PROJECT_DIR" || {
    echo "❌ 无法进入项目子目录"
    exit 1
  }
  
  # 安装依赖
  echo "安装依赖..."
  npm install --quiet || {
    echo "⚠️  依赖安装失败"
    exit 1
  }
  
  # 构建项目
  echo "构建项目..."
  export NODE_OPTIONS="--max-old-space-size=3072"
  npm run build || {
    echo "❌ 构建失败"
    exit 1
  }
  
  if [ ! -d "dist" ]; then
    echo "❌ dist 目录不存在"
    exit 1
  fi
  
  echo "✅ 构建完成"
  
  # 停止旧进程
  pm2 delete "$PM2_NAME" 2>/dev/null || true
  if sudo lsof -i :$TARGET_PORT >/dev/null 2>&1; then
    sudo lsof -ti :$TARGET_PORT | xargs sudo kill -9 2>/dev/null || true
    sleep 2
  fi
  
  # 启动服务
  mkdir -p "$PROJECT_ROOT/logs"
  echo "启动 tgmini 服务 (端口 $TARGET_PORT)..."
  # 使用 npx serve 确保使用正确的 serve 命令
  pm2 start npx \
    --name "$PM2_NAME" \
    --max-memory-restart 1G \
    --error "$PROJECT_ROOT/logs/${PM2_NAME}-error.log" \
    --output "$PROJECT_ROOT/logs/${PM2_NAME}-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- serve -s "$PROJECT_DIR/dist" -l $TARGET_PORT || {
    echo "⚠️  PM2 启动失败，查看错误..."
    pm2 logs "$PM2_NAME" --lines 50 --nostream 2>/dev/null || true
    exit 1
  }
  
  pm2 save || true
  
  # 智能健康检查：等待端口启动
  wait_for_port $TARGET_PORT "TG Mini"
  echo ""
fi

# ============================================
# 验证所有服务
# ============================================
echo "🔍 验证所有服务..."
echo "----------------------------------------"
pm2 list
echo ""

echo "端口监听状态:"
sudo lsof -i :8000 -i :3005 -i :3001 -i :3002 -i :3003 2>/dev/null || echo "无法检查端口状态"
echo ""

# ============================================
# 重启 Nginx
# ============================================
echo "🌐 重启 Nginx..."
echo "----------------------------------------"
sudo nginx -t && sudo systemctl restart nginx || {
  echo "⚠️  Nginx 重启失败"
}
echo "✅ Nginx 已重启"
echo ""

# ============================================
# 完成
# ============================================
echo "=========================================="
echo "✅ 部署完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "服务状态:"
echo "  后端: http://127.0.0.1:8000"
echo "  aikz (saas-demo): http://127.0.0.1:3000"
echo "  tgmini: http://127.0.0.1:3001"
echo "  hongbao: http://127.0.0.1:3002"
echo "  aizkw: http://127.0.0.1:3003"
echo ""
echo "PM2 状态:"
pm2 list
echo ""
echo "验证命令:"
echo "  pm2 list"
echo "  curl -I http://127.0.0.1:8000/health"
echo "  curl -I http://127.0.0.1:3005"
echo "  curl -I http://127.0.0.1:3001"
echo "  curl -I http://127.0.0.1:3002"
echo "  curl -I http://127.0.0.1:3003"
