#!/bin/bash
# 驗證服務器環境變量配置腳本

set -e

echo "=========================================="
echo "環境變量配置驗證"
echo "=========================================="

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
ENV_FILE="$PROJECT_DIR/.env"

echo ""
echo "檢查 .env 文件..."
if [ -f "$ENV_FILE" ]; then
    echo "[通過] .env 文件存在: $ENV_FILE"
    
    # 檢查關鍵環境變量是否存在
    echo ""
    echo "檢查關鍵環境變量..."
    
    required_vars=(
        "TELEGRAM_API_ID"
        "TELEGRAM_API_HASH"
        "TELEGRAM_SESSION_NAME"
        "OPENAI_API_KEY"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "$ENV_FILE"; then
            # 檢查值是否為空
            value=$(grep "^${var}=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '[:space:]')
            if [ -z "$value" ] || [ "$value" = "" ]; then
                echo "[警告] $var 存在但值為空"
                missing_vars+=("$var (空值)")
            else
                # 顯示前後幾個字符（隱藏中間部分）
                if [ "$var" = "OPENAI_API_KEY" ]; then
                    masked=$(echo "$value" | sed 's/\(.\{7\}\).*\(.\{4\}\)/\1...\2/')
                    echo "[通過] $var = $masked"
                else
                    echo "[通過] $var 已設置"
                fi
            fi
        else
            echo "[失敗] $var 未找到"
            missing_vars+=("$var")
        fi
    done
    
    echo ""
    if [ ${#missing_vars[@]} -eq 0 ]; then
        echo "=========================================="
        echo "[成功] 所有必需的環境變量都已配置"
        echo "=========================================="
    else
        echo "=========================================="
        echo "[警告] 以下環境變量缺失或為空:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo "=========================================="
        exit 1
    fi
    
else
    echo "[失敗] .env 文件不存在: $ENV_FILE"
    echo ""
    echo "請確保 .env 文件已上傳到服務器"
    exit 1
fi

echo ""
echo "=========================================="
echo "檢查 Python 環境變量加載"
echo "=========================================="

# 檢查 config.py 是否能正確加載環境變量
cd "$PROJECT_DIR" || exit 1

if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "[通過] 虛擬環境已激活"
else
    echo "[警告] 虛擬環境不存在，嘗試使用系統 Python"
fi

echo ""
echo "測試環境變量加載..."
python3 << 'PYTHON_EOF'
import os
import sys
from pathlib import Path

# 嘗試加載 .env 文件
env_file = Path("/home/ubuntu/telegram-ai-system/.env")
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)
    print("[通過] .env 文件已加載")
else:
    print("[失敗] .env 文件不存在")

# 檢查關鍵環境變量
required_vars = [
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH", 
    "TELEGRAM_SESSION_NAME",
    "OPENAI_API_KEY"
]

missing = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        if var == "OPENAI_API_KEY":
            masked = value[:7] + "..." + value[-4:] if len(value) > 11 else "***"
            print(f"[通過] {var} = {masked}")
        else:
            print(f"[通過] {var} 已設置")
    else:
        print(f"[失敗] {var} 未設置")
        missing.append(var)

if missing:
    print(f"\n[警告] 缺失環境變量: {', '.join(missing)}")
    sys.exit(1)
else:
    print("\n[成功] 所有環境變量都已正確加載")
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "[成功] 環境變量配置驗證完成"
    echo "=========================================="
    exit 0
else
    echo ""
    echo "=========================================="
    echo "[失敗] 環境變量配置驗證失敗"
    echo "=========================================="
    exit 1
fi

