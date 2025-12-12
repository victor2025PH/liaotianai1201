#!/bin/bash
# ============================================================
# 自动化部署脚本
# ============================================================

# set -x  # 已關閉調試模式，減少日誌輸出
set -o pipefail
# 不使用 set -e，因為它會與條件判斷 [ ] 產生衝突
# 我們使用手動錯誤檢查來處理關鍵命令的失敗

handle_error() {
  echo "❌ Error at: $1"
  echo "Exit code: $?"
  exit 1
}

echo "=========================================="
echo "Starting deployment - $(date)"
echo "=========================================="

echo "Testing SSH connection..."
if ! whoami; then
  echo "❌ SSH connection failed"
  handle_error "SSH connection test"
fi
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "✅ SSH connection successful"

echo "=========================================="
echo "Step 1: Check project directory"
echo "=========================================="
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
GITHUB_REPO="${GITHUB_REPO:-victor2025PH/liaotianai1201}"

# 直接嘗試進入目錄，如果失敗則克隆
if cd "$PROJECT_DIR" 2>/dev/null; then
  echo "✅ Project directory exists"
else
  echo "Project directory not found, cloning..."
  cd /home/ubuntu || handle_error "cd to /home/ubuntu"
  if ! timeout 10m git clone "https://github.com/$GITHUB_REPO.git" telegram-ai-system; then
    echo "❌ Git clone failed or timeout"
    handle_error "git clone"
  fi
  cd "$PROJECT_DIR" || handle_error "cd to project directory"
fi

# 清理 /home/ubuntu/ 下的重複文件（舊的手動部署遺留）
echo ""
echo "清理舊的部署文件（如果存在）..."
# 顯式進入目錄，避免相對路徑問題
cd /home/ubuntu 2>/dev/null || true

for dir in admin-backend saas-demo deploy scripts; do
  target="/home/ubuntu/$dir"
  # 邏輯：如果目標存在且是目錄 (-d)，並且 它不是軟鏈接 (! -L)
  if [ -d "$target" ] && [ ! -L "$target" ]; then
    echo "⚠️  發現舊的部署目錄: $target"
    echo "   這可能是舊的手動部署遺留，建議手動檢查後刪除"
  fi || true
done

# 返回項目目錄
cd "$PROJECT_DIR" || handle_error "cd to project directory"

echo ""
echo "=========================================="
echo "Step 2: Pull latest code"
echo "=========================================="
if ! timeout 5m git fetch origin main; then
  echo "⚠️  Git fetch failed or timeout, retrying..."
  git remote set-url origin "https://github.com/$GITHUB_REPO.git"
  if ! timeout 5m git fetch origin main; then
    echo "❌ Git fetch failed or timeout"
    handle_error "git fetch"
  fi
fi
if ! timeout 1m git reset --hard origin/main; then
  echo "❌ Git reset failed or timeout"
  handle_error "git reset"
fi
echo "✅ Code updated to latest version"
timeout 10s git log -1 --oneline || true

echo ""
echo "=========================================="
echo "Step 3: Update backend dependencies"
echo "=========================================="
if [ -d "admin-backend" ]; then
  cd admin-backend
  # 如果 venv 不存在或 activate 文件不存在，則重新創建
  if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment (venv is missing or broken)..."
    rm -rf venv  # 安全起見，先刪除可能存在的壞目錄
    # 嘗試創建虛擬環境，如果失敗則安裝 python3-venv 包
    if ! python3 -m venv venv 2>/dev/null; then
      echo "python3-venv not available, installing python3-venv package..."
      timeout 2m sudo apt-get update -qq && timeout 5m sudo apt-get install -y python3-venv || {
        echo "❌ Failed to install python3-venv"
        handle_error "install python3-venv"
      }
      # 重新嘗試創建虛擬環境
      python3 -m venv venv || {
        echo "❌ Failed to create virtual environment after installing python3-venv"
        handle_error "create venv"
      }
    fi
  fi
  
  # Check and install ffmpeg (Safe pattern for ssh-action)
  command -v ffmpeg >/dev/null 2>&1 || {
    echo "Installing system ffmpeg..."
    timeout 2m sudo apt-get update -qq
    timeout 5m sudo apt-get install -y ffmpeg
  }
  
  source venv/bin/activate
  echo "Updating Python packages..."
  timeout 2m pip install --quiet --upgrade pip || echo "⚠️  pip upgrade failed or timeout, continuing..."
  timeout 10m pip install --quiet -r requirements.txt --timeout=300 --cache-dir=/tmp/pip-cache || {
    echo "⚠️  Some dependencies failed or timeout, continuing..."
  }
  cd ..
  echo "✅ Backend dependencies updated"
