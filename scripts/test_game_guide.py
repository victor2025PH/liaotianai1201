"""
测试游戏引导功能
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# 设置控制台编码为UTF-8（Windows）
if sys.platform == 'win32':
    try:
        # 尝试设置控制台编码
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from group_ai_service.game_api_client import GameEvent
from group_ai_service.service_manager import ServiceManager
from group_ai_service.game_guide_service import GameGuideService


async def test_game_start_guide():
    """测试游戏开始引导"""
    print("\n" + "="*60)
    print("测试 1: 游戏开始引导")
    print("="*60)
    
    service_manager = ServiceManager.get_instance()
    
    # 创建游戏开始事件
    event = GameEvent(
        event_type="GAME_START",
        event_id="test_event_001",
        group_id=-1001234567890,  # 测试群组ID
        game_id="game_001",
        timestamp=datetime.now(),
        payload={
            "game_mode": "normal",
            "total_prize": 1000.0,
            "token": "USDT"
        }
    )
    
    try:
        await service_manager.handle_game_start(event)
        print("[OK] 游戏开始引导测试完成")
        print(f"   事件ID: {event.event_id}")
        print(f"   群组ID: {event.group_id}")
        print(f"   游戏ID: {event.game_id}")
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_redpacket_sent_guide():
    """测试红包发送引导"""
    print("\n" + "="*60)
    print("测试 2: 红包发送引导")
    print("="*60)
    
    service_manager = ServiceManager.get_instance()
    
    # 创建红包发送事件
    event = GameEvent(
        event_type="REDPACKET_SENT",
        event_id="test_event_002",
        group_id=-1001234567890,
        game_id="game_001",
        timestamp=datetime.now(),
        payload={
            "redpacket_id": "rp_001",
            "amount": 100.0,
            "count": 10,
            "remaining_count": 10,
            "token": "USDT"
        }
    )
    
    try:
        await service_manager.handle_redpacket_sent(event)
        print("[OK] 红包发送引导测试完成")
        print(f"   红包金额: {event.payload.get('amount')} {event.payload.get('token')}")
        print(f"   红包份数: {event.payload.get('count')} 份")
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_redpacket_claimed_guide():
    """测试红包被领取引导（快抢完提醒）"""
    print("\n" + "="*60)
    print("测试 3: 红包被领取引导（快抢完提醒）")
    print("="*60)
    
    service_manager = ServiceManager.get_instance()
    
    # 创建红包被领取事件（剩余3份）
    event = GameEvent(
        event_type="REDPACKET_CLAIMED",
        event_id="test_event_003",
        group_id=-1001234567890,
        game_id="game_001",
        timestamp=datetime.now(),
        payload={
            "redpacket_id": "rp_001",
            "account_id": "user_123",
            "amount": 10.5,
            "token": "USDT",
            "remaining_count": 3  # 剩余3份，应该触发提醒
        }
    )
    
    try:
        await service_manager.handle_redpacket_claimed(event)
        print("[OK] 红包被领取引导测试完成")
        print(f"   剩余份数: {event.payload.get('remaining_count')} 份")
        print("   [WARNING] 应该触发'快抢完'提醒")
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_game_end_guide():
    """测试游戏结束引导"""
    print("\n" + "="*60)
    print("测试 4: 游戏结束引导")
    print("="*60)
    
    service_manager = ServiceManager.get_instance()
    
    # 创建游戏结束事件
    event = GameEvent(
        event_type="GAME_END",
        event_id="test_event_004",
        group_id=-1001234567890,
        game_id="game_001",
        timestamp=datetime.now(),
        payload={
            "total_amount": 1000.0,
            "token": "USDT",
            "participants": 25,
            "winners": 10
        }
    )
    
    try:
        await service_manager.handle_game_end(event)
        print("[OK] 游戏结束引导测试完成")
        print(f"   总金额: {event.payload.get('total_amount')} {event.payload.get('token')}")
        print(f"   参与人数: {event.payload.get('participants')} 人")
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_result_announced_guide():
    """测试结果公布引导"""
    print("\n" + "="*60)
    print("测试 5: 结果公布引导")
    print("="*60)
    
    service_manager = ServiceManager.get_instance()
    
    # 创建结果公布事件
    event = GameEvent(
        event_type="RESULT_ANNOUNCED",
        event_id="test_event_005",
        group_id=-1001234567890,
        game_id="game_001",
        timestamp=datetime.now(),
        payload={
            "summary": "🎉 恭喜以下用户获得奖励！\n\n🥇 第一名: @user1 - 50 USDT\n🥈 第二名: @user2 - 30 USDT\n🥉 第三名: @user3 - 20 USDT",
            "leaderboard": [
                {"user": "@user1", "amount": 50.0},
                {"user": "@user2", "amount": 30.0},
                {"user": "@user3", "amount": 20.0}
            ]
        }
    )
    
    try:
        await service_manager.handle_result_announced(event)
        print("[OK] 结果公布引导测试完成")
        summary = event.payload.get('summary', '')
        if summary:
            # 移除emoji字符以避免编码问题
            import re
            summary_clean = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}]', '', summary)
            if summary_clean:
                print(f"   结果摘要: {summary_clean[:50]}...")
            else:
                print("   结果摘要: (包含特殊字符)")
        else:
            print("   结果摘要: (无)")
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_custom_guide():
    """测试自定义引导消息"""
    print("\n" + "="*60)
    print("测试 6: 自定义引导消息")
    print("="*60)
    
    service_manager = ServiceManager.get_instance()
    
    if not service_manager.game_guide_service:
        print("[ERROR] GameGuideService 未初始化")
        return
    
    try:
        await service_manager.game_guide_service.send_custom_guide(
            group_id=-1001234567890,
            message="[提示] 红包游戏正在进行中，快来参与吧！"
        )
        print("[OK] 自定义引导消息测试完成")
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("="*60)
    print("游戏引导功能测试")
    print("="*60)
    print("\n注意：此测试需要：")
    print("  1. 后端服务正在运行")
    print("  2. 至少有一个账号已启动并监听测试群组")
    print("  3. 测试群组ID: -1001234567890（请根据实际情况修改）")
    print("\n开始测试...\n")
    
    # 检查 ServiceManager
    try:
        service_manager = ServiceManager.get_instance()
        print(f"[OK] ServiceManager 初始化成功")
        print(f"   GameGuideService: {'已初始化' if service_manager.game_guide_service else '未初始化'}")
        print(f"   账号数量: {len(service_manager.account_manager.accounts)}")
    except Exception as e:
        print(f"[ERROR] ServiceManager 初始化失败: {e}")
        return
    
    # 运行测试
    await test_game_start_guide()
    await asyncio.sleep(1)
    
    await test_redpacket_sent_guide()
    await asyncio.sleep(1)
    
    await test_redpacket_claimed_guide()
    await asyncio.sleep(1)
    
    await test_game_end_guide()
    await asyncio.sleep(1)
    
    await test_result_announced_guide()
    await asyncio.sleep(1)
    
    await test_custom_guide()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    print("\n提示：")
    print("  - 如果账号已启动并监听测试群组，应该能在群组中看到引导消息")
    print("  - 如果没有看到消息，请检查：")
    print("    1. 账号是否已启动（status = online）")
    print("    2. 账号的 group_ids 是否包含测试群组ID")
    print("    3. 账号的 client 是否正常连接")


if __name__ == "__main__":
    asyncio.run(main())

