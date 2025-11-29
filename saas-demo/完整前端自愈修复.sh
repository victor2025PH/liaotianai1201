#!/bin/bash
# 完整前端自愈诊断和修复

set -e

cd ~/liaotian/saas-demo

echo "========================================"
echo "前端自愈诊断和修复系统"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

LOG_FILE="/tmp/frontend_auto_fix_$(date +%s).log"
{
    echo "========================================"
    echo "前端自愈修复日志"
    echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo ""
} > "$LOG_FILE"

# 函数：记录步骤
log_step() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo "" | tee -a "$LOG_FILE"
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 1. 环境检查
log_step "[1] 环境信息检查"

echo "工作目录: $(pwd)" | tee -a "$LOG_FILE"
echo "Node 版本: $(node -v 2>&1)" | tee -a "$LOG_FILE"
echo "npm 版本: $(npm -v 2>&1)" | tee -a "$LOG_FILE"

if [ ! -f "package.json" ]; then
    echo "❌ 错误: 找不到 package.json" | tee -a "$LOG_FILE"
    exit 1
fi

if ! grep -q '"next"' package.json; then
    echo "❌ 错误: 这不是一个 Next.js 项目" | tee -a "$LOG_FILE"
    exit 1
fi

echo "✅ 确认为 Next.js 项目" | tee -a "$LOG_FILE"

# 2. 检查并修复 package.json 端口配置
log_step "[2] 检查 package.json 配置"

if grep -q '"dev": "next dev -p 3001"' package.json; then
    echo "⚠️  发现端口配置为 3001，需要改为 3000" | tee -a "$LOG_FILE"
    sed -i 's/"dev": "next dev -p 3001"/"dev": "next dev -p 3000"/g' package.json
    echo "✅ 已修复端口配置为 3000" | tee -a "$LOG_FILE"
fi

# 3. 停止旧进程
log_step "[3] 停止旧进程"

pkill -f "next.*dev\|node.*3000\|node.*3001" || true
sleep 2

# 清理端口
if sudo lsof -i :3000 2>/dev/null | grep -q LISTEN; then
    echo "清理端口 3000..." | tee -a "$LOG_FILE"
    sudo lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 4. 尝试运行并捕获错误
log_step "[4] 尝试运行 npm run dev 并捕获错误"

timeout 30 npm run dev > /tmp/frontend_error.log 2>&1 &
DEV_PID=$!
sleep 10

if ! ps -p $DEV_PID > /dev/null 2>&1; then
    echo "❌ 进程启动后立即退出" | tee -a "$LOG_FILE"
    echo "错误信息:" | tee -a "$LOG_FILE"
    cat /tmp/frontend_error.log | tee -a "$LOG_FILE"
    ERROR_FOUND=true
else
    kill $DEV_PID 2>/dev/null || true
    wait $DEV_PID 2>/dev/null || true
    ERROR_FOUND=false
fi

# 5. 分析错误并修复依赖
if [ "$ERROR_FOUND" = true ] || [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/next" ]; then
    log_step "[5] 修复依赖问题"
    
    echo "检查依赖状态..." | tee -a "$LOG_FILE"
    
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/next" ]; then
        echo "⚠️  依赖不完整，重新安装..." | tee -a "$LOG_FILE"
        rm -rf node_modules package-lock.json
        npm install 2>&1 | tee -a "$LOG_FILE"
        
        if [ $? -eq 0 ]; then
            echo "✅ 依赖安装成功" | tee -a "$LOG_FILE"
        else
            echo "❌ 依赖安装失败，查看错误信息" | tee -a "$LOG_FILE"
            exit 1
        fi
    else
        echo "✅ 依赖存在" | tee -a "$LOG_FILE"
    fi
fi

# 6. 检查构建
log_step "[6] 检查构建状态"

if [ ! -d ".next" ]; then
    echo "⚠️  .next 目录不存在，开始构建..." | tee -a "$LOG_FILE"
    npm run build 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ 构建成功" | tee -a "$LOG_FILE"
    else
        echo "❌ 构建失败，查看错误信息" | tee -a "$LOG_FILE"
        # 尝试修复常见构建错误
        echo "尝试清理并重新构建..." | tee -a "$LOG_FILE"
        rm -rf .next
        npm run build 2>&1 | tee -a "$LOG_FILE" || {
            echo "构建仍然失败，需要人工检查" | tee -a "$LOG_FILE"
        }
    fi
else
    echo "✅ .next 目录存在" | tee -a "$LOG_FILE"
fi

# 7. 最终验证启动
log_step "[7] 最终验证启动"

pkill -f "next.*dev\|node.*3000" || true
sleep 2

echo "启动开发服务器..." | tee -a "$LOG_FILE"
npm run dev > /tmp/frontend_final.log 2>&1 &
FINAL_PID=$!
echo "进程 PID: $FINAL_PID" | tee -a "$LOG_FILE"

echo "等待服务器启动（45秒）..." | tee -a "$LOG_FILE"
sleep 45

# 检查进程
if ps -p $FINAL_PID > /dev/null 2>&1; then
    echo "✅ 进程正在运行" | tee -a "$LOG_FILE"
else
    echo "❌ 进程已退出" | tee -a "$LOG_FILE"
    echo "查看启动日志:" | tee -a "$LOG_FILE"
    tail -50 /tmp/frontend_final.log | tee -a "$LOG_FILE"
fi

# 检查端口
echo "" | tee -a "$LOG_FILE"
echo "检查端口 3000..." | tee -a "$LOG_FILE"
if curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 端口 3000 可以访问" | tee -a "$LOG_FILE"
    SUCCESS=true
else
    echo "❌ 端口 3000 无法访问" | tee -a "$LOG_FILE"
    echo "查看启动日志:" | tee -a "$LOG_FILE"
    tail -50 /tmp/frontend_final.log | tee -a "$LOG_FILE"
    SUCCESS=false
fi

# 8. 总结
log_step "[8] 修复总结"

{
    echo ""
    echo "========================================"
    echo "修复完成"
    echo "========================================"
    echo ""
    echo "日志文件: $LOG_FILE"
    echo "启动日志: /tmp/frontend_final.log"
    echo ""
    
    if [ "$SUCCESS" = true ]; then
        echo "✅ 前端服务已成功启动在端口 3000"
        echo ""
        echo "验证命令:"
        echo "  curl http://localhost:3000"
        echo "  或访问: http://aikz.usdt2026.cc/group-ai/accounts"
    else
        echo "⚠️  前端服务可能仍在启动中或存在问题"
        echo ""
        echo "查看日志:"
        echo "  tail -f $LOG_FILE"
        echo "  tail -f /tmp/frontend_final.log"
    fi
} | tee -a "$LOG_FILE"

# 输出日志位置
echo ""
echo "完整日志: $LOG_FILE"