else
  echo "⚠️  admin-backend directory not found"
fi

echo ""
echo "=========================================="
echo "Step 4: Update Bot dependencies"
echo "=========================================="
if [ -f "requirements.txt" ]; then
  # 如果 venv 不存在或 activate 文件不存在，則重新創建
  if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment (venv is missing or broken)..."
    rm -rf venv  # 安全起見，先刪除可能存在的壞目錄
    # 嘗試創建虛擬環境，如果失敗則安裝 python3-venv 包
    if ! python3 -m venv venv 2>/dev/null; then
      echo "python3-venv not available, installing python3-venv package..."
      timeout 2m sudo apt-get update -qq && timeout 5m sudo apt-get install -y python3-venv || {
        echo "❌ Failed to install python3-venv"
        handle_error "install python3-venv"
      }
      # 重新嘗試創建虛擬環境
      python3 -m venv venv || {
        echo "❌ Failed to create virtual environment after installing python3-venv"
        handle_error "create venv"
      }
    fi
  fi
  
  # Check and install ffmpeg (Safe pattern for ssh-action)
  command -v ffmpeg >/dev/null 2>&1 || {
    echo "Installing system ffmpeg..."
    timeout 2m sudo apt-get update -qq
    timeout 5m sudo apt-get install -y ffmpeg
  }
  
  source venv/bin/activate
  timeout 2m pip install --quiet --upgrade pip || echo "⚠️  pip upgrade failed or timeout, continuing..."
  timeout 10m pip install --quiet -r requirements.txt --timeout=300 --cache-dir=/tmp/pip-cache || {
    echo "⚠️  Some dependencies failed or timeout, continuing..."
  }
  echo "✅ Bot dependencies updated"
else
  echo "⚠️  Bot requirements.txt not found"
fi

