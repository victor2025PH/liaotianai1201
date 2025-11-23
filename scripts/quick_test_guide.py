"""
快速测试游戏引导功能
需要先导入并启动账号
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from group_ai_service.service_manager import ServiceManager
from group_ai_service.game_api_client import GameEvent


async def main():
    print("="*60)
    print("游戏引导功能快速测试")
    print("="*60)
    
    # 检查账号状态
    sm = ServiceManager.get_instance()
    print(f"\n账号数量: {len(sm.account_manager.accounts)}")
    
    # 列出所有账号
    print("\n账号列表:")
    for account_id, account in sm.account_manager.accounts.items():
        print(f"  - {account_id}")
        print(f"    状态: {account.status.value}")
        print(f"    群组: {account.config.group_ids}")
    
    # 检查是否有在线账号
    online_accounts = [
        acc for acc in sm.account_manager.accounts.values()
        if acc.status.value == "online"
    ]
    
    if not online_accounts:
        print("\n⚠️  没有在线账号，无法发送测试消息")
        print("\n请先:")
        print("  1. 导入账号（前端或API）")
        print("  2. 启动账号")
        print("  3. 配置群组ID")
        return
    
    print(f"\n✅ 找到 {len(online_accounts)} 个在线账号")
    
    # 测试群组ID（需要根据实际情况修改）
    test_group_id = -1001234567890
    
    # 检查是否有账号监听该群组
    accounts_for_group = [
        acc for acc in online_accounts
        if not acc.config.group_ids or test_group_id in acc.config.group_ids
    ]
    
    if not accounts_for_group:
        print(f"\n⚠️  没有账号监听群组 {test_group_id}")
        print("\n请配置账号的 group_ids:")
        for acc in online_accounts:
            print(f"  - {acc.account_id}: 当前群组 {acc.config.group_ids}")
        print(f"\n需要添加群组ID: {test_group_id}")
        return
    
    print(f"\n✅ 找到 {len(accounts_for_group)} 个账号可以发送消息到群组 {test_group_id}")
    
    # 询问是否继续
    print("\n准备发送测试事件...")
    print("  事件类型: GAME_START")
    print(f"  目标群组: {test_group_id}")
    
    user_input = input("\n是否继续？(y/N): ").strip().lower()
    if user_input != 'y':
        print("已取消")
        return
    
    # 发送测试事件
    event = GameEvent(
        event_type="GAME_START",
        event_id="quick_test_001",
        group_id=test_group_id,
        game_id="test_game",
        timestamp=datetime.now(),
        payload={}
    )
    
    print(f"\n发送游戏开始事件到群组 {test_group_id}...")
    try:
        await sm.handle_game_start(event)
        print("✅ 事件已发送，请检查群组是否收到消息")
        print("\n提示:")
        print("  - 如果群组中收到引导消息，说明功能正常")
        print("  - 如果没有收到，请检查:")
        print("    1. 账号是否真的在线")
        print("    2. 账号是否有权限在该群组发送消息")
        print("    3. 群组ID是否正确")
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

