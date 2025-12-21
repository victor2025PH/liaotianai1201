#!/bin/bash
# ============================================================
# 检查三个网站的部署状态
# ============================================================

set -e

echo "============================================================"
echo "🔍 检查三个网站的部署状态"
echo "============================================================"
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 检查项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# 检查三个网站目录
SITES=(
    "tgmini20251220:tgmini.usdt2026.cc:3001"
    "hbwy20251220:hongbao.usdt2026.cc:3002"
    "aizkw20251219:aikz.usdt2026.cc:3003"
)

for SITE_INFO in "${SITES[@]}"; do
    IFS=':' read -r DIR DOMAIN PORT <<< "$SITE_INFO"
    SITE_DIR="$PROJECT_DIR/$DIR"
    
    echo "============================================================"
    echo "📊 检查: $DIR"
    echo "域名: $DOMAIN"
    echo "端口: $PORT"
    echo "============================================================"
    
    # 检查目录
    if [ ! -d "$SITE_DIR" ]; then
        echo "❌ 目录不存在: $SITE_DIR"
        continue
    fi
    echo "✅ 目录存在"
    
    # 检查 package.json
    if [ ! -f "$SITE_DIR/package.json" ]; then
        echo "❌ package.json 不存在"
        continue
    fi
    echo "✅ package.json 存在"
    
    # 检查 dist 目录
    if [ ! -d "$SITE_DIR/dist" ]; then
        echo "⚠️  dist 目录不存在（可能未构建）"
    else
        echo "✅ dist 目录存在"
        echo "   文件数量: $(find "$SITE_DIR/dist" -type f | wc -l)"
    fi
    
    # 检查 PM2 进程
    PM2_NAME="${DIR//202512*/}-frontend"
    if pm2 list | grep -q "$PM2_NAME"; then
        echo "✅ PM2 进程存在: $PM2_NAME"
        pm2 info "$PM2_NAME" | grep -E "status|uptime|memory" || true
    else
        echo "❌ PM2 进程不存在: $PM2_NAME"
    fi
    
    # 检查端口
    if sudo lsof -i :$PORT >/dev/null 2>&1; then
        echo "✅ 端口 $PORT 正在监听"
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT || echo "000")
        echo "   HTTP 状态码: $HTTP_CODE"
    else
        echo "❌ 端口 $PORT 未在监听"
    fi
    
    # 检查 Nginx 配置
    if [ -f "/etc/nginx/sites-available/$DOMAIN" ]; then
        echo "✅ Nginx 配置存在"
        if [ -L "/etc/nginx/sites-enabled/$DOMAIN" ]; then
            echo "✅ Nginx 配置已启用"
        else
            echo "⚠️  Nginx 配置未启用"
        fi
    else
        echo "❌ Nginx 配置不存在"
    fi
    
    echo ""
done

# 检查 Nginx 状态
echo "============================================================"
echo "🌐 Nginx 状态"
echo "============================================================"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
else
    echo "❌ Nginx 未运行"
fi

# 检查 PM2 状态
echo ""
echo "============================================================"
echo "📦 PM2 进程列表"
echo "============================================================"
pm2 list || echo "PM2 未安装或未运行"

echo ""
echo "============================================================"
echo "✅ 检查完成"
echo "============================================================"