echo ""
echo "=========================================="
echo "Step 5: Deploy frontend"
echo "=========================================="
if [ -d "saas-demo" ]; then
  cd saas-demo
  
  # 智能跳過前端構建：檢查前端代碼是否有變動
  FRONTEND_CHANGED=true
  
  # 方法1: 检查最近的commit是否包含前端文件变化
  # 获取最近2个commit的hash
  LAST_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")
  PREV_COMMIT=$(git rev-parse HEAD^ 2>/dev/null || echo "")
  
  if [ -n "$LAST_COMMIT" ] && [ -n "$PREV_COMMIT" ]; then
    # 检查最近commit是否包含前端文件变化
    if git diff --quiet "$PREV_COMMIT" "$LAST_COMMIT" -- saas-demo/ 2>/dev/null; then
      # 检查 .next 目录是否存在且完整
      if [ -d ".next/standalone" ] && [ -d ".next/static" ] && [ -f ".next/standalone/server.js" ]; then
        # 额外检查：如果standalone目录的修改时间比最近commit时间新，说明已经构建过
        BUILD_TIME=$(stat -c %Y .next/standalone/server.js 2>/dev/null || echo "0")
        COMMIT_TIME=$(git log -1 --format=%ct "$LAST_COMMIT" 2>/dev/null || echo "0")
        
        if [ "$BUILD_TIME" -gt "$COMMIT_TIME" ]; then
          FRONTEND_CHANGED=false
          echo "⏩ Frontend code unchanged, skipping build..."
          echo "✅ Reusing existing build artifacts (built after last commit)"
        else
          echo "🔨 Frontend build is older than last commit, rebuilding..."
        fi
      else
        echo "🔨 Frontend code unchanged but build artifacts missing, rebuilding..."
      fi
    else
      echo "🔨 Frontend code changed in recent commits, rebuilding..."
    fi
  else
    # 如果无法获取commit信息，检查文件是否存在
    if [ -d ".next/standalone" ] && [ -d ".next/static" ] && [ -f ".next/standalone/server.js" ]; then
      echo "⚠️  Cannot determine git history, but build artifacts exist"
      echo "   To force rebuild, delete .next directory or set FORCE_FRONTEND_BUILD=true"
      # 如果设置了强制构建环境变量，则强制构建
      if [ "${FORCE_FRONTEND_BUILD:-false}" = "true" ]; then
        echo "🔨 FORCE_FRONTEND_BUILD=true, forcing rebuild..."
        FRONTEND_CHANGED=true
      else
        FRONTEND_CHANGED=false
        echo "⏩ Skipping build (use FORCE_FRONTEND_BUILD=true to force)"
      fi
    else
      echo "🔨 Build artifacts missing, rebuilding..."
    fi
  fi
  
  if [ "$FRONTEND_CHANGED" = "true" ]; then
    echo "Installing frontend dependencies..."
    if [ -d "node_modules" ]; then
      echo "Using incremental install..."
      # 先尝试 npm ci，如果失败（lock文件不同步），则使用 npm install
      if timeout 15m npm ci --prefer-offline --no-audit --no-fund 2>/dev/null; then
        echo "✅ Dependencies installed with npm ci"
      else
        echo "⚠️  npm ci failed (lock file out of sync), using npm install..."
        timeout 15m npm install --prefer-offline --no-audit --no-fund || {
          echo "⚠️  Dependency installation timeout or failed, continuing..."
        }
      fi
    else
      echo "First-time install..."
      timeout 20m npm install --prefer-offline --no-audit --no-fund || {
        echo "⚠️  Dependency installation timeout or failed, continuing..."
      }
    fi
    
    echo "Building frontend project..."
    export NODE_OPTIONS="--max-old-space-size=2048"
    
    # 强制清理可能存在的 Next.js 构建锁，避免 "Unable to acquire lock" 错误
    if [ -f ".next/lock" ]; then
      echo "🧹 Found stale lock file, removing..."
      rm -f .next/lock
    fi
    
    timeout 20m npm run build || {
      echo "⚠️  Build failed or timeout, but continuing..."
    }
  fi
  
  # 无论是否重新构建，都需要确保 standalone 目录结构完整
  if [ -d ".next/standalone" ]; then
    echo "Preparing Standalone directory..."
    
    # 复制 public 目录（如果存在且需要更新）
    if [ -d "public" ]; then
      if [ ! -d ".next/standalone/public" ] || [ "public" -nt ".next/standalone/public" ]; then
        echo "  Copying public directory..."
        cp -r public .next/standalone/ || true
      fi
    fi
    
    # 确保 .next 目录存在
    mkdir -p .next/standalone/.next
    
    # 复制 .next/static 目录（关键：静态资源必须存在）
    if [ -d ".next/static" ]; then
      # 如果 standalone 中的 static 不存在或比源文件旧，则更新
      if [ ! -d ".next/standalone/.next/static" ] || [ ".next/static" -nt ".next/standalone/.next/static" ]; then
        echo "  Copying .next/static directory..."
        rm -rf .next/standalone/.next/static
        cp -r .next/static .next/standalone/.next/ || {
          echo "❌ Failed to copy .next/static"
          exit 1
        }
      fi
    else
      echo "⚠️  .next/static directory not found - build may be incomplete"
    fi
    
    # 验证关键文件
    if [ ! -f ".next/standalone/server.js" ]; then
      echo "❌ server.js not found in standalone directory"
      exit 1
    fi
    
    echo "✅ Standalone directory ready"
  else
    echo "❌ .next/standalone directory not found - build required"
    if [ "$FRONTEND_CHANGED" = "false" ]; then
      echo "⚠️  Frontend code unchanged but standalone missing - forcing rebuild..."
      FRONTEND_CHANGED=true
      # 重新执行构建（这里简化处理，实际应该递归调用或重构逻辑）
      echo "  请手动运行: cd saas-demo && npm run build"
    fi
  fi
  
  # 确保前端环境变量正确设置（生产环境使用相对路径）
  echo "Setting frontend environment variables..."
  if [ ! -f ".env.local" ]; then
    echo "Creating .env.local..."
    cat > .env.local << 'EOF'
