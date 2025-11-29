#!/bin/bash
# 一键重新构建并启动

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend
sleep 2

echo ""
echo "=== [2] 清理构建缓存 ==="
rm -rf .next node_modules/.cache
echo "✅ 已清理"

echo ""
echo "=== [3] 加载NVM ==="
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "Node版本: $(node --version)"
echo "NPM版本: $(npm --version)"

echo ""
echo "=== [4] 重新构建（这可能需要几分钟）==="
npm run build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 构建成功"
    
    echo ""
    echo "=== [5] 验证BUILD_ID ==="
    if [ -f ".next/BUILD_ID" ]; then
        echo "✅ BUILD_ID存在: $(cat .next/BUILD_ID)"
    else
        echo "❌ BUILD_ID不存在"
        exit 1
    fi
    
    echo ""
    echo "=== [6] 启动服务 ==="
    sudo systemctl start liaotian-frontend
    sleep 5
    
    echo ""
    echo "=== [7] 检查服务状态 ==="
    sudo systemctl status liaotian-frontend --no-pager | head -20
    
    echo ""
    echo "=== [8] 检查端口 ==="
    if ss -tlnp | grep -q ':3000'; then
        echo "✅ 端口3000正在监听"
        ss -tlnp | grep ':3000'
    else
        echo "❌ 端口3000未监听"
        echo "查看最新日志:"
        sudo journalctl -u liaotian-frontend -n 10 --no-pager
    fi
else
    echo ""
    echo "❌ 构建失败"
    exit 1
fi

echo ""
echo "=== 完成 ==="

