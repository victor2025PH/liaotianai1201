#!/bin/bash
# 完整诊断并修复502问题
# 在远程服务器 ubuntu@165.154.233.55 上执行

set -e

LOG_FILE="/tmp/fix_502_complete_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee "$LOG_FILE") 2>&1

echo "========================================="
echo "完整诊断并修复 502 Bad Gateway 问题"
echo "开始时间: $(date)"
echo "========================================="
echo ""

# ============================================================================
# 步骤1: 检查前端服务状态
# ============================================================================

echo "【步骤1】检查前端服务状态"
echo "─────────────────────────────────────────"
cd ~/liaotian/saas-demo

echo "1.1 检查进程:"
FRONTEND_PROCESSES=$(ps aux | grep -E 'next.*dev|node.*3000' | grep -v grep || true)
if [ -n "$FRONTEND_PROCESSES" ]; then
    echo "$FRONTEND_PROCESSES"
    echo "  ⚠ 发现前端进程，将停止"
else
    echo "  ✓ 无前端进程运行"
fi
echo ""

echo "1.2 检查端口3000:"
PORT_3000=$(sudo ss -tlnp | grep ':3000 ' || echo "")
if [ -n "$PORT_3000" ]; then
    echo "  ⚠ 端口3000正在被占用:"
    echo "$PORT_3000"
else
    echo "  ✓ 端口3000未监听（需要启动服务）"
fi
echo ""

echo "1.3 测试本地连接:"
LOCAL_3000_TEST=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>&1 || echo "FAILED")
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
    echo "日志文件存在，最后50行:"
    tail -50 /tmp/frontend.log
else
    echo "  ⚠ 日志文件不存在"
fi
echo ""

# ============================================================================
# 步骤3: 检查配置和环境
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
if [ -d node_modules ]; then
    MODULE_COUNT=$(ls node_modules 2>/dev/null | wc -l)
    echo "  ✓ node_modules目录存在，包含 $MODULE_COUNT 个项目"
    
    if [ -f node_modules/.bin/next ]; then
        echo "  ✓ Next.js已安装"
    else
        echo "  ✗ Next.js未安装，需要运行 npm install"
        NEED_INSTALL=true
    fi
else
    echo "  ✗ node_modules目录不存在，需要运行 npm install"
    NEED_INSTALL=true
fi
echo ""

# ============================================================================
# 步骤4: 修复端口配置（如果需要）
# ============================================================================

if [ "$NEED_FIX_PORT" = true ]; then
    echo "【步骤4】修复端口配置"
    echo "─────────────────────────────────────────"
    
    # 使用node修复package.json
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
    npm install 2>&1 | tail -20
    echo "  ✓ npm install 完成"
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

# 后台启动并捕获输出
npm run dev > /tmp/frontend_direct_run.log 2>&1 &
FRONTEND_PID=$!
sleep 30

# 检查进程是否还在运行
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "  ✓ 进程仍在运行（PID: $FRONTEND_PID）"
    echo "  查看输出:"
    cat /tmp/frontend_direct_run.log | tail -30
    
    # 检查是否成功监听3000端口
    if sudo ss -tlnp | grep -q ':3000 '; then
        echo ""
        echo "  ✓ 端口3000正在监听"
        PORT_INFO=$(sudo ss -tlnp | grep ':3000 ')
        echo "  $PORT_INFO"
    else
        echo ""
        echo "  ⚠ 进程在运行但端口3000未监听"
    fi
else
    echo "  ✗ 进程已退出"
    echo "  完整输出:"
    cat /tmp/frontend_direct_run.log
    echo ""
    echo "  错误分析:"
    ERROR_OUTPUT=$(cat /tmp/frontend_direct_run.log)
    
    if echo "$ERROR_OUTPUT" | grep -qi "error.*cannot find module"; then
        echo "    原因: 缺少依赖模块"
        echo "    解决方案: 运行 npm install"
    elif echo "$ERROR_OUTPUT" | grep -qi "port.*already in use"; then
        echo "    原因: 端口被占用"
        echo "    解决方案: 停止占用端口的进程"
    elif echo "$ERROR_OUTPUT" | grep -qi "syntax.*error"; then
        echo "    原因: 代码语法错误"
        echo "    解决方案: 修复代码错误"
    elif echo "$ERROR_OUTPUT" | grep -qi "ENOENT"; then
        echo "    原因: 文件或目录不存在"
        echo "    解决方案: 检查文件路径"
    else
        echo "    未识别错误类型，请查看完整日志"
    fi
    
    exit 1