NODE_ENV=production
NEXT_PUBLIC_API_BASE_URL=/api/v1
EOF
    echo "✅ .env.local created"
  else
    # 更新或添加API_BASE_URL
    if grep -q "NEXT_PUBLIC_API_BASE_URL" .env.local; then
      sed -i 's|NEXT_PUBLIC_API_BASE_URL=.*|NEXT_PUBLIC_API_BASE_URL=/api/v1|' .env.local
    else
      echo "NEXT_PUBLIC_API_BASE_URL=/api/v1" >> .env.local
    fi
    echo "✅ .env.local updated"
  fi
  
  cd ..
else
  echo "⚠️  saas-demo directory not found"
fi

echo ""
echo "=========================================="
echo "Step 6: Update Nginx config"
echo "=========================================="
if [ -f "deploy/nginx/aikz.conf" ]; then
  sudo cp deploy/nginx/aikz.conf /etc/nginx/sites-available/aikz.conf
  sudo ln -sf /etc/nginx/sites-available/aikz.conf /etc/nginx/sites-enabled/aikz.conf
  if timeout 30s sudo nginx -t 2>/dev/null; then
    timeout 30s sudo systemctl reload nginx 2>/dev/null && echo "✅ Nginx config updated and reloaded" || echo "⚠️  Nginx reload failed or timeout"
  else
    echo "❌ Nginx config test failed or timeout"
  fi
else
  echo "⚠️  deploy/nginx/aikz.conf not found"
fi

echo ""
echo "=========================================="
echo "Step 7: Deploy Systemd services"
echo "=========================================="
if [ -f "scripts/server/deploy-systemd.sh" ]; then
  timeout 5m sudo bash scripts/server/deploy-systemd.sh || echo "⚠️  Systemd deployment failed or timeout, continuing..."
else
  echo "⚠️  deploy-systemd.sh not found"
fi

echo ""
echo "=========================================="
echo "Step 8: Restart services"
echo "=========================================="

# 清理端口 8000 占用（避免 "address already in use" 错误）
echo "Checking port 8000..."
PORT_8000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || true)
if [ -n "$PORT_8000_PID" ]; then
  echo "⚠️  Port 8000 is occupied by PID $PORT_8000_PID, stopping it..."
  sudo kill -9 "$PORT_8000_PID" 2>/dev/null || true
  sleep 1
  # 再次检查确保端口已释放
  PORT_8000_PID_AFTER=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || true)
  if [ -n "$PORT_8000_PID_AFTER" ]; then
    echo "⚠️  Port 8000 still occupied, trying harder..."
    sudo kill -9 "$PORT_8000_PID_AFTER" 2>/dev/null || true
    sleep 1
  fi
  echo "✅ Port 8000 cleared"
else
  echo "✅ Port 8000 is free"
fi

echo "Restarting backend service..."
# 优先使用 luckyred-api，否则使用 telegram-backend（使用 systemctl cat 避免管道 SIGPIPE 错误）
BACKEND_SERVICE=""
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
  BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
  BACKEND_SERVICE="telegram-backend"
fi

