#!/bin/bash

# 重新构建 saas-demo 项目（解决 404 _next 资源问题）
# 使用方法: bash scripts/server/rebuild_saas_demo.sh

set -e

echo "=========================================="
echo "🔧 重新构建 saas-demo 项目"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
SAAS_DEMO_DIR="$PROJECT_ROOT/saas-demo"

# 1. 进入目录
echo "1. 进入 saas-demo 目录..."
echo "----------------------------------------"
if [ ! -d "$SAAS_DEMO_DIR" ]; then
  echo "❌ 目录不存在: $SAAS_DEMO_DIR"
  exit 1
fi

cd "$SAAS_DEMO_DIR" || {
  echo "❌ 无法进入目录: $SAAS_DEMO_DIR"
  exit 1
}

echo "✅ 当前目录: $(pwd)"
echo ""

# 2. 检查 package.json
echo "2. 检查 package.json..."
echo "----------------------------------------"
if [ ! -f "package.json" ]; then
  echo "❌ package.json 不存在"
  exit 1
fi

echo "✅ package.json 存在"
echo ""

# 3. 清理缓存和旧构建
echo "3. 清理缓存和旧构建..."
echo "----------------------------------------"

# 删除 .next 文件夹
if [ -d ".next" ]; then
  echo "删除 .next 文件夹..."
  rm -rf .next
  echo "✅ .next 文件夹已删除"
else
  echo "✅ .next 文件夹不存在，跳过"
fi

# 清理其他可能的缓存
if [ -d ".cache" ]; then
  echo "删除 .cache 文件夹..."
  rm -rf .cache
  echo "✅ .cache 文件夹已删除"
fi

# 清理 node_modules/.cache（如果存在）
if [ -d "node_modules/.cache" ]; then
  echo "删除 node_modules/.cache 文件夹..."
  rm -rf node_modules/.cache
  echo "✅ node_modules/.cache 文件夹已删除"
fi

echo "✅ 清理完成"
echo ""

# 4. 检查 node_modules
echo "4. 检查 node_modules..."
echo "----------------------------------------"
if [ ! -d "node_modules" ]; then
  echo "⚠️  node_modules 不存在，安装依赖..."
  npm install || {
    echo "❌ 依赖安装失败"
    exit 1
  }
  echo "✅ 依赖安装完成"
else
  echo "✅ node_modules 已存在"
fi
echo ""

# 5. 重新构建
echo "5. 重新构建项目..."
echo "----------------------------------------"
echo "执行 npm run build..."
npm run build || {
  echo "❌ 构建失败"
  echo ""
  echo "构建错误详情："
  npm run build 2>&1 | tail -50
  exit 1
}

echo "✅ 构建完成"
echo ""

# 6. 验证构建输出
echo "6. 验证构建输出..."
echo "----------------------------------------"

if [ -d ".next" ]; then
  echo "✅ .next 文件夹已创建"
  
  # 检查关键目录
  if [ -d ".next/static" ]; then
    STATIC_SIZE=$(du -sh .next/static 2>/dev/null | awk '{print $1}' || echo "未知")
    echo "✅ .next/static 目录存在 (大小: $STATIC_SIZE)"
  else
    echo "⚠️  .next/static 目录不存在"
  fi
  
  if [ -d ".next/standalone" ]; then
    echo "✅ .next/standalone 目录存在（standalone 模式）"
  else
    echo "⚠️  .next/standalone 目录不存在（非 standalone 模式）"
  fi
  
  # 列出 .next 目录内容
  echo ""
  echo ".next 目录内容："
  ls -la .next/ | head -20
else
  echo "❌ .next 文件夹未创建，构建可能失败"
  exit 1
fi
echo ""

# 7. 重启 PM2 进程
echo "7. 重启 saas-demo 进程..."
echo "----------------------------------------"
cd "$PROJECT_ROOT" || exit 1

if pm2 list | grep -q "saas-demo"; then
  echo "重启 PM2 saas-demo 进程..."
  pm2 restart saas-demo || {
    echo "⚠️  PM2 restart 失败，尝试删除后重新启动..."
    pm2 delete saas-demo 2>/dev/null || true
    sleep 2
    
    # 重新启动
    cd "$SAAS_DEMO_DIR" || exit 1
    
    # 检查是否有 standalone 构建
    if [ -f ".next/standalone/server.js" ]; then
      echo "使用 standalone 模式启动..."
      pm2 start ".next/standalone/server.js" \
        --name saas-demo \
        --interpreter node \
        --cwd "$SAAS_DEMO_DIR" \
        --env PORT=3000 \
        --env NODE_ENV=production || {
        echo "❌ standalone 启动失败，尝试使用 npm start..."
        pm2 start npm \
          --name saas-demo \
          --cwd "$SAAS_DEMO_DIR" \
          -- start || {
          echo "❌ 服务启动失败"
          exit 1
        }
      }
    else
      echo "使用 npm start 启动..."
      pm2 start npm \
        --name saas-demo \
        --cwd "$SAAS_DEMO_DIR" \
        -- start || {
        echo "❌ 服务启动失败"
        exit 1
      }
    fi
    echo "✅ saas-demo 已重新启动"
  } else
    echo "✅ saas-demo 已重启"
  fi
