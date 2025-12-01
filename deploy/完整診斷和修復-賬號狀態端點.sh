#!/bin/bash
# 完整診斷和修復賬號狀態端點問題

set -e

cd /home/ubuntu/liaotian/deployment-package/admin-backend

echo "=== 【步驟 1】檢查代碼是否已更新 ==="
if grep -q "db_account = db.query(GroupAIAccount)" app/api/group_ai/accounts.py; then
    echo "✅ 代碼已包含數據庫檢查"
    CODE_UPDATED=true
else
    echo "❌ 代碼未更新，需要修復"
    CODE_UPDATED=false
fi

echo ""
echo "=== 【步驟 2】檢查賬號是否存在 ==="
source /home/ubuntu/liaotian/admin-backend/.venv/bin/activate
export PYTHONPATH=/home/ubuntu/liaotian/deployment-package

python3 << 'PYEOF'
from app.db import SessionLocal
from app.models.group_ai import GroupAIAccount

db = SessionLocal()
account = db.query(GroupAIAccount).filter(GroupAIAccount.account_id == "639454959591").first()
if account:
    print(f"✅ 賬號存在: {account.account_id}, 名稱: {account.name}")
else:
    print("❌ 賬號不存在於數據庫中")
    print("\n數據庫中的所有賬號:")
    all_accounts = db.query(GroupAIAccount).all()
    if all_accounts:
        for acc in all_accounts:
            print(f"  - {acc.account_id}: {acc.name}")
    else:
        print("  (數據庫中沒有賬號)")
db.close()
PYEOF

echo ""
echo "=== 【步驟 3】檢查服務狀態 ==="
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 後端服務正在運行"
else
    echo "❌ 後端服務未運行"
fi

echo ""
echo "=== 診斷完成 ==="
echo "請根據上述結果決定下一步操作："
echo "1. 如果代碼未更新 → 需要部署修復後的代碼"
echo "2. 如果賬號不存在 → 需要創建測試賬號或使用現有賬號"
echo "3. 如果服務未運行 → 需要重啟服務"