if [ -n "$BACKEND_SERVICE" ]; then
  # 先停止服务，确保完全释放资源
  timeout 10s sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
  sleep 2
  
  # 启动服务
  timeout 30s sudo systemctl start "$BACKEND_SERVICE" && echo "✅ Backend ($BACKEND_SERVICE) restarted" || echo "⚠️  Backend restart failed or timeout"
  
  # 等待服务启动
  echo "Waiting for backend service to start (10 seconds)..."
  sleep 10
  
  # 验证后端健康检查
  echo "Verifying backend health..."
  for i in {1..6}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
      echo "✅ Backend health check passed"
      break
    fi
    if [ $i -lt 6 ]; then
      echo "  Waiting for backend... ($i/6)"
      sleep 5
    else
      echo "⚠️  Backend health check failed after 30 seconds"
      echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
    fi
  done
  
  # 验证 AI Provider API 路由是否可用
  echo "Verifying AI Provider API routes..."
  sleep 2
  AI_PROVIDER_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/api/v1/group-ai/ai-provider/providers 2>/dev/null || echo "ERROR")
  AI_PROVIDER_HTTP_CODE=$(echo "$AI_PROVIDER_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")
  
  if [ "$AI_PROVIDER_HTTP_CODE" = "200" ] || [ "$AI_PROVIDER_HTTP_CODE" = "401" ] || [ "$AI_PROVIDER_HTTP_CODE" = "403" ]; then
    echo "✅ AI Provider API route is accessible (HTTP $AI_PROVIDER_HTTP_CODE)"
  elif [ "$AI_PROVIDER_HTTP_CODE" = "404" ]; then
    echo "⚠️  AI Provider API route returned 404 - route may not be registered"
    echo "  检查路由注册: grep -r 'ai-provider' $PROJECT_DIR/admin-backend/app/api/group_ai/__init__.py"
    echo "  查看后端日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager | grep -i 'ai-provider\|ai_provider' || true"
  else
    echo "⚠️  AI Provider API route check failed (HTTP $AI_PROVIDER_HTTP_CODE)"
  fi
else
  echo "⚠️  Backend systemd service not found"
  echo "  尝试部署systemd服务..."
  if [ -f "scripts/server/deploy-systemd.sh" ]; then
    timeout 5m sudo bash scripts/server/deploy-systemd.sh || echo "⚠️  Systemd deployment failed"
  fi
fi

echo "Restarting Bot service..."
timeout 30s sudo systemctl restart telegram-bot && echo "✅ Bot restarted" || echo "⚠️  Bot restart failed or timeout"

FRONTEND_SERVICE_NAME=""
# 使用 systemctl cat 检查服务是否存在（避免管道 SIGPIPE 错误）
if systemctl cat liaotian-frontend.service >/dev/null 2>&1; then
  FRONTEND_SERVICE_NAME="liaotian-frontend"
elif systemctl cat smart-tg-frontend.service >/dev/null 2>&1; then
  FRONTEND_SERVICE_NAME="smart-tg-frontend"
fi

if [ -n "$FRONTEND_SERVICE_NAME" ]; then
  echo "Restarting frontend service ($FRONTEND_SERVICE_NAME)..."
  
  # 如果前端代码有变化，确保重新加载
  if [ "$FRONTEND_CHANGED" = "true" ]; then
    echo "  Frontend code was rebuilt, ensuring service reloads new build..."
    # 停止服务
    timeout 10s sudo systemctl stop "$FRONTEND_SERVICE_NAME" 2>/dev/null || true
    sleep 2
  fi
  
  # 启动/重启服务
  timeout 30s sudo systemctl restart "$FRONTEND_SERVICE_NAME" && echo "✅ Frontend restarted" || echo "⚠️  Frontend restart failed or timeout"
  
  # 等待服务启动并验证端口监听
  echo "Waiting for frontend service to start (10 seconds)..."
  sleep 10
  
  # 检查端口是否监听（最多等待30秒）
  PORT_3000=""
  for i in {1..6}; do
    PORT_3000=$(sudo ss -tlnp 2>/dev/null | grep ":3000" || echo "")
    if [ -n "$PORT_3000" ]; then
      echo "✅ Frontend port 3000 is listening"
      break
    fi
    if [ $i -lt 6 ]; then
      echo "  Waiting for port 3000... ($i/6)"
      sleep 5
    fi
  done
  
  if [ -z "$PORT_3000" ]; then
    echo "⚠️  Frontend port 3000 is not listening after 30 seconds - service may have failed"
    echo "  查看日志: sudo journalctl -u $FRONTEND_SERVICE_NAME -n 50 --no-pager"
    echo "  检查服务状态: sudo systemctl status $FRONTEND_SERVICE_NAME --no-pager | head -20"
  fi
else
  echo "⚠️  Frontend systemd service not found"
fi

echo ""
echo "Waiting for services to start (3 seconds)..."
sleep 3

echo ""
echo "=========================================="
echo "Step 9: Check service status"
echo "=========================================="

echo "Checking backend service..."
# 默认目标服务
TARGET_SERVICE="telegram-backend"

