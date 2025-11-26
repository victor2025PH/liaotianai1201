#!/bin/bash
# 快速部署修复后的前端代码

set -e

echo "=========================================="
echo "前端修复部署脚本"
echo "=========================================="

# 1. 进入目录
cd /home/ubuntu/saas-demo

# 2. 备份原文件
echo ""
echo "[1] 备份原文件..."
cp src/components/layout-wrapper.tsx src/components/layout-wrapper.tsx.bak
echo "[OK] 备份完成: src/components/layout-wrapper.tsx.bak"

# 3. 提示用户编辑文件
echo ""
echo "[2] 请编辑文件并粘贴修复后的代码:"
echo "   文件路径: src/components/layout-wrapper.tsx"
echo "   编辑命令: nano src/components/layout-wrapper.tsx"
echo ""
echo "   在 nano 中:"
echo "   - 删除所有内容（多次按 Ctrl+K）"
echo "   - 按 Ctrl+V 粘贴修复后的代码"
echo "   - 按 Ctrl+O 保存"
echo "   - 按 Enter 确认"
echo "   - 按 Ctrl+X 退出"
echo ""
read -p "编辑完成后按 Enter 继续..."

# 4. 验证文件
echo ""
echo "[3] 验证文件..."
if grep -q "setChecking(false); // 先停止檢查狀態" src/components/layout-wrapper.tsx; then
    echo "[OK] 文件包含修复"
else
    echo "[WARNING] 文件可能未包含修复，请检查"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 5. 确保使用 Node.js 20
echo ""
echo "[4] 检查 Node.js 版本..."
source ~/.nvm/nvm.sh
nvm use 20
NODE_VERSION=$(node --version)
echo "  Node.js 版本: $NODE_VERSION"

if [[ ! "$NODE_VERSION" =~ ^v20 ]]; then
    echo "  安装 Node.js 20..."
    nvm install 20
    nvm use 20
    nvm alias default 20
    echo "[OK] 已切换到 Node.js 20"
fi

# 6. 重新构建
echo ""
echo "[5] 重新构建前端..."
npm run build

if [ $? -eq 0 ]; then
    echo "[OK] 构建成功"
else
    echo "[ERROR] 构建失败"
    exit 1
fi

# 7. 重启服务
echo ""
echo "[6] 重启前端服务..."
sudo systemctl restart smart-tg-frontend
sleep 3

# 检查服务状态
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
echo "访问地址: http://165.154.254.99:3000"
echo ""
echo "如果仍然卡在认证检查，请:"
echo "  1. 清除浏览器缓存 (Ctrl+Shift+Delete)"
echo "  2. 在浏览器控制台执行: localStorage.clear()"
echo "  3. 刷新页面"

