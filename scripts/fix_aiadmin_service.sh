#!/bin/bash
# 修复 aiadmin.usdt2026.cc 服务问题
# 根据诊断结果：端口 3007 未占用或返回错误内容

echo "=========================================="
echo "修复 aiadmin.usdt2026.cc 服务"
echo "=========================================="
echo ""

PROJECT_DIR="/opt/web3-sites"
FRONTEND_DIR="$PROJECT_DIR/sites-admin-frontend"
PORT=3007

# 1. 检查目录是否存在
echo "1. 检查项目目录"
echo "----------------------------------------"
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 前端目录不存在: $FRONTEND_DIR"
    exit 1
fi
echo "✅ 前端目录存在: $FRONTEND_DIR"
echo ""

# 2. 停止可能占用端口的进程
echo "2. 停止占用端口 $PORT 的进程"
echo "----------------------------------------"
if sudo lsof -ti:$PORT >/dev/null 2>&1; then
    echo "发现占用端口 $PORT 的进程，正在停止..."
    sudo lsof -ti:$PORT | xargs sudo kill -9 2>/dev/null || true
    sleep 2
    echo "✅ 端口 $PORT 已释放"
else
    echo "✅ 端口 $PORT 未被占用"
fi

# 停止 PM2 中的 sites-admin-frontend
echo ""
echo "停止 PM2 进程 sites-admin-frontend..."
pm2 delete sites-admin-frontend 2>/dev/null || true
echo "✅ PM2 进程已停止"
echo ""

# 3. 检查前端构建
echo "3. 检查前端构建"
echo "----------------------------------------"
cd "$FRONTEND_DIR" || exit 1

if [ ! -d ".next" ]; then
    echo "⚠️  .next 目录不存在，需要构建"
    echo "正在安装依赖..."
    npm install
    echo "正在构建..."
    npm run build
else
    echo "✅ .next 目录存在"
fi

# 检查 package.json 中的启动脚本
if [ ! -f "package.json" ]; then
    echo "❌ package.json 不存在"
    exit 1
fi

echo "✅ package.json 存在"
echo ""

# 4. 启动服务
echo "4. 启动管理后台前端服务"
echo "----------------------------------------"

# 检查是否使用 Next.js
if grep -q "\"next\"" package.json; then
    echo "检测到 Next.js 项目"
    echo "使用 PM2 启动 Next.js 服务..."
    
    # 使用 PM2 启动
    pm2 start npm --name sites-admin-frontend -- start -- --port $PORT || {
        echo "❌ PM2 启动失败，尝试直接启动..."
        # 备用方案：直接启动
        nohup npm start -- --port $PORT > /tmp/sites-admin-frontend.log 2>&1 &
        echo "✅ 服务已在后台启动（PID: $!）"
    }
else
    echo "未检测到 Next.js，检查是否有其他启动方式..."
    # 可能需要使用 serve 或其他方式
    if command -v serve >/dev/null 2>&1; then
        echo "使用 serve 启动静态文件服务..."
        if [ -d "out" ]; then
            pm2 start serve --name sites-admin-frontend -- -s out -l $PORT
        elif [ -d ".next" ]; then
            # Next.js standalone 模式
            if [ -d ".next/standalone" ]; then
                cd .next/standalone
                pm2 start server.js --name sites-admin-frontend -- --port $PORT
            else
                echo "❌ 未找到构建输出目录"
                exit 1
            fi
        else
            echo "❌ 未找到可用的构建输出"
            exit 1
        fi
    else
        echo "❌ serve 命令不存在，请先安装: npm install -g serve"
        exit 1
    fi
fi

pm2 save
echo "✅ 服务启动完成"
echo ""

# 5. 等待服务启动
echo "5. 等待服务启动并验证"
echo "----------------------------------------"
sleep 5

# 检查端口是否监听
if sudo lsof -ti:$PORT >/dev/null 2>&1; then
    echo "✅ 端口 $PORT 正在监听"
    
    # 检查 HTTP 响应
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT 2>&1)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ 服务响应正常 (HTTP $HTTP_CODE)"
        
        # 检查返回内容
        CONTENT=$(curl -s http://127.0.0.1:$PORT 2>&1)
        if echo "$CONTENT" | grep -qi "三个展示网站管理后台\|sites-admin\|站点概览"; then
            echo "✅ 服务返回的是管理后台内容"
        elif echo "$CONTENT" | grep -qi "智控王\|aizkw"; then
            echo "❌ 警告：服务仍然返回 aizkw 内容，可能需要检查配置"
        else
            echo "⚠️  无法识别返回内容类型"
        fi
    else
        echo "⚠️  服务响应异常 (HTTP $HTTP_CODE)"
    fi
else
    echo "❌ 端口 $PORT 未在监听，服务可能启动失败"
    echo "查看 PM2 日志："
    pm2 logs sites-admin-frontend --lines 20 --nostream 2>/dev/null || true
    exit 1
fi

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "服务状态："
pm2 list | grep sites-admin-frontend || echo "PM2 进程列表中没有找到"
echo ""
echo "访问地址: http://aiadmin.usdt2026.cc"
echo ""