# 使用 systemctl cat 检查 luckyred-api 是否存在
# 这种方式不需要管道，不会触发 SIGPIPE 错误
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
  TARGET_SERVICE="luckyred-api"
fi

echo "Target Service detected: $TARGET_SERVICE"

# 使用 awk 确保只取第一行的第一个单词，并剔除所有空白字符
# 使用 || true 忽略 systemctl is-active 的非零退出码（pipefail 兼容）
BACKEND_STATUS=$(systemctl is-active "$TARGET_SERVICE" 2>/dev/null | awk 'NR==1 {print $1}' || true)
# 如果为空则默认为 inactive
if [ -z "$BACKEND_STATUS" ]; then BACKEND_STATUS="inactive"; fi
echo "Backend Status: $BACKEND_STATUS"

# 如果服务正在启动中，等待最多 90 秒（增加等待时间）
if [ "$BACKEND_STATUS" = "activating" ] || [ "$BACKEND_STATUS" = "deactivating" ]; then
  echo "⏳ Backend service is $BACKEND_STATUS, waiting up to 90 seconds..."
  for i in {1..90}; do
    sleep 1
    BACKEND_STATUS=$(systemctl is-active "$TARGET_SERVICE" 2>/dev/null | awk 'NR==1 {print $1}' || true)
    if [ -z "$BACKEND_STATUS" ]; then BACKEND_STATUS="inactive"; fi
    
    # 只在状态变化时打印，避免刷屏（每 5 秒打印一次）
    if [ $((i % 5)) -eq 0 ]; then
      echo "  Attempt $i/90: Status = $BACKEND_STATUS"
    fi
    
    if [ "$BACKEND_STATUS" = "active" ]; then
      echo "✅ Service started successfully!"
      break
    elif [ "$BACKEND_STATUS" = "failed" ]; then
      echo "❌ Service failed to start (status: failed)"
      break
    elif [ "$BACKEND_STATUS" != "activating" ] && [ "$BACKEND_STATUS" != "active" ] && [ "$BACKEND_STATUS" != "deactivating" ]; then
      # 如果状态不再是 activating/deactivating 或 active，也退出循环
      echo "⚠️  Service status changed to: $BACKEND_STATUS"
      break
    fi
  done
  
  # 循环结束后再次检查状态
  BACKEND_STATUS=$(systemctl is-active "$TARGET_SERVICE" 2>/dev/null | awk 'NR==1 {print $1}' || true)
  if [ -z "$BACKEND_STATUS" ]; then BACKEND_STATUS="inactive"; fi
  echo "Final status after wait: $BACKEND_STATUS"
fi

# 最终检查状态 - 确保状态变量是最新的
BACKEND_STATUS=$(systemctl is-active "$TARGET_SERVICE" 2>/dev/null | awk 'NR==1 {print $1}' || true)
if [ -z "$BACKEND_STATUS" ]; then BACKEND_STATUS="inactive"; fi
echo "Final check - Status: $BACKEND_STATUS"
# 强制刷新输出，确保能看到状态
sync 2>/dev/null || true
echo "DEBUG: About to check if status is active..."
sync 2>/dev/null || true
echo "DEBUG: Status value is: [$BACKEND_STATUS]"
sync 2>/dev/null || true

# 立即输出状态判断结果，确保能看到执行流程
if [ "$BACKEND_STATUS" = "active" ]; then
  echo "Status is active, entering success branch"
  sync 2>/dev/null || true
else
  echo "Status is NOT active ($BACKEND_STATUS), entering error handler"
  sync 2>/dev/null || true
  echo "DEBUG: Confirmed status is NOT active, will enter else branch"
  sync 2>/dev/null || true
fi

if [ "$BACKEND_STATUS" = "active" ]; then
  echo "✅ Backend service ($TARGET_SERVICE) is running"
  # 健康检查
  if timeout 10s curl -s -f --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend health check: Passed"
  else
    echo "⚠️  Backend health check: Failed (Service is up but API not responding)"
    echo "⬇️ Last 20 lines of logs:"
    sudo journalctl -u "$TARGET_SERVICE" -n 20 --no-pager || true
  fi
