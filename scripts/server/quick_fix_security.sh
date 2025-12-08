#!/bin/bash
# 快速修复安全配置脚本
# 自动生成JWT_SECRET并更新.env文件

set -e

SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
ENV_FILE="$PROJECT_ROOT/admin-backend/.env"

echo "============================================================"
echo "快速修复安全配置"
echo "============================================================"

# 生成JWT密钥
echo ""
echo "生成新的JWT密钥..."
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
echo "✓ JWT密钥已生成"

# 备份现有.env文件
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✓ 已备份现有.env文件"
fi

# 更新或添加JWT_SECRET
if grep -q "^JWT_SECRET=" "$ENV_FILE" 2>/dev/null; then
    # 更新现有配置
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" "$ENV_FILE"
    else
        # Linux
        sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" "$ENV_FILE"
    fi
    echo "✓ 已更新JWT_SECRET"
else
    # 添加新配置
    echo "JWT_SECRET=$JWT_SECRET" >> "$ENV_FILE"
    echo "✓ 已添加JWT_SECRET"
fi

# 检查并提示管理员密码
if grep -q "^ADMIN_DEFAULT_PASSWORD=changeme123" "$ENV_FILE" 2>/dev/null || ! grep -q "^ADMIN_DEFAULT_PASSWORD=" "$ENV_FILE" 2>/dev/null; then
    echo ""
    echo "⚠ 检测到管理员密码使用默认值"
    echo "请手动编辑 $ENV_FILE 文件，修改 ADMIN_DEFAULT_PASSWORD"
    echo "或运行: python3 scripts/server/update_security_config.py"
fi

echo ""
echo "============================================================"
echo "配置更新完成！"
echo "============================================================"
echo ""
echo "下一步:"
echo "1. 重启后端服务:"
echo "   pm2 restart backend"
echo ""
echo "2. 验证配置:"
echo "   cd admin-backend && source venv/bin/activate"
echo "   python3 ../scripts/server/system_health_check.py"
echo ""
echo "⚠️  请妥善保管JWT_SECRET，不要泄露！"
echo ""

