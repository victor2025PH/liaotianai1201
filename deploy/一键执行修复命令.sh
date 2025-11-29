#!/bin/bash
# 一键执行修复命令
# 在服务器上直接执行此脚本

set -e  # 遇到错误立即退出

echo "========================================"
echo "开始修复前端服务"
echo "========================================"
echo ""

# 步骤1：停止服务
echo "[1/10] 停止前端服务..."
sudo systemctl stop liaotian-frontend || true
echo "✓ 服务已停止"
echo ""

# 步骤2：切换到项目目录
echo "[2/10] 切换到项目目录..."
cd /home/ubuntu/liaotian/saas-demo
pwd
echo ""

# 步骤3：加载Node.js环境
echo "[3/10] 加载Node.js环境..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "✓ Node.js版本: $(node --version)"
echo "✓ npm版本: $(npm --version)"
echo ""

# 步骤4：检查文件
echo "[4/10] 检查关键文件..."
if [ -f "src/app/group-ai/accounts/page.tsx" ]; then
    echo "✓ page.tsx 存在"
    # 检查重复代码
    COUNT=$(grep -c "workerAccounts.map" src/app/group-ai/accounts/page.tsx || echo "0")
    if [ "$COUNT" -eq "1" ]; then
        echo "✓ 无重复代码（workerAccounts.map出现1次）"
    else
        echo "⚠ 警告：workerAccounts.map出现${COUNT}次（应该只出现1次）"
    fi
else
    echo "✗ page.tsx 不存在！需要上传文件"
    exit 1
fi
echo ""

# 步骤5：清理旧构建
echo "[5/10] 清理旧构建..."
rm -rf .next node_modules/.cache
echo "✓ 已清理"
echo ""

# 步骤6：重新构建
echo "[6/10] 重新构建前端..."
echo "这可能需要几分钟，请耐心等待..."
npm run build
if [ $? -ne 0 ]; then
    echo "✗ 构建失败！"
    echo "请查看上面的错误信息"
    exit 1
fi
echo "✓ 构建完成"
echo ""

# 步骤7：验证构建
echo "[7/10] 验证构建结果..."
if [ -f ".next/BUILD_ID" ]; then
    echo "✓ 构建成功 - BUILD_ID存在"
    BUILD_ID=$(cat .next/BUILD_ID)
    echo "  构建ID: $BUILD_ID"
else
    echo "✗ 构建失败 - BUILD_ID不存在"
    exit 1
fi
echo ""

# 步骤8：检查服务配置
echo "[8/10] 检查服务配置..."
if [ -f "/etc/systemd/system/liaotian-frontend.service" ]; then
    echo "✓ 服务配置文件存在"
    # 检查关键配置
    if grep -q "WorkingDirectory=/home/ubuntu/liaotian/saas-demo" /etc/systemd/system/liaotian-frontend.service; then
        echo "✓ 工作目录配置正确"
    else
        echo "⚠ 警告：工作目录配置可能不正确"
    fi
else
    echo "✗ 服务配置文件不存在！"
    exit 1
fi
echo ""

# 步骤9：重新加载并启动服务
echo "[9/10] 重新加载并启动服务..."
sudo systemctl daemon-reload
sudo systemctl start liaotian-frontend
sleep 5
echo "✓ 服务已启动"
echo ""

# 步骤10：检查服务状态
echo "[10/10] 检查服务状态..."
STATUS=$(sudo systemctl is-active liaotian-frontend)
if [ "$STATUS" = "active" ]; then
    echo "✓ 服务运行中"
else
    echo "✗ 服务未运行，状态: $STATUS"
    echo "查看日志："
    sudo journalctl -u liaotian-frontend -n 20 --no-pager
    exit 1
fi
echo ""

# 检查端口
echo "检查端口监听..."
if sudo netstat -tlnp 2>/dev/null | grep ':3000' || sudo ss -tlnp 2>/dev/null | grep ':3000'; then
    echo "✓ 端口3000正在监听"
else
    echo "⚠ 警告：端口3000未监听"
fi
echo ""

echo "========================================"
echo "修复完成！"
echo "========================================"
echo ""
echo "服务状态："
sudo systemctl status liaotian-frontend --no-pager | head -10
echo ""
echo "下一步："
echo "1. 清除浏览器缓存（Ctrl+Shift+Delete）"
echo "2. 强制刷新页面（Ctrl+F5）"
echo "3. 访问 http://aikz.usdt2026.cc"
echo ""