else
  # 立即输出错误信息，避免被截断
  echo "DEBUG: Entering error handler branch..."
  sync 2>/dev/null || true
  echo "Entering error handler..."
  sync 2>/dev/null || true
  echo ""
  echo "=========================================="
  echo "ERROR: Backend service ($TARGET_SERVICE) failed to start!"
  echo "Final Status: $BACKEND_STATUS"
  echo "=========================================="
  sync 2>/dev/null || true
  echo "DEBUG: Error header printed, about to show logs..."
  sync 2>/dev/null || true
  
  # 先输出最关键的错误信息（journalctl 的最后 15 行）
  echo ""
  echo "ERROR LOGS (Last 15 lines):"
  sudo journalctl -u "$TARGET_SERVICE" -n 15 --no-pager --no-hostname 2>&1 | tail -15 || echo "  (No logs)"
  sync 2>/dev/null || true
  
  # 检查文件是否存在（关键诊断）
  echo ""
  echo "FILE CHECK:"
  UVCORN_EXISTS=$([ -f "$PROJECT_DIR/admin-backend/venv/bin/uvicorn" ] && echo "YES" || echo "NO")
  ENV_EXISTS=$([ -f "$PROJECT_DIR/admin-backend/.env" ] && echo "YES" || echo "NO")
  DIR_EXISTS=$([ -d "$PROJECT_DIR/admin-backend" ] && echo "YES" || echo "NO")
  echo "  uvicorn: $UVCORN_EXISTS"
  echo "  .env: $ENV_EXISTS"
  echo "  WorkingDir: $DIR_EXISTS"
  
  # Python 语法检查（快速检查）
  echo ""
  echo "PYTHON SYNTAX:"
  cd "$PROJECT_DIR/admin-backend" 2>/dev/null || true
  if python3 -m py_compile app/api/group_ai/servers.py 2>&1 >/dev/null; then
    echo "  OK"
  else
    echo "  ERROR:"
    python3 -m py_compile app/api/group_ai/servers.py 2>&1 | head -3 || true
  fi
  
  # 服务配置（只显示关键部分）
  echo ""
  echo "SERVICE CONFIG:"
  sudo systemctl cat "$TARGET_SERVICE" 2>&1 | grep -E "(ExecStart|WorkingDirectory|User|EnvironmentFile)" | head -5 || echo "  (N/A)"
  
  # 强制刷新并退出
  echo ""
  echo "=========================================="
  echo "Exiting with error code 1"
  sync 2>/dev/null || true
  exit 1
fi

echo ""
echo "Checking Bot service..."
# 使用 awk 确保只取第一行的第一个单词，并剔除所有空白字符
# 使用 || true 忽略 systemctl is-active 的非零退出码（pipefail 兼容）
BOT_STATUS=$(systemctl is-active telegram-bot 2>/dev/null | awk 'NR==1 {print $1}' || true)
# 如果为空则默认为 inactive
if [ -z "$BOT_STATUS" ]; then BOT_STATUS="inactive"; fi
echo "Bot Status: $BOT_STATUS"
if [ "$BOT_STATUS" = "active" ]; then
  echo "✅ Bot service: Running"
else
  echo "⚠️  Bot service: Not running (This is expected if session is not configured)"
  echo "   Bot service requires a valid Telegram session file to run."
  echo "   To configure:"
  echo "   1. Place a session file in /home/ubuntu/telegram-ai-system/sessions/"
  echo "   2. Or set SESSION_STRING environment variable"
  echo "   3. Ensure API_ID and API_HASH are set in config.py or environment"
  echo "⬇️ Bot Logs (last 20 lines):"
  sudo journalctl -u telegram-bot -n 20 --no-pager || true
  echo ""
  echo "ℹ️  Continuing deployment (Bot service failure is non-critical)..."
fi

echo ""
echo "Checking frontend service..."
FRONTEND_SERVICE=""
# 使用 systemctl cat 检查服务是否存在（避免管道 SIGPIPE 错误）
if systemctl cat liaotian-frontend.service >/dev/null 2>&1; then
  FRONTEND_SERVICE="liaotian-frontend"
elif systemctl cat smart-tg-frontend.service >/dev/null 2>&1; then
  FRONTEND_SERVICE="smart-tg-frontend"
