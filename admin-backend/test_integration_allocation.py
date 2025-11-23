"""
智能分配系统集成测试
测试完整的账号分配流程
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.db import SessionLocal
from app.core.intelligent_allocator import IntelligentAllocator
from app.core.load_balancer import AllocationStrategy
from app.models.group_ai import GroupAIAccount, AllocationHistory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_server_monitoring():
    """测试服务器监控功能"""
    print("\n" + "="*60)
    print("集成测试1: 服务器监控")
    print("="*60)
    
    try:
        allocator = IntelligentAllocator()
        
        # 检查所有服务器
        print("\n[1.1] 检查所有服务器状态...")
        server_metrics = await allocator.server_monitor.check_all_servers()
        
        if not server_metrics:
            print("   [FAIL] 没有可用的服务器")
            return False
        
        print(f"   [OK] 找到 {len(server_metrics)} 个服务器:")
        for node_id, metrics in server_metrics.items():
            print(f"      - {node_id}:")
            print(f"        CPU: {metrics.cpu_usage:.1f}%")
            print(f"        内存: {metrics.memory_usage:.1f}%")
            print(f"        账号: {metrics.current_accounts}/{metrics.max_accounts}")
            print(f"        延迟: {metrics.network_latency:.1f}ms")
            print(f"        状态: {metrics.status}")
        
        # 检查服务器健康状态
        print("\n[1.2] 检查服务器健康状态...")
        healthy_count = 0
        for node_id in server_metrics.keys():
            is_healthy = allocator.server_monitor.is_server_healthy(node_id)
            health_status = allocator.server_monitor.get_server_health_status(node_id)
            if is_healthy:
                healthy_count += 1
                print(f"      [OK] {node_id}: 健康")
            else:
                print(f"      [WARN] {node_id}: 故障 (连续失败: {health_status.consecutive_failures if health_status else 0} 次)")
        
        print(f"\n   [OK] {healthy_count}/{len(server_metrics)} 个服务器健康")
        return True
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_allocation_strategies():
    """测试不同分配策略"""
    print("\n" + "="*60)
    print("集成测试2: 分配策略")
    print("="*60)
    
    try:
        allocator = IntelligentAllocator()
        
        # 获取服务器指标
        server_metrics = await allocator.server_monitor.check_all_servers()
        if not server_metrics:
            print("   [WARN] 没有可用的服务器，跳过策略测试")
            return False
        
        server_list = list(server_metrics.values())
        
        # 测试负载均衡策略
        print("\n[2.1] 测试负载均衡策略...")
        best_server = allocator.load_balancer.select_best_server(
            server_list,
            strategy=AllocationStrategy.LOAD_BALANCE
        )
        if best_server:
            score = allocator.load_balancer.calculate_load_score(best_server)
            print(f"   [OK] 选择服务器: {best_server.node_id}, 负载分数: {score.total_score:.2f}")
        else:
            print("   [WARN] 未找到可用服务器（可能所有服务器已满）")
        
        # 测试地理位置策略
        print("\n[2.2] 测试地理位置策略...")
        best_server = allocator.load_balancer.select_best_server(
            server_list,
            strategy=AllocationStrategy.LOCATION,
            account_location="LosAngeles"
        )
        if best_server:
            score = allocator.load_balancer.calculate_load_score(best_server)
            print(f"   [OK] 选择服务器: {best_server.node_id}, 负载分数: {score.total_score:.2f}, 位置: {best_server.location}")
        else:
            print("   [WARN] 未找到可用服务器")
        
        # 测试剧本亲和性策略
        print("\n[2.3] 测试剧本亲和性策略...")
        db = SessionLocal()
        try:
            server_scripts = allocator._get_server_scripts(db)
            best_server = allocator.load_balancer.select_best_server(
                server_list,
                strategy=AllocationStrategy.AFFINITY,
                script_id="000新人欢迎剧本",
                server_scripts=server_scripts
            )
            if best_server:
                score = allocator.load_balancer.calculate_load_score(best_server)
                print(f"   [OK] 选择服务器: {best_server.node_id}, 负载分数: {score.total_score:.2f}")
            else:
                print("   [WARN] 未找到可用服务器")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_account_type_strategies():
    """测试账号类型策略"""
    print("\n" + "="*60)
    print("集成测试3: 账号类型策略")
    print("="*60)
    
    try:
        allocator = IntelligentAllocator()
        
        # 测试不同账号类型的策略
        print("\n[3.1] 测试账号类型策略映射...")
        strategies = {
            "default": allocator.get_strategy_for_account_type("default"),
            "high_priority": allocator.get_strategy_for_account_type("high_priority"),
            "batch": allocator.get_strategy_for_account_type("batch"),
        }
        
        for account_type, strategy in strategies.items():
            print(f"   [OK] {account_type}: {strategy.value}")
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_allocation_history():
    """测试分配历史记录"""
    print("\n" + "="*60)
    print("集成测试4: 分配历史记录")
    print("="*60)
    
    try:
        db = SessionLocal()
        try:
            # 查询分配历史
            print("\n[4.1] 查询分配历史...")
            history_records = db.query(AllocationHistory).limit(10).all()
            print(f"   [OK] 找到 {len(history_records)} 条历史记录")
            
            for record in history_records[:5]:
                print(f"      - 账号: {record.account_id}, 服务器: {record.server_id}, "
                      f"类型: {record.allocation_type}, 策略: {record.strategy}")
            
            return True
        finally:
            db.close()
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_existing_accounts():
    """测试现有账号分配情况"""
    print("\n" + "="*60)
    print("集成测试5: 现有账号分配")
    print("="*60)
    
    try:
        db = SessionLocal()
        try:
            # 查询已分配的账号
            print("\n[5.1] 查询已分配的账号...")
            allocated_accounts = db.query(GroupAIAccount).filter(
                GroupAIAccount.server_id.isnot(None)
            ).all()
            
            print(f"   [OK] 找到 {len(allocated_accounts)} 个已分配的账号")
            
            # 按服务器分组统计
            server_accounts = {}
            for account in allocated_accounts:
                server_id = account.server_id
                if server_id not in server_accounts:
                    server_accounts[server_id] = []
                server_accounts[server_id].append(account.account_id)
            
            print("\n[5.2] 按服务器统计账号分布:")
            for server_id, account_ids in server_accounts.items():
                print(f"      - {server_id}: {len(account_ids)} 个账号")
                if len(account_ids) <= 5:
                    print(f"        账号列表: {', '.join(account_ids)}")
            
            # 按剧本分组统计
            script_accounts = {}
            for account in allocated_accounts:
                if account.script_id:
                    script_id = account.script_id
                    if script_id not in script_accounts:
                        script_accounts[script_id] = []
                    script_accounts[script_id].append(account.account_id)
            
            if script_accounts:
                print("\n[5.3] 按剧本统计账号分布:")
                for script_id, account_ids in script_accounts.items():
                    print(f"      - {script_id}: {len(account_ids)} 个账号")
            
            return True
        finally:
            db.close()
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("智能分配系统集成测试")
    print("="*60)
    
    results = []
    
    # 测试服务器监控
    results.append(("服务器监控", await test_server_monitoring()))
    
    # 测试分配策略
    results.append(("分配策略", await test_allocation_strategies()))
    
    # 测试账号类型策略
    results.append(("账号类型策略", await test_account_type_strategies()))
    
    # 测试分配历史
    results.append(("分配历史记录", await test_allocation_history()))
    
    # 测试现有账号
    results.append(("现有账号分配", await test_existing_accounts()))
    
    # 输出测试结果
    print("\n" + "="*60)
    print("集成测试结果总结")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "[PASS] 通过" if result else "[FAIL] 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

