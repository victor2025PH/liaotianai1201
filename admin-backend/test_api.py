#!/usr/bin/env python3
"""測試紅包 API 連通性"""

import sys

def test_api():
    try:
        import httpx
    except ImportError:
        print("ERROR: httpx 未安裝，請執行: pip install httpx")
        return False
    
    print("=" * 50)
    print("  紅包 API 連通性測試")
    print("=" * 50)
    print()
    
    # 1. 健康檢查
    print("1. 測試 API 健康狀態...")
    try:
        r = httpx.get("https://api.usdt2026.cc/api/v2/ai/status", timeout=10)
        if r.status_code == 200:
            print(f"   ✅ API 在線 (狀態碼: {r.status_code})")
        else:
            print(f"   ⚠️ API 響應異常 (狀態碼: {r.status_code})")
    except Exception as e:
        print(f"   ❌ 連接失敗: {e}")
        return False
    
    # 2. 測試 AI 帳號餘額
    print()
    print("2. 測試 AI 帳號餘額查詢...")
    
    ai_accounts = [
        (639277358115, "AI-1"),
        (639543603735, "AI-2"),
        (639952948692, "AI-3"),
    ]
    
    for user_id, name in ai_accounts:
        try:
            r = httpx.get(
                "https://api.usdt2026.cc/api/v2/ai/wallet/balance",
                headers={
                    "Authorization": "Bearer test-key-2024",
                    "X-Telegram-User-Id": str(user_id)
                },
                timeout=10
            )
            
            if r.status_code == 200:
                data = r.json()
                balance = data.get("data", {}).get("balances", {}).get("usdt", 0)
                print(f"   ✅ {name} (ID: {user_id}) - 餘額: {balance} USDT")
            else:
                print(f"   ⚠️ {name} 查詢失敗 (狀態碼: {r.status_code})")
        except Exception as e:
            print(f"   ❌ {name} 查詢異常: {e}")
    
    print()
    print("=" * 50)
    print("  測試完成")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
