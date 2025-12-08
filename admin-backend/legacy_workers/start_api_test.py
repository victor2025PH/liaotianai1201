#!/usr/bin/env python3
"""
🧪 紅包 API 功能測試腳本
無需 Telegram Session，直接測試 API 功能
"""

import asyncio
import sys
from pathlib import Path

# 設置路徑
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    print("=" * 60)
    print("  🧧 紅包 API 功能測試")
    print("=" * 60)
    print()
    
    # 導入紅包客戶端
    try:
        from worker_redpacket_client import (
            RedPacketAPIClient, RedPacketAPIConfig,
            RedPacketGameEngine, GameStrategy
        )
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        print("請確保已安裝依賴: pip install -r requirements.txt")
        return
    
    # 創建客戶端 (必須使用 HTTPS)
    config = RedPacketAPIConfig(
        api_url="https://api.usdt2026.cc",
        api_key="test-key-2024"
    )
    client = RedPacketAPIClient(config)
    
    # AI 帳號列表
    ai_accounts = [
        (639277358115, "AI-1"),
        (639543603735, "AI-2"),
        (639952948692, "AI-3"),
        (639454959591, "AI-4"),
        (639542360349, "AI-5"),
        (639950375245, "AI-6"),
    ]
    
    # 1. 健康檢查
    print("📡 1. API 健康檢查...")
    print(f"   目標: {config.api_url}/api/v2/ai/status")
    try:
        is_healthy = await client.health_check()
        if is_healthy:
            print("   ✅ API 在線運行")
        else:
            print("   ⚠️ API 響應異常，嘗試繼續...")
    except Exception as e:
        print(f"   ❌ 連接失敗: {e}")
        print()
        print("   可能原因:")
        print("   1. 網絡無法訪問 api.usdt2026.cc")
        print("   2. API 服務器暫時離線")
        print("   3. 防火牆阻擋了請求")
        print()
        print("   嘗試手動測試:")
        print("   curl https://api.usdt2026.cc/api/v2/ai/status")
        print()
        
        # 嘗試繼續測試其他功能
        print("   嘗試繼續測試餘額查詢...")
        try:
            balance = await client.get_balance(ai_accounts[0][0])
            print(f"   ✅ 餘額查詢成功: {balance.get_balance('usdt')} USDT")
        except Exception as e2:
            print(f"   ❌ 餘額查詢也失敗: {e2}")
            print()
            print("=" * 60)
            print("  ⚠️ API 無法訪問，請檢查網絡連接")
            print("=" * 60)
            await client.close()
            return
    
    # 2. 查詢所有 AI 餘額
    print()
    print("💰 2. 查詢 AI 帳號餘額...")
    total_balance = 0
    for user_id, name in ai_accounts:
        try:
            balance = await client.get_balance(user_id)
            usdt = balance.get_balance("usdt")
            total_balance += usdt
            print(f"   ✅ {name} (ID: {user_id}): {usdt:.2f} USDT")
        except Exception as e:
            print(f"   ⚠️ {name}: 查詢失敗 - {e}")
    
    print(f"\n   📊 總餘額: {total_balance:.2f} USDT")
    
    # 3. 測試發紅包（AI-1 發）
    print()
    print("🧧 3. 測試發送紅包...")
    sender_id = ai_accounts[0][0]
    
    try:
        packet = await client.send_packet(
            sender_id=sender_id,
            total_amount=1.0,
            total_count=5,
            currency="usdt",
            packet_type="random",
            message="🤖 API 測試紅包"
        )
        
        if packet:
            print(f"   ✅ 紅包發送成功!")
            print(f"      UUID: {packet.packet_uuid}")
            print(f"      金額: {packet.total_amount} USDT")
            print(f"      份數: {packet.total_count}")
            
            # 4. 測試領取紅包（AI-2 領）
            print()
            print("🎯 4. 測試領取紅包...")
            claimer_id = ai_accounts[1][0]
            
            result = await client.claim_packet(claimer_id, packet.packet_uuid)
            
            if result.success:
                print(f"   ✅ 領取成功!")
                print(f"      金額: {result.claimed_amount:.4f} USDT")
                if result.is_bomb_hit:
                    print(f"      💣 踩雷! 賠付: {result.penalty_amount} USDT")
            else:
                print(f"   ⚠️ 領取失敗: {result.error_message}")
        else:
            print("   ❌ 發送失敗")
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
    
    # 5. 測試炸彈紅包
    print()
    print("💣 5. 測試炸彈紅包...")
    
    try:
        bomb_packet = await client.send_packet(
            sender_id=sender_id,
            total_amount=1.0,
            total_count=5,  # 炸彈紅包必須是 5 或 10 份
            currency="usdt",
            packet_type="equal",
            message="💣 炸彈紅包測試",
            bomb_number=3  # 雷號是 3
        )
        
        if bomb_packet:
            print(f"   ✅ 炸彈紅包發送成功!")
            print(f"      UUID: {bomb_packet.packet_uuid}")
            print(f"      雷號: 3")
            
            # AI-3 領取炸彈紅包
            print()
            print("🎲 6. 測試領取炸彈紅包...")
            claimer_id = ai_accounts[2][0]
            
            result = await client.claim_packet(claimer_id, bomb_packet.packet_uuid)
            
            if result.success:
                print(f"   領取金額: {result.claimed_amount:.4f} USDT")
                if result.is_bomb_hit:
                    print(f"   💥 踩雷了! 賠付: {result.penalty_amount:.2f} USDT")
                    print(f"   淨收益: {result.net_amount:.4f} USDT")
                else:
                    print(f"   ✅ 安全! 未踩雷")
            else:
                print(f"   ⚠️ 領取失敗: {result.error_message}")
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
    
    # 7. 最終餘額
    print()
    print("📊 7. 最終餘額統計...")
    final_total = 0
    for user_id, name in ai_accounts[:3]:  # 只查前3個參與的
        try:
            balance = await client.get_balance(user_id)
            usdt = balance.get_balance("usdt")
            final_total += usdt
            print(f"   {name}: {usdt:.2f} USDT")
        except:
            pass
    
    # 統計
    print()
    print("=" * 60)
    print("  📈 API 統計")
    print("=" * 60)
    stats = client.get_stats()
    print(f"  請求總數: {stats['requests_total']}")
    print(f"  成功: {stats['requests_success']}")
    print(f"  失敗: {stats['requests_failed']}")
    print(f"  發送紅包: {stats['packets_sent']}")
    print(f"  領取紅包: {stats['packets_claimed']}")
    print(f"  發送金額: {stats['amount_sent']:.2f} USDT")
    print(f"  領取金額: {stats['amount_claimed']:.4f} USDT")
    
    # 關閉客戶端
    await client.close()
    
    print()
    print("✅ 測試完成!")
    print()
    print("下一步：準備 Telegram Session 文件後，運行 start_full_system.py")


if __name__ == "__main__":
    asyncio.run(main())
