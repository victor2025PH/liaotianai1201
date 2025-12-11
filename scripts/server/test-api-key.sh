#!/bin/bash
# 在服務器上測試 OpenAI API Key

set -e

echo "=========================================="
echo "OpenAI API Key 測試"
echo "=========================================="

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
ENV_FILE="$PROJECT_DIR/.env"

# 檢查 .env 文件
if [ ! -f "$ENV_FILE" ]; then
    echo "[失敗] .env 文件不存在: $ENV_FILE"
    exit 1
fi

echo "[通過] .env 文件存在"

# 加載環境變量
export $(grep -v '^#' "$ENV_FILE" | xargs)

# 檢查 API Key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "[失敗] OPENAI_API_KEY 未設置"
    exit 1
fi

echo "[通過] OPENAI_API_KEY 已設置"
echo "Key 長度: ${#OPENAI_API_KEY} 字符"
echo "Key 前綴: ${OPENAI_API_KEY:0:7}..."

# 進入項目目錄
cd "$PROJECT_DIR" || exit 1

# 激活虛擬環境
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "[通過] 虛擬環境已激活"
else
    echo "[警告] 虛擬環境不存在，使用系統 Python"
fi

# 測試 API Key
echo ""
echo "測試 OpenAI API 連接..."
python3 << 'PYTHON_EOF'
import os
import sys
import asyncio
from openai import AsyncOpenAI

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("[失敗] OPENAI_API_KEY 未設置")
    sys.exit(1)

print(f"[信息] API Key 長度: {len(api_key)} 字符")
print(f"[信息] API Key 前綴: {api_key[:7]}...")

client = AsyncOpenAI(api_key=api_key)

async def test():
    try:
        print("[測試] 發送測試請求...")
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=5
        )
        reply = response.choices[0].message.content.strip()
        print(f"[成功] API 連接成功！")
        print(f"[成功] 測試回覆: {reply}")
        return True
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "invalid_api_key" in error_str.lower():
            print("[失敗] API Key 無效或已過期")
            print("[建議] 請檢查 OpenAI 平台上的 API Key 狀態")
            print("[建議] 如果 Key 已過期，請生成新的 API Key")
        elif "429" in error_str:
            print("[警告] API 請求過於頻繁，請稍後再試")
        elif "quota" in error_str.lower():
            print("[失敗] API 配額已用完")
        else:
            print(f"[失敗] API 連接失敗: {e}")
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
PYTHON_EOF

exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "[成功] OpenAI API Key 測試通過"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "[失敗] OpenAI API Key 測試失敗"
    echo "=========================================="
    echo ""
    echo "請檢查："
    echo "1. API Key 是否正確（應該以 sk- 開頭）"
    echo "2. API Key 是否在 OpenAI 平台上有效"
    echo "3. API Key 是否已過期或被撤銷"
    echo "4. 賬戶是否有足夠的配額"
    echo ""
    echo "獲取新的 API Key:"
    echo "https://platform.openai.com/account/api-keys"
fi

exit $exit_code

