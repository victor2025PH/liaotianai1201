#!/bin/bash
# 完整修复脚本 - 在服务器上直接执行

set -e

echo "========================================"
echo "完整修复前端服务"
echo "========================================"
echo ""

# 1. 停止服务
echo "[1/8] 停止服务..."
sudo systemctl stop liaotian-frontend || true
echo "✓ 服务已停止"
echo ""

# 2. 切换到项目目录
cd /home/ubuntu/liaotian/saas-demo

# 3. 加载nvm
echo "[2/8] 加载Node.js环境..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "✓ Node.js $(node --version)"
echo ""

# 4. 检查文件
echo "[3/8] 检查文件..."
if [ ! -f "src/app/group-ai/accounts/page.tsx" ]; then
    echo "✗ 文件不存在！"
    exit 1
fi
echo "✓ 文件存在"

# 检查workerAccounts.map出现次数
COUNT=$(grep -c "workerAccounts.map" src/app/group-ai/accounts/page.tsx || echo "0")
echo "workerAccounts.map出现次数: $COUNT"
if [ "$COUNT" != "1" ]; then
    echo "⚠ 警告：应该只出现1次"
fi
echo ""

# 5. 查看第2023行附近
echo "[4/8] 查看第2023行附近的内容..."
sed -n '2018,2028p' src/app/group-ai/accounts/page.tsx | cat -n
echo ""

# 6. 清理
echo "[5/8] 清理旧构建..."
rm -rf .next node_modules/.cache
echo "✓ 已清理"
echo ""

# 7. 构建
echo "[6/8] 重新构建..."
echo "这可能需要几分钟..."
npm run build 2>&1 | tee /tmp/build.log
BUILD_EXIT=${PIPESTATUS[0]}

if [ $BUILD_EXIT -ne 0 ]; then
    echo ""
    echo "✗ 构建失败！"
    echo "错误信息（最后50行）："
    tail -50 /tmp/build.log
    echo ""
    echo "查看完整日志: cat /tmp/build.log"
    exit 1
fi

echo ""
echo "✓ 构建完成"
echo ""

# 8. 验证构建
echo "[7/8] 验证构建..."
if [ -f ".next/BUILD_ID" ]; then
    BUILD_ID=$(cat .next/BUILD_ID)
    echo "✓ 构建成功 - BUILD_ID: $BUILD_ID"
else
    echo "✗ 构建失败 - BUILD_ID不存在"
    exit 1
fi
echo ""

# 9. 重启服务
echo "[8/8] 重启服务..."
sudo systemctl daemon-reload
sudo systemctl start liaotian-frontend
sleep 5
echo "✓ 服务已重启"
echo ""

# 10. 检查状态
echo "检查服务状态..."
sudo systemctl status liaotian-frontend --no-pager | head -20
echo ""

# 11. 检查端口
echo "检查端口监听..."
if sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000'; then
    echo "✓ 端口3000正在监听"
else
    echo "⚠ 端口3000未监听"
fi
echo ""

echo "========================================"
echo "修复完成！"
echo "========================================"
echo ""
echo "如果服务状态显示 'active (running)'，说明修复成功。"
echo "请清除浏览器缓存并刷新页面。"
echo ""