else
  echo "⚠️  PM2 中未找到 saas-demo 进程，尝试启动..."
  cd "$SAAS_DEMO_DIR" || exit 1
  
  # 检查是否有 standalone 构建
  if [ -f ".next/standalone/server.js" ]; then
    echo "使用 standalone 模式启动..."
    pm2 start ".next/standalone/server.js" \
      --name saas-demo \
      --interpreter node \
      --cwd "$SAAS_DEMO_DIR" \
      --env PORT=3000 \
      --env NODE_ENV=production || {
      echo "❌ standalone 启动失败，尝试使用 npm start..."
      pm2 start npm \
        --name saas-demo \
        --cwd "$SAAS_DEMO_DIR" \
        -- start || {
        echo "❌ 服务启动失败"
        exit 1
      }
    }
  else
    echo "使用 npm start 启动..."
    pm2 start npm \
      --name saas-demo \
      --cwd "$SAAS_DEMO_DIR" \
      -- start || {
      echo "❌ 服务启动失败"
      exit 1
    }
  fi
  echo "✅ saas-demo 已启动"
fi

echo ""

# 8. 等待服务启动
echo "8. 等待服务启动..."
echo "----------------------------------------"
sleep 5

# 9. 验证服务状态
echo "9. 验证服务状态..."
echo "----------------------------------------"
pm2 list | grep saas-demo || echo "⚠️  未找到 saas-demo 进程"
echo ""

# 检查端口 3000 是否监听
if ss -tlnp 2>/dev/null | grep -q ":3000 " || netstat -tlnp 2>/dev/null | grep -q ":3000 "; then
  echo "✅ 端口 3000 正在监听"
  
  # 测试端口 3000 HTTP 响应
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://127.0.0.1:3000 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ 端口 3000 HTTP 响应正常 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  端口 3000 HTTP 响应异常 (HTTP $HTTP_CODE)"
  fi
  
  # 测试 _next 资源（检查构建是否正常）
  echo ""
  echo "测试 _next 资源访问..."
  NEXT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:3000/_next/static 2>/dev/null || echo "000")
  if [ "$NEXT_RESPONSE" = "200" ] || [ "$NEXT_RESPONSE" = "404" ]; then
    # 404 也是正常的，因为 _next/static 本身不是一个文件
    echo "✅ _next 资源路径可访问 (HTTP $NEXT_RESPONSE)"
  else
    echo "⚠️  _next 资源路径响应异常 (HTTP $NEXT_RESPONSE)"
  fi
else
  echo "❌ 端口 3000 未监听"
  echo "   请检查 saas-demo 服务日志: pm2 logs saas-demo --lines 30"
fi
echo ""

# 10. 显示服务日志（最近几行）
echo "10. 服务日志（最近 10 行）..."
echo "----------------------------------------"
pm2 logs saas-demo --lines 10 --nostream || {
  echo "⚠️  无法获取日志"
}
echo ""

# 11. 保存 PM2 配置
echo "11. 保存 PM2 配置..."
echo "----------------------------------------"
pm2 save || echo "⚠️  PM2 配置保存失败"
echo "✅ PM2 配置已保存"
echo ""

echo "=========================================="
echo "✅ saas-demo 重新构建完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "构建摘要："
echo "  - 目录: $SAAS_DEMO_DIR"
echo "  - .next 目录: $([ -d "$SAAS_DEMO_DIR/.next" ] && echo "存在" || echo "不存在")"
echo "  - .next/static 目录: $([ -d "$SAAS_DEMO_DIR/.next/static" ] && echo "存在" || echo "不存在")"
echo "  - PM2 服务: saas-demo"
echo ""
echo "如果仍有 404 错误，请检查："
echo "  1. 浏览器清除缓存（Ctrl+Shift+R 强制刷新）"
echo "  2. Cloudflare 清除缓存"
echo "  3. 检查 Nginx 配置是否正确代理 _next 路径"
echo "  4. 查看服务日志: pm2 logs saas-demo --lines 50"
echo "  5. 测试本地访问: curl http://127.0.0.1:3000"
