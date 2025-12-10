#!/bin/bash
# 直接修复 Next.js 服务

# 查找项目目录
PROJECT_DIRS=(
    "/home/ubuntu/telegram-ai-system/saas-demo"
    "/home/ubuntu/liaotian/saas-demo"
    "/var/www/liaotian/saas-demo"
)

PROJECT_DIR=""
for dir in "${PROJECT_DIRS[@]}"; do
    if [ -f "$dir/package.json" ]; then
        PROJECT_DIR="$dir"
        break
    fi
done

if [ -z "$PROJECT_DIR" ]; then
    echo "错误：未找到项目目录"
    exit 1
fi

echo "使用项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR"

# 1. 确保在项目根目录
if [ ! -f "package.json" ]; then
    echo "错误：请先进入项目根目录"
    exit 1
fi

# 2. 暴力杀死所有占用 3000 端口的进程
echo "正在清理旧进程..."
fuser -k 3000/tcp 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
sleep 2

# 3. 彻底删除缓存文件夹
echo "正在清理构建缓存..."
rm -rf .next
echo "✅ .next 目录已删除"

# 4. 重新构建
echo "正在重新构建..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20 || true
npm run build
echo "✅ 构建完成"

# 5. 后台启动服务
echo "正在启动服务..."
nohup npm run start > app.log 2>&1 &
echo "✅ 服务已启动（后台运行）"

# 6. 验证启动结果
sleep 5
echo ""
echo "=== 服务日志（前 20 行）==="
cat app.log | head -n 20

echo ""
echo "=== 检查端口 3000 ==="
ss -tlnp | grep :3000 || echo "端口 3000 未监听"

echo ""
echo "=== 检查进程 ==="
ps aux | grep -E "next-server|npm.*start" | grep -v grep || echo "未找到进程"

