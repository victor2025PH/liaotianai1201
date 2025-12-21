#!/bin/bash

# 检查页面空白问题的诊断脚本

set -e

echo "=========================================="
echo "🔍 检查页面空白问题"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

# 检查三个项目
declare -A PROJECTS=(
    ["aizkw"]="aizkw20251219"
    ["hongbao"]="hbwy20251220"
    ["tgmini"]="tgmini20251220"
)

for project_name in "${!PROJECTS[@]}"; do
    project_dir="${PROJECTS[$project_name]}"
    project_path="$PROJECT_ROOT/$project_dir"
    
    echo "=========================================="
    echo "📁 检查项目: $project_name"
    echo "目录: $project_path"
    echo "=========================================="
    echo ""
    
    if [ ! -d "$project_path" ]; then
        echo "❌ 项目目录不存在"
        echo ""
        continue
    fi
    
    # 检查 dist 目录
    if [ ! -d "$project_path/dist" ]; then
        echo "❌ dist 目录不存在（项目未构建）"
        echo ""
        continue
    fi
    
    echo "✅ dist 目录存在"
    echo ""
    
    # 检查 index.html
    DIST_INDEX="$project_path/dist/index.html"
    if [ ! -f "$DIST_INDEX" ]; then
        echo "❌ dist/index.html 不存在"
        echo ""
        continue
    fi
    
    echo "✅ dist/index.html 存在"
    echo ""
    
    # 检查是否包含 CDN 引用
    echo "检查 CDN 引用..."
    if grep -qi "cdn.tailwindcss.com" "$DIST_INDEX" 2>/dev/null; then
        echo "⚠️  发现 Tailwind CDN 引用（不应该在生产环境使用）"
        grep -i "cdn.tailwindcss.com" "$DIST_INDEX" | head -3
    else
        echo "✅ 没有 Tailwind CDN 引用"
    fi
    
    if grep -qi "esm.sh" "$DIST_INDEX" 2>/dev/null; then
        echo "⚠️  发现 ES Modules CDN 引用（可能导致加载失败）"
        grep -i "esm.sh" "$DIST_INDEX" | head -3
    else
        echo "✅ 没有 ES Modules CDN 引用"
    fi
    
    echo ""
    
    # 检查 assets 目录
    ASSETS_DIR="$project_path/dist/assets"
    if [ -d "$ASSETS_DIR" ]; then
        ASSET_COUNT=$(find "$ASSETS_DIR" -type f | wc -l)
        echo "✅ assets 目录存在，包含 $ASSET_COUNT 个文件"
        
        # 列出主要资源文件
        echo "主要资源文件："
        ls -lh "$ASSETS_DIR" | head -5 | awk '{print "  " $9 " (" $5 ")"}'
    else
        echo "⚠️  assets 目录不存在（可能构建不完整）"
    fi
    
    echo ""
    
    # 检查服务状态
    case $project_name in
        "aizkw")
            PORT=3003
            ;;
        "hongbao")
            PORT=3002
            ;;
        "tgmini")
            PORT=3001
            ;;
    esac
    
    echo "检查服务状态（端口 $PORT）..."
    if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
        echo "✅ 端口 $PORT 正在监听"
        
        # 测试 HTTP 响应
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT || echo "000")
        if [ "$HTTP_CODE" = "200" ]; then
            echo "✅ 服务响应正常 (HTTP $HTTP_CODE)"
        else
            echo "⚠️  服务响应异常 (HTTP $HTTP_CODE)"
        fi
    else
        echo "❌ 端口 $PORT 未监听"
    fi
    
    echo ""
    echo ""
done

echo "=========================================="
echo "📊 诊断总结"
echo "=========================================="
echo ""
echo "如果发现 CDN 引用："
echo "1. 需要安装 Tailwind CSS 作为 PostCSS 插件"
echo "2. 需要移除 index.html 中的 CDN 引用"
echo "3. 需要重新构建项目"
echo ""
echo "如果 dist 目录不完整："
echo "1. 运行: cd /home/ubuntu/telegram-ai-system"
echo "2. 运行: sudo bash scripts/server/build_and_start_all.sh"
echo ""
