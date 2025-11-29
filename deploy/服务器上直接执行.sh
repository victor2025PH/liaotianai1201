#!/bin/bash
# 在服务器上直接执行的修复脚本
# 使用方法：将此脚本上传到服务器后执行，或通过SSH执行

set -e

echo "========================================"
echo "修复前端服务 - 在服务器上直接执行"
echo "========================================"
echo ""

# 1. 停止服务
echo "[1/7] 停止前端服务..."
sudo systemctl stop liaotian-frontend || true
echo "[OK] 服务已停止"
echo ""

# 2. 切换到项目目录
cd /home/ubuntu/liaotian/saas-demo

# 3. 加载nvm
echo "[2/7] 加载nvm..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "[OK] Node.js版本: $(node --version)"
echo ""

# 4. 清理旧构建
echo "[3/7] 清理旧构建..."
rm -rf .next node_modules/.cache
echo "[OK] 已清理"
echo ""

# 5. 重新构建
echo "[4/7] 重新构建前端..."
echo "这可能需要几分钟，请耐心等待..."
npm run build
if [ $? -ne 0 ]; then
    echo "[错误] 构建失败！"
    echo "请查看上面的错误信息"
    exit 1
fi
echo "[OK] 构建完成"
echo ""

# 6. 验证构建
echo "[5/7] 验证构建结果..."
if [ -f .next/BUILD_ID ]; then
    echo "[OK] 构建成功 - BUILD_ID存在"
else
    echo "[错误] 构建失败 - BUILD_ID不存在"
    exit 1
fi
echo ""

# 7. 重新加载并启动服务
echo "[6/7] 重新加载并启动服务..."
sudo systemctl daemon-reload
sudo systemctl start liaotian-frontend
sleep 3
echo "[OK] 服务已启动"
echo ""

# 8. 检查服务状态
echo "[7/7] 检查服务状态..."
sudo systemctl status liaotian-frontend --no-pager | head -20
echo ""

# 9. 检查端口
echo "检查端口监听..."
if sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000'; then
    echo "[OK] 端口3000正在监听"
else
    echo "[警告] 端口3000未监听"
fi
echo ""

echo "========================================"
echo "修复完成！"
echo "========================================"
echo ""
echo "如果服务状态显示 'active (running)'，说明修复成功。"
echo ""

