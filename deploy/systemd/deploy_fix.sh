#!/bin/bash
# 部署前端修复

set -e

FRONTEND_DIR="/home/ubuntu/saas-demo"
BACKUP_DIR="${FRONTEND_DIR}/backups"

echo "=========================================="
echo "部署前端修复"
echo "=========================================="

# 1. 备份原文件
echo ""
echo "[1] 备份原文件..."
mkdir -p "$BACKUP_DIR"
cp "${FRONTEND_DIR}/src/components/layout-wrapper.tsx" "${BACKUP_DIR}/layout-wrapper.tsx.$(date +%Y%m%d_%H%M%S).bak"
echo "[OK] 备份完成"

# 2. 停止服务
echo ""
echo "[2] 停止前端服务..."
sudo systemctl stop smart-tg-frontend
sleep 2
echo "[OK] 服务已停止"

# 3. 确保使用 Node.js 20
echo ""
echo "[3] 检查 Node.js 版本..."
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

# 4. 提示用户上传文件
echo ""
echo "[4] 请上传修复后的 layout-wrapper.tsx 文件"
echo "  文件路径: ${FRONTEND_DIR}/src/components/layout-wrapper.tsx"
echo ""
echo "  可以使用以下方法之一:"
echo "  方法1: 使用 SCP (在本地执行):"
echo "    scp saas-demo/src/components/layout-wrapper.tsx ubuntu@165.154.254.99:${FRONTEND_DIR}/src/components/"
echo ""
echo "  方法2: 手动编辑文件，应用以下修复:"
echo "    - 在第 21 行后添加: setChecking(false); // 先停止檢查狀態，避免卡住"
echo "    - 将第 33-35 行改为: // 無論是否認證，都應該停止檢查狀態 和 setChecking(false);"
echo "    - 将第 77 行改为: }, [pathname, router, isLoginPage, authState]);"
echo ""
read -p "  上传完成后按 Enter 继续..."

# 5. 验证文件
echo ""
echo "[5] 验证文件..."
if [ ! -f "${FRONTEND_DIR}/src/components/layout-wrapper.tsx" ]; then
    echo "[ERROR] 文件不存在！"
    exit 1
fi

# 检查是否包含修复
if grep -q "setChecking(false); // 先停止檢查狀態" "${FRONTEND_DIR}/src/components/layout-wrapper.tsx"; then
    echo "[OK] 文件包含修复"
else
    echo "[WARNING] 文件可能未包含修复，请检查"
fi

# 6. 重新构建
echo ""
echo "[6] 重新构建前端..."
cd "$FRONTEND_DIR"
source ~/.nvm/nvm.sh
nvm use 20
npm run build

if [ $? -eq 0 ]; then
    echo "[OK] 构建成功"
else
    echo "[ERROR] 构建失败"
    exit 1
fi

# 7. 重启服务
echo ""
echo "[7] 重启前端服务..."
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