fi

echo ""

# ============================================================================
# 步骤8: 验证本地连接
# ============================================================================

echo "【步骤8】验证本地连接"
echo "─────────────────────────────────────────"
LOCAL_TEST=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>&1 || echo "FAILED")
if [ "$LOCAL_TEST" = "200" ] || [ "$LOCAL_TEST" = "304" ]; then
    echo "  ✓ http://localhost:3000 返回 HTTP $LOCAL_TEST"
    FRONTEND_OK=true
else
    echo "  ✗ http://localhost:3000 连接失败: $LOCAL_TEST"
    FRONTEND_OK=false
fi
echo ""

if [ "$FRONTEND_OK" = false ]; then
    echo "  前端服务未正常响应，停止进程并退出"
    kill $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

# ============================================================================
# 步骤9: 停止前台进程，改为后台运行
# ============================================================================

echo "【步骤9】改为后台运行"
echo "─────────────────────────────────────────"
kill $FRONTEND_PID 2>/dev/null || true
sleep 2

pkill -f "next.*dev|node.*3000" 2>/dev/null || true
sleep 2

nohup npm run dev > /tmp/frontend.log 2>&1 &
NEW_FRONTEND_PID=$!
sleep 15

if ps -p $NEW_FRONTEND_PID > /dev/null 2>&1; then
    echo "  ✓ 前端服务已在后台启动（PID: $NEW_FRONTEND_PID）"
else
    echo "  ✗ 前端服务启动失败"
    tail -30 /tmp/frontend.log
    exit 1
fi
echo ""

# ============================================================================
# 步骤10: 验证后台服务
# ============================================================================

echo "【步骤10】验证后台服务"
echo "─────────────────────────────────────────"
BACKEND_TEST=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>&1 || echo "000")
FRONTEND_TEST=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>&1 || echo "000")

echo "  后端健康检查: HTTP $BACKEND_TEST"
echo "  前端服务: HTTP $FRONTEND_TEST"

if [ "$FRONTEND_TEST" = "200" ] || [ "$FRONTEND_TEST" = "304" ]; then
    echo "  ✓ 前端服务正常"
else
    echo "  ✗ 前端服务异常，查看日志:"
    tail -30 /tmp/frontend.log
    exit 1
fi
echo ""

# ============================================================================
# 步骤11: 重载Nginx并验证域名
# ============================================================================

echo "【步骤11】重载Nginx并验证域名"
echo "─────────────────────────────────────────"
sudo systemctl reload nginx 2>/dev/null && echo "  ✓ Nginx已重载" || echo "  ✗ Nginx重载失败"
sleep 3

DOMAIN_ACCOUNTS=$(curl -s -o /dev/null -w '%{http_code}' http://aikz.usdt2026.cc/group-ai/accounts 2>&1 || echo "000")
DOMAIN_ROOT=$(curl -s -o /dev/null -w '%{http_code}' http://aikz.usdt2026.cc/ 2>&1 || echo "000")

echo "  域名 /group-ai/accounts: HTTP $DOMAIN_ACCOUNTS"
echo "  域名 /: HTTP $DOMAIN_ROOT"

if [ "$DOMAIN_ACCOUNTS" != "502" ] && [ "$DOMAIN_ROOT" != "502" ]; then
    echo "  ✓ 域名访问不再返回502"
else
    echo "  ✗ 域名访问仍返回502"
    echo "  查看Nginx错误日志:"
    sudo tail -20 /var/log/nginx/error.log
fi
echo ""

# ============================================================================
# 最终总结
# ============================================================================

echo "========================================="
echo "诊断和修复完成！总结报告"
echo "完成时间: $(date)"
echo "========================================="
echo ""
echo "【前端服务状态】"
echo "  进程PID: $NEW_FRONTEND_PID"
echo "  本地测试: HTTP $FRONTEND_TEST"
echo "  域名测试: HTTP $DOMAIN_ACCOUNTS"
echo ""
echo "【修复内容】"
if [ "$NEED_FIX_PORT" = true ]; then
    echo "  - 修复了package.json中的端口配置"
fi
if [ "$NEED_INSTALL" = true ]; then
    echo "  - 重新安装了npm依赖"
fi
echo "  - 重启了前端服务"
echo "  - 重载了Nginx配置"
echo ""
echo "完整日志已保存到: $LOG_FILE"
echo "========================================="
