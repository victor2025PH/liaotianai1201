#!/bin/bash
# 診斷服務器後端啟動失敗問題

set -e

echo "========================================="
echo "診斷後端啟動失敗問題"
echo "開始時間: $(date)"
echo "========================================="
echo ""

cd ~/liaotian/admin-backend

# 步驟 1: 查看錯誤日誌
echo "【步驟1】查看錯誤日誌..."
if [ -f "/tmp/backend.log" ]; then
    echo "  最後 50 行日誌："
    tail -50 /tmp/backend.log
    echo ""
    
    echo "  錯誤和異常："
    tail -100 /tmp/backend.log | grep -iE "error|exception|traceback|failed|fatal" | tail -20 || echo "  未發現明顯錯誤"
else
    echo "  ⚠ 日誌文件不存在"
fi
echo ""

# 步驟 2: 檢查虛擬環境
echo "【步驟2】檢查虛擬環境..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "  ✓ 虛擬環境已激活"
    echo "  Python 路徑: $(which python)"
    echo "  Python 版本: $(python --version)"
else
    echo "  ✗ 虛擬環境不存在"
    echo "  正在創建虛擬環境..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "  ✓ 虛擬環境已創建"
fi
echo ""

# 步驟 3: 檢查依賴
echo "【步驟3】檢查依賴..."
REQUIRED_PACKAGES=("uvicorn" "fastapi" "sqlalchemy")
MISSING_PACKAGES=()

for PACKAGE in "${REQUIRED_PACKAGES[@]}"; do
    if pip list | grep -qi "^$PACKAGE"; then
        VERSION=$(pip list | grep -i "^$PACKAGE" | awk '{print $2}')
        echo "  ✓ $PACKAGE: $VERSION"
    else
        echo "  ✗ $PACKAGE: 未安裝"
        MISSING_PACKAGES+=("$PACKAGE")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo ""
    echo "  ⚠ 發現缺失的依賴，正在安裝..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        echo "  ✓ 依賴安裝完成"
    else
        echo "  ✗ requirements.txt 不存在"
    fi
fi
echo ""

# 步驟 4: 檢查環境變量文件
echo "【步驟4】檢查環境變量文件..."
if [ -f ".env" ]; then
    echo "  ✓ .env 文件存在"
    echo "  環境變量內容（隱藏敏感信息）："
    cat .env | sed 's/=.*/=***/' | head -10
else
    echo "  ✗ .env 文件不存在"
    echo "  正在創建基本 .env 文件..."
    cat > .env << 'EOF'
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=temp_jwt_secret_change_in_production
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
    echo "  ✓ .env 文件已創建"
fi
echo ""

# 步驟 5: 測試 Python 導入
echo "【步驟5】測試 Python 模塊導入..."
python -c "from app.main import app; print('  ✓ 模塊導入成功')" 2>&1 || {
    echo "  ✗ 模塊導入失敗"
    echo "  錯誤詳情："
    python -c "from app.main import app" 2>&1 | head -20 | sed 's/^/    /'
}
echo ""

# 步驟 6: 檢查數據庫
echo "【步驟6】檢查數據庫..."
if [ -f "admin.db" ]; then
    echo "  ✓ 數據庫文件存在"
    ls -lh admin.db | awk '{print "    大小: " $5}'
else
    echo "  ⚠ 數據庫文件不存在（可能需要初始化）"
fi
echo ""

# 步驟 7: 檢查端口
echo "【步驟7】檢查端口占用..."
PORT_8000=$(netstat -tlnp 2>/dev/null | grep ":8000 " || echo "")
if [ -n "$PORT_8000" ]; then
    echo "  ⚠ 端口 8000 已被占用："
    echo "$PORT_8000" | sed 's/^/    /'
else
    echo "  ✓ 端口 8000 可用"
fi
echo ""

# 步驟 8: 嘗試手動啟動（測試）
echo "【步驟8】嘗試手動啟動（測試模式）..."
echo "  直接運行 uvicorn 查看錯誤..."
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

# 嘗試啟動並立即停止（只為查看錯誤）
timeout 5 uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | head -30 || true

echo ""
echo "========================================="
echo "診斷完成"
echo "完成時間: $(date)"
echo "========================================="
echo ""
echo "根據上述診斷結果，修復問題後重新啟動服務"
echo ""
