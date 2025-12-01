#!/bin/bash
# 配置基本環境變量

set -e

cd /home/ubuntu/liaotian/deployment-package

echo "=== 配置基本環境變量 ==="
echo ""

# 1. 配置 .env 文件（AI 服務）
echo "【步驟 1】配置 .env 文件..."
if [ ! -f ".env" ]; then
    echo "創建 .env 文件..."
    cat > .env << 'ENVEOF'
# ========== OpenAI API 配置 ==========
OPENAI_API_KEY=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

# ========== Telegram API 配置 ==========
# 注意：這些配置是每個賬號不同的，將通過批量導入或 API 提交
# TELEGRAM_API_ID=
# TELEGRAM_API_HASH=
# TELEGRAM_SESSION_NAME=

# ========== OpenAI 模型配置（可選） ==========
OPENAI_MODEL=gpt-4
OPENAI_VISION_MODEL=gpt-4o-mini
ENVEOF
    echo "✅ .env 文件已創建"
else
    echo "✅ .env 文件已存在"
    # 更新 OpenAI API Key
    if grep -q "^OPENAI_API_KEY=" .env; then
        sed -i 's|^OPENAI_API_KEY=.*|OPENAI_API_KEY=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|' .env
        echo "✅ OpenAI API Key 已更新"
    else
        echo "OPENAI_API_KEY=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" >> .env
        echo "✅ OpenAI API Key 已添加"
    fi
fi

echo ""
echo "【步驟 2】配置後端環境變量..."
echo ""
echo "⚠️ 注意：後端環境變量需要在啟動服務時設置，或通過 systemd 服務文件配置"
echo ""
echo "建議的環境變量設置："
echo "  export JWT_SECRET='kLZdZJCzq8qev_isfbrxjSshcHGiMDMA8Uok8f55RXc'"
echo "  export ADMIN_DEFAULT_PASSWORD='Along2021!!!'"
echo ""
echo "或者在啟動服務時："
echo "  JWT_SECRET='kLZdZJCzq8qev_isfbrxjSshcHGiMDMA8Uok8f55RXc' \\"
echo "  ADMIN_DEFAULT_PASSWORD='Along2021!!!' \\"
echo "  /home/ubuntu/liaotian/admin-backend/.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo ""
echo "【步驟 3】更新管理員密碼..."
cd admin-backend
source /home/ubuntu/liaotian/admin-backend/.venv/bin/activate
export PYTHONPATH=/home/ubuntu/liaotian/deployment-package
export JWT_SECRET='kLZdZJCzq8qev_isfbrxjSshcHGiMDMA8Uok8f55RXc'
export ADMIN_DEFAULT_PASSWORD='Along2021!!!'

python3 << 'PYEOF'
from app.db import SessionLocal
from app.crud.user import get_user_by_email, update_user_password
from app.core.security import get_password_hash

db = SessionLocal()
try:
    user = get_user_by_email(db, "admin@example.com")
    if user:
        # 更新密碼
        new_password_hash = get_password_hash("Along2021!!!")
        user.hashed_password = new_password_hash
        db.commit()
        print("✅ 管理員密碼已更新")
    else:
        print("⚠️ 管理員用戶不存在，將在首次登錄時創建")
except Exception as e:
    print(f"❌ 更新密碼失敗: {e}")
    db.rollback()
finally:
    db.close()
PYEOF

echo ""
echo "=== 配置完成 ==="
echo ""
echo "下一步："
echo "1. 準備 Telegram 賬號配置文件（TXT 或 Excel）"
echo "2. 使用腳本導入：python scripts/import_telegram_accounts.py <文件路徑>"
echo "3. 或通過 API 動態提交賬號配置"
