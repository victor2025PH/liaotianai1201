#!/bin/bash
# 马尼拉服务器快速部署脚本

set -e

HOST="165.154.233.55"
USER="ubuntu"
REMOTE_DIR="/home/ubuntu/saas-demo"

echo "=========================================="
echo "马尼拉服务器部署脚本"
echo "=========================================="
echo ""
echo "服务器: $USER@$HOST"
echo ""

# 检查是否在服务器上
if [ "$HOSTNAME" != "10-11-156-159" ] && [ -z "$SSH_CONNECTION" ]; then
    echo "请在服务器上执行此脚本，或使用以下命令:"
    echo "  ssh $USER@$HOST"
    echo "  然后执行此脚本"
    exit 1
fi

echo "[1] 进入前端目录..."
cd $REMOTE_DIR || {
    echo "[ERROR] 目录不存在: $REMOTE_DIR"
    echo "请先确认前端代码已部署"
    exit 1
}

echo "[OK] 目录: $(pwd)"

echo ""
echo "[2] 备份原文件..."
cp src/components/layout-wrapper.tsx src/components/layout-wrapper.tsx.bak.$(date +%Y%m%d_%H%M%S)
echo "[OK] 备份完成"

echo ""
echo "[3] 请编辑文件并粘贴修复后的代码:"
echo "   文件: src/components/layout-wrapper.tsx"
echo "   命令: nano src/components/layout-wrapper.tsx"
echo ""
echo "   在 nano 中:"
echo "   - 删除所有内容（多次按 Ctrl+K）"
echo "   - 按 Ctrl+V 粘贴修复后的代码"
echo "   - 按 Ctrl+O 保存"
echo "   - 按 Enter 确认"
echo "   - 按 Ctrl+X 退出"
echo ""
read -p "编辑完成后按 Enter 继续..."

echo ""
echo "[4] 验证文件..."
if grep -q "setChecking(false); // 先停止檢查狀態" src/components/layout-wrapper.tsx; then
    echo "[OK] 文件包含修复"
else
    echo "[WARNING] 文件可能未包含修复"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "[5] 检查 Node.js 版本..."
source ~/.nvm/nvm.sh 2>/dev/null || echo "[WARNING] nvm 未找到，尝试使用系统 Node.js"

if command -v nvm &> /dev/null; then
    nvm use 20 2>/dev/null || {
        echo "  安装 Node.js 20..."
        nvm install 20
        nvm use 20
        nvm alias default 20
    }
fi

NODE_VERSION=$(node --version)
echo "  Node.js 版本: $NODE_VERSION"

if [[ ! "$NODE_VERSION" =~ ^v20 ]]; then
    echo "[WARNING] 需要 Node.js 20，当前版本: $NODE_VERSION"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "[6] 重新构建前端..."
npm run build

if [ $? -eq 0 ]; then
    echo "[OK] 构建成功"
else
    echo "[ERROR] 构建失败"
    exit 1
fi

echo ""
echo "[7] 重启前端服务..."
sudo systemctl restart smart-tg-frontend
sleep 3

if systemctl is-active --quiet smart-tg-frontend; then
    echo "[OK] 前端服务已启动"
else
    echo "[WARNING] 前端服务可能未正常启动"
    echo "查看日志:"
    sudo journalctl -u smart-tg-frontend -n 10 --no-pager
fi

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "访问地址: http://$HOST:3000"
echo "后端 API: http://$HOST:8000"
echo ""
echo "如果仍然卡在认证检查，请:"
echo "  1. 清除浏览器缓存 (Ctrl+Shift+Delete)"
echo "  2. 在浏览器控制台执行: localStorage.clear()"
echo "  3. 刷新页面"

