#!/bin/bash
# 彻底诊断并修复502问题
# 在远程服务器 ubuntu@165.154.233.55 上执行

set -e

LOG_FILE="/tmp/fix_502_complete_$(date +%Y%m%d_%H%M%S).log"

{
echo "========================================="
echo "彻底诊断并修复 502 Bad Gateway"
echo "开始时间: $(date)"
echo "========================================="
echo ""

# ============================================================================
# 步骤1: 检查前端服务状态
# ============================================================================

echo "【步骤1】检查前端服务状态"
echo "─────────────────────────────────────────"
cd ~/liaotian/saas-demo || { echo "✗ 无法进入前端目录"; exit 1; }

echo "1.1 检查进程:"
FRONTEND_PROCESSES=$(ps aux | grep -E 'next.*dev|node.*3000' | grep -v grep || true)
if [ -n "$FRONTEND_PROCESSES" ]; then
    echo "$FRONTEND_PROCESSES"
    echo "  ⚠ 发现前端进程"
else
    echo "  无前端进程运行"
fi
echo ""

echo "1.2 检查端口3000:"
PORT_3000=$(sudo ss -tlnp | grep ':3000 ' || echo "")
if [ -n "$PORT_3000" ]; then
    echo "  ⚠ 端口3000正在被占用:"
    echo "$PORT_3000"
else
    echo "  端口3000未监听"
fi
echo ""

echo "1.3 测试本地连接:"
LOCAL_3000_TEST=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 http://localhost:3000 2>&1 || echo "FAILED")
if [ "$LOCAL_3000_TEST" = "200" ] || [ "$LOCAL_3000_TEST" = "304" ]; then
    echo "  ✓ http://localhost:3000 返回 HTTP $LOCAL_3000_TEST"
else
    echo "  ✗ http://localhost:3000 连接失败: $LOCAL_3000_TEST"
fi
echo ""

# ============================================================================
# 步骤2: 查看前端日志
# ============================================================================

echo "【步骤2】查看前端日志"
echo "─────────────────────────────────────────"
if [ -f /tmp/frontend.log ]; then
    echo "日志文件存在，最后100行:"
    tail -100 /tmp/frontend.log
else
    echo "  日志文件不存在"
fi
echo ""

# ============================================================================
# 步骤3: 检查配置
# ============================================================================

echo "【步骤3】检查配置和环境"
echo "─────────────────────────────────────────"

echo "3.1 package.json dev脚本:"
if [ -f package.json ]; then
    DEV_SCRIPT=$(grep -A 1 '"dev"' package.json | head -2 || echo "")
    echo "$DEV_SCRIPT"
    
    if echo "$DEV_SCRIPT" | grep -q 'next dev -p 3000'; then
        echo "  ✓ 端口配置正确（3000）"
        NEED_FIX_PORT=false
    else
        echo "  ✗ 端口配置可能不正确"
        NEED_FIX_PORT=true
    fi
else
    echo "  ✗ package.json 不存在"
    exit 1
fi
echo ""

echo "3.2 Node.js版本:"
NODE_VERSION=$(node -v 2>&1 || echo "未安装")
echo "  $NODE_VERSION"
if [ "$NODE_VERSION" = "未安装" ]; then
    echo "  ✗ Node.js未安装，无法运行前端"
    exit 1
fi
echo ""

echo "3.3 npm版本:"
NPM_VERSION=$(npm -v 2>&1 || echo "未安装")
echo "  $NPM_VERSION"
if [ "$NPM_VERSION" = "未安装" ]; then
    echo "  ✗ npm未安装，无法运行前端"
    exit 1
fi
echo ""

echo "3.4 检查node_modules:"
if [ ! -d node_modules ]; then
    echo "  ✗ node_modules不存在，需要安装依赖"
    NEED_INSTALL=true
elif [ ! -f node_modules/.bin/next ]; then
    echo "  ⚠ Next.js未安装，需要安装依赖"
    NEED_INSTALL=true
else
    echo "  ✓ node_modules和Next.js存在"
    NEED_INSTALL=false
fi
echo ""

# ============================================================================
# 步骤4: 修复端口配置（如果需要）
# ============================================================================

if [ "$NEED_FIX_PORT" = true ]; then
    echo "【步骤4】修复端口配置"
    echo "─────────────────────────────────────────"
    
    node -e "
    const fs = require('fs');
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    pkg.scripts.dev = 'next dev -p 3000';
    fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n', 'utf8');
    " && echo "  ✓ package.json已修复，端口设置为3000" || echo "  ✗ 修复失败"
    echo ""
fi

# ============================================================================
# 步骤5: 安装依赖（如果需要）
# ============================================================================

if [ "$NEED_INSTALL" = true ]; then
    echo "【步骤5】安装依赖"
    echo "─────────────────────────────────────────"
    echo "  正在安装npm依赖（这可能需要几分钟）..."
    npm install 2>&1 | tail -30
    if [ $? -eq 0 ]; then
        echo "  ✓ npm install 完成"
    else
        echo "  ✗ npm install 失败"
        exit 1
    fi
    echo ""
fi

# ============================================================================
# 步骤6: 停止旧进程
# ============================================================================

echo "【步骤6】停止旧进程"
echo "─────────────────────────────────────────"
pkill -f "next.*dev|node.*3000" 2>/dev/null || true
sleep 2
echo "  ✓ 旧进程已停止"
echo ""

# ============================================================================
# 步骤7: 前台运行npm run dev（捕获错误）
# ============================================================================

echo "【步骤7】前台运行npm run dev（捕获错误）"
echo "─────────────────────────────────────────"
echo "  前台运行，等待30秒观察输出..."
echo ""

# 启动并捕获输出
npm run dev > /tmp/frontend_direct_output.log 2>&1 &
DEV_PID=$!
sleep 30

# 检查进程状态
if ps -p $DEV_PID > /dev/null 2>&1; then
    echo "  ✓ 进程仍在运行（PID: $DEV_PID）"
    echo "  查看输出:"
    tail -50 /tmp/frontend_direct_output.log
    
    # 检查端口
    if sudo ss -tlnp | grep -q ':3000 '; then
        echo ""
        echo "  ✓ 端口3000正在监听"
        PORT_INFO=$(sudo ss -tlnp | grep ':3000 ')
        echo "  $PORT_INFO"
    else
        echo ""
        echo "  ⚠ 进程运行但端口3000未监听"
    fi
    
    # 测试连接
    TEST_RESULT=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 http://localhost:3000 2>&1 || echo "FAILED")
    if [ "$TEST_RESULT" = "200" ] || [ "$TEST_RESULT" = "304" ]; then
        echo "  ✓ 本地连接测试成功 (HTTP $TEST_RESULT)"
        FRONTEND_READY=true
    else
        echo "  ✗ 本地连接测试失败: $TEST_RESULT"
        FRONTEND_READY=false
    fi
else
    echo "  ✗ 进程已退出"
    echo "  完整输出:"
    cat /tmp/frontend_direct_output.log
    
    # 分析错误
    ERROR_CONTENT=$(cat /tmp/frontend_direct_output.log)
    
    echo ""
    echo "  【错误分析】"
    if echo "$ERROR_CONTENT" | grep -qi "cannot find module\|module not found"; then
        echo "    错误类型: 缺少依赖模块"
        echo "    解决方案: 需要运行 npm install"
        echo "    将自动执行 npm install..."
        npm install 2>&1 | tail -30
    elif echo "$ERROR_CONTENT" | grep -qi "port.*already in use\|address already in use"; then
        echo "    错误类型: 端口被占用"
        echo "    解决方案: 停止占用端口的进程"
        sudo lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    elif echo "$ERROR_CONTENT" | grep -qi "syntax.*error\|parse.*error"; then
        echo "    错误类型: 代码语法错误"
        echo "    解决方案: 需要修复代码错误"
        echo "    错误详情请查看 /tmp/frontend_direct_output.log"
    elif echo "$ERROR_CONTENT" | grep -qi "ENOENT\|no such file"; then
        echo "    错误类型: 文件或目录不存在"
        echo "    解决方案: 检查文件路径"
    else
        echo "    错误类型: 未知错误，请查看完整日志"
    fi
    
    FRONTEND_READY=false
fi

echo ""

if [ "$FRONTEND_READY" = false ]; then
    echo "  ⚠ 前端服务未正常启动，但继续尝试后台启动..."
fi

# 停止前台进程
kill $DEV_PID 2>/dev/null || true
sleep 2

# ============================================================================
# 步骤8: 后台启动前端服务
# ============================================================================

echo "【步骤8】后台启动前端服务"
echo "─────────────────────────────────────────"
pkill -f "next.*dev|node.*3000" 2>/dev/null || true
sleep 2

nohup npm run dev > /tmp/frontend.log 2>&1 &
NEW_PID=$!
sleep 20

# 验证后台进程
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "  ✓ 前端服务已在后台启动（PID: $NEW_PID）"
else
    echo "  ✗ 前端服务启动失败"
    echo "  查看日志:"
    tail -50 /tmp/frontend.log
    exit 1
fi

# 验证端口和连接
sleep 5
if sudo ss -tlnp | grep -q ':3000 '; then
    echo "  ✓ 端口3000正在监听"
else
    echo "  ⚠ 端口3000未监听，查看日志:"
    tail -30 /tmp/frontend.log
fi

BACKEND_TEST=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 http://localhost:8000/health 2>&1 || echo "000")
FRONTEND_TEST=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 http://localhost:3000 2>&1 || echo "000")

echo ""
echo "【步骤9】验证服务状态"
echo "─────────────────────────────────────────"
echo "  后端健康检查: HTTP $BACKEND_TEST"
echo "  前端服务: HTTP $FRONTEND_TEST"

if [ "$FRONTEND_TEST" = "200" ] || [ "$FRONTEND_TEST" = "304" ]; then
    echo "  ✓ 前端服务正常"
    FRONTEND_OK=true
else
    echo "  ✗ 前端服务异常 (HTTP $FRONTEND_TEST)"
    echo "  查看日志:"
    tail -50 /tmp/frontend.log
    FRONTEND_OK=false
fi
echo ""

# ============================================================================
# 步骤10: 重载Nginx并验证域名
# ============================================================================

echo "【步骤10】重载Nginx并验证域名"
echo "─────────────────────────────────────────"
sudo systemctl reload nginx 2>/dev/null && echo "  ✓ Nginx已重载" || echo "  ⚠ Nginx重载失败"
sleep 3

DOMAIN_ACCOUNTS=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 http://aikz.usdt2026.cc/group-ai/accounts 2>&1 || echo "000")
DOMAIN_ROOT=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 http://aikz.usdt2026.cc/ 2>&1 || echo "000")

echo "  域名 /group-ai/accounts: HTTP $DOMAIN_ACCOUNTS"
echo "  域名 /: HTTP $DOMAIN_ROOT"

if [ "$DOMAIN_ACCOUNTS" != "502" ] && [ "$DOMAIN_ROOT" != "502" ]; then
    echo "  ✓ 域名访问不再返回502"
    FIXED_502=true
else
    echo "  ✗ 域名访问仍返回502"
    echo "  查看Nginx错误日志:"
    sudo tail -20 /var/log/nginx/error.log
    FIXED_502=false
fi
echo ""

# ============================================================================
# 最终总结
# ============================================================================

echo "========================================="
echo "诊断和修复完成！"
echo "完成时间: $(date)"
echo "========================================="
echo ""
echo "【前端服务状态】"
echo "  进程PID: $NEW_PID"
echo "  本地测试: HTTP $FRONTEND_TEST"
echo "  域名测试: HTTP $DOMAIN_ACCOUNTS"
echo ""
echo "【修复内容】"
if [ "$NEED_FIX_PORT" = true ]; then
    echo "  ✓ 修复了package.json中的端口配置"
fi
if [ "$NEED_INSTALL" = true ]; then
    echo "  ✓ 安装了npm依赖"
fi
echo "  ✓ 重启了前端服务"
echo "  ✓ 重载了Nginx配置"
echo ""
if [ "$FIXED_502" = true ]; then
    echo "  ✅ 502问题已修复！"
else
    echo "  ⚠ 502问题可能仍存在，请检查Nginx配置或查看日志"
fi
echo ""
echo "【错误原因总结】"
if [ -f /tmp/frontend_direct_output.log ]; then
    ERROR_CONTENT=$(cat /tmp/frontend_direct_output.log)
    if echo "$ERROR_CONTENT" | grep -qi "cannot find module"; then
        echo "  根本原因: 缺少依赖模块，已通过 npm install 修复"
    elif echo "$ERROR_CONTENT" | grep -qi "port.*already in use"; then
        echo "  根本原因: 端口被占用，已停止占用进程"
    elif echo "$ERROR_CONTENT" | grep -qi "syntax.*error"; then
        echo "  根本原因: 代码语法错误（需手动修复）"
    else
        echo "  根本原因: 请查看 /tmp/frontend_direct_output.log 了解详情"
    fi
fi
echo "========================================="

} 2>&1 | tee "$LOG_FILE"

echo ""
echo "完整日志已保存到: $LOG_FILE"
