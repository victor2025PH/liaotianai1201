#!/bin/bash
# 檢查和配置環境變量

set -e

cd /home/ubuntu/liaotian/deployment-package

echo "=== 環境變量配置助手 ==="
echo ""

echo "【步驟 1】檢查 .env 文件..."
if [ -f ".env" ]; then
    echo "✅ .env 文件已存在"
    echo "當前配置:"
    grep -E "^(TELEGRAM_API_ID|TELEGRAM_API_HASH|OPENAI_API_KEY|TELEGRAM_SESSION_NAME)=" .env 2>/dev/null | sed 's/=.*/=***/' || echo "  未找到關鍵變量"
    
    # 檢查必填變量
    missing_vars=()
    if ! grep -q "^TELEGRAM_API_ID=" .env 2>/dev/null || grep -q "^TELEGRAM_API_ID=$" .env 2>/dev/null; then
        missing_vars+=("TELEGRAM_API_ID")
    fi
    if ! grep -q "^TELEGRAM_API_HASH=" .env 2>/dev/null || grep -q "^TELEGRAM_API_HASH=$" .env 2>/dev/null; then
        missing_vars+=("TELEGRAM_API_HASH")
    fi
    if ! grep -q "^OPENAI_API_KEY=" .env 2>/dev/null || grep -q "^OPENAI_API_KEY=$" .env 2>/dev/null; then
        missing_vars+=("OPENAI_API_KEY")
    fi
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        echo "✅ 所有必填變量已設置"
    else
        echo "❌ 缺少必填變量: ${missing_vars[*]}"
        echo "   請編輯 .env 文件並填入實際值"
    fi
else
    echo "❌ .env 文件不存在"
    echo ""
    echo "創建 .env 文件模板..."
    if [ -f "docs/env.example" ]; then
        cp docs/env.example .env
        echo "✅ 已從 docs/env.example 創建 .env 文件"
    else
        echo "# 環境變量配置文件" > .env
        echo "# 請填入以下必填變量:" >> .env
        echo "TELEGRAM_API_ID=" >> .env
        echo "TELEGRAM_API_HASH=" >> .env
        echo "TELEGRAM_SESSION_NAME=" >> .env
        echo "OPENAI_API_KEY=" >> .env
        echo "✅ 已創建 .env 文件模板"
    fi
    echo ""
    echo "⚠️ 請編輯 .env 文件並填入以下必填值："
    echo "  1. TELEGRAM_API_ID（從 https://my.telegram.org 獲取）"
    echo "  2. TELEGRAM_API_HASH（從 https://my.telegram.org 獲取）"
    echo "  3. TELEGRAM_SESSION_NAME（自定義名稱）"
    echo "  4. OPENAI_API_KEY（從 https://platform.openai.com/api-keys 獲取）"
fi

echo ""
echo "【步驟 2】檢查後端配置..."
cd admin-backend
source /home/ubuntu/liaotian/admin-backend/.venv/bin/activate
export PYTHONPATH=/home/ubuntu/liaotian/deployment-package

python3 << 'PYEOF'
from app.core.config import get_settings
settings = get_settings()

print(f"數據庫 URL: {settings.database_url}")
print(f"管理員郵箱: {settings.admin_default_email}")

warnings = []
if settings.jwt_secret == 'change_me':
    warnings.append("⚠️ JWT_SECRET: 使用默認值（建議修改）")
else:
    print("✅ JWT_SECRET: 已設置")

if settings.admin_default_password == 'changeme123':
    warnings.append("⚠️ ADMIN_DEFAULT_PASSWORD: 使用默認值（建議修改）")
else:
    print("✅ ADMIN_DEFAULT_PASSWORD: 已設置")

if warnings:
    print("\n".join(warnings))
    print("\n建議：")
    print("  1. 設置 JWT_SECRET 環境變量（生成方式：python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"）")
    print("  2. 設置 ADMIN_DEFAULT_PASSWORD 環境變量（使用強密碼）")
else:
    print("✅ 後端配置安全（已修改默認值）")
PYEOF

echo ""
echo "=== 檢查完成 ==="
echo ""
echo "下一步："
echo "1. 如果 .env 文件缺少變量，請編輯並填入實際值"
echo "2. 如果後端配置使用默認值，建議設置環境變量："
echo "   export JWT_SECRET=\$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo "   export ADMIN_DEFAULT_PASSWORD='your_secure_password'"