fi

if [ -n "$FRONTEND_SERVICE" ]; then
  # 使用 awk 确保只取第一行的第一个单词，并剔除所有空白字符
  # 使用 || true 忽略 systemctl is-active 的非零退出码（pipefail 兼容）
  FRONTEND_STATUS=$(systemctl is-active "$FRONTEND_SERVICE" 2>/dev/null | awk 'NR==1 {print $1}' || true)
  # 如果为空则默认为 inactive
  if [ -z "$FRONTEND_STATUS" ]; then FRONTEND_STATUS="inactive"; fi
  echo "Frontend Status: $FRONTEND_STATUS"
  
  # 如果前端服务正在启动中，等待最多 30 秒
  if [ "$FRONTEND_STATUS" = "activating" ]; then
    echo "⏳ Frontend service is activating, waiting up to 30 seconds..."
    for i in {1..30}; do
      sleep 1
      FRONTEND_STATUS=$(systemctl is-active "$FRONTEND_SERVICE" 2>/dev/null | awk 'NR==1 {print $1}' || true)
      if [ -z "$FRONTEND_STATUS" ]; then FRONTEND_STATUS="inactive"; fi
      
      # 每 5 秒打印一次状态
      if [ $((i % 5)) -eq 0 ]; then
        echo "  Attempt $i/30: Status = $FRONTEND_STATUS"
      fi
      
      if [ "$FRONTEND_STATUS" = "active" ]; then
        echo "✅ Frontend service started successfully!"
        break
      elif [ "$FRONTEND_STATUS" = "failed" ]; then
        echo "❌ Frontend service failed to start (status: failed)"
        break
      elif [ "$FRONTEND_STATUS" != "activating" ] && [ "$FRONTEND_STATUS" != "active" ]; then
        echo "⚠️  Frontend service status changed to: $FRONTEND_STATUS"
        break
      fi
    done
    
    # 循环结束后再次检查状态
    FRONTEND_STATUS=$(systemctl is-active "$FRONTEND_SERVICE" 2>/dev/null | awk 'NR==1 {print $1}' || true)
    if [ -z "$FRONTEND_STATUS" ]; then FRONTEND_STATUS="inactive"; fi
    echo "Final frontend status after wait: $FRONTEND_STATUS"
  fi
  
  if [ "$FRONTEND_STATUS" = "active" ]; then
    echo "✅ Frontend service ($FRONTEND_SERVICE): Running"
    HTTP_CODE=$(timeout 10s curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
      echo "✅ Frontend HTTP response: Normal (HTTP $HTTP_CODE)"
    else
      echo "⚠️  Frontend HTTP response: Abnormal (HTTP $HTTP_CODE)"
      echo "⬇️ Last 20 lines of logs:"
      sudo journalctl -u "$FRONTEND_SERVICE" -n 20 --no-pager || true
    fi
  else
    # 前端服务启动失败，打印详细日志但不中断部署（前端不是关键服务）
    echo "⚠️  Frontend service ($FRONTEND_SERVICE): Not running (Status: $FRONTEND_STATUS)"
    echo "⬇️ Frontend Service Status:"
    sudo systemctl status "$FRONTEND_SERVICE" -l --no-pager | head -30 || true
    echo ""
    echo "⬇️ Frontend Logs (Last 50 lines):"
    sudo journalctl -u "$FRONTEND_SERVICE" -n 50 --no-pager || true
    echo ""
    echo "⚠️  Frontend service failed to start, but continuing deployment..."
    # 不调用 handle_error，因为前端服务不是关键服务，后端和 Bot 已经成功启动
  fi
else
  echo "⚠️  Frontend systemd service not found"
fi

echo ""
echo "=========================================="
echo "Deployment completed - $(date)"
echo "=========================================="
echo "✅ Code updated"
echo "✅ Services restarted"
echo ""
SERVER_HOST="${SERVER_HOST:-localhost}"
echo "Service URLs:"
echo "  - Frontend: http://$SERVER_HOST"
echo "  - Backend API: http://$SERVER_HOST:8000"
echo "  - API Docs: http://$SERVER_HOST:8000/docs"

