"""
智能分配系统端到端测试
测试完整的账号创建和分配流程
"""
import sys
import asyncio
import json
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


async def test_account_allocation_flow():
    """测试账号分配流程"""
    print("\n" + "="*60)
    print("端到端测试: 账号分配流程")
    print("="*60)
    
    try:
        allocator = IntelligentAllocator()
        
        # 1. 检查服务器状态
        print("\n[1] 检查服务器状态...")
        server_metrics = await allocator.server_monitor.check_all_servers()
        
        if not server_metrics:
            print("   [FAIL] 没有可用的服务器")
            return False
        
        print(f"   [OK] 找到 {len(server_metrics)} 个服务器")
        
        # 检查是否有可用服务器
        available_servers = [
            s for s in server_metrics.values()
            if s.status == "active" and s.current_accounts < s.max_accounts
        ]
        
        if not available_servers:
            print("   [WARN] 所有服务器都已满，无法进行分配测试")
            print("   服务器状态:")
            for node_id, metrics in server_metrics.items():
                print(f"      - {node_id}: {metrics.current_accounts}/{metrics.max_accounts} (状态: {metrics.status})")
            return False
        
        print(f"   [OK] 找到 {len(available_servers)} 个可用服务器")
        
        # 2. 查找session文件
        print("\n[2] 查找session文件...")
        sessions_dir = project_root / "sessions"
        if not sessions_dir.exists():
            print(f"   [WARN] sessions目录不存在: {sessions_dir}")
            return False
        
        session_files = list(sessions_dir.glob("*.session"))
        if not session_files:
            print("   [WARN] 没有找到session文件")
            return False
        
        print(f"   [OK] 找到 {len(session_files)} 个session文件")
        test_session_file = session_files[0]
        print(f"   使用测试文件: {test_session_file.name}")
        
        # 3. 测试分配（不实际创建账号，只测试分配逻辑）
        print("\n[3] 测试分配逻辑...")
        test_account_id = f"test_{Path(test_session_file).stem}"
        
        # 使用负载均衡策略
        best_server = allocator.load_balancer.select_best_server(
            list(server_metrics.values()),
            strategy=AllocationStrategy.LOAD_BALANCE
        )
        
        if best_server:
            score = allocator.load_balancer.calculate_load_score(best_server)
            print(f"   [OK] 选择服务器: {best_server.node_id}")
            print(f"      负载分数: {score.total_score:.2f}")
            print(f"      CPU: {best_server.cpu_usage:.1f}%")
            print(f"      内存: {best_server.memory_usage:.1f}%")
            print(f"      账号: {best_server.current_accounts}/{best_server.max_accounts}")
        else:
            print("   [WARN] 未找到可用服务器")
            return False
        
        # 4. 测试不同策略
        print("\n[4] 测试不同分配策略...")
        
        strategies = [
            (AllocationStrategy.LOAD_BALANCE, "负载均衡"),
            (AllocationStrategy.LOCATION, "地理位置"),
            (AllocationStrategy.AFFINITY, "剧本亲和性"),
        ]
        
        for strategy, name in strategies:
            best = allocator.load_balancer.select_best_server(
                list(server_metrics.values()),
                strategy=strategy,
                account_location="LosAngeles",
                script_id="000新人欢迎剧本"
            )
            if best:
                score = allocator.load_balancer.calculate_load_score(best)
                print(f"   [OK] {name}策略: {best.node_id} (分数: {score.total_score:.2f})")
            else:
                print(f"   [WARN] {name}策略: 未找到可用服务器")
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_allocation_with_db():
    """测试带数据库的分配流程（模拟）"""
    print("\n" + "="*60)
    print("端到端测试: 数据库分配流程（模拟）")
    print("="*60)
    
    try:
        allocator = IntelligentAllocator()
        db = SessionLocal()
        
        try:
            # 1. 查询服务器剧本分布
            print("\n[1] 查询服务器剧本分布...")
            server_scripts = allocator._get_server_scripts(db)
            
            if server_scripts:
                print(f"   [OK] 查询到 {len(server_scripts)} 个服务器的剧本分布:")
                for server_id, scripts in server_scripts.items():
                    print(f"      - {server_id}: {len(scripts)} 个剧本 - {scripts}")
            else:
                print("   [INFO] 当前没有已分配的账号，无法查询剧本分布")
            
            # 2. 查询分配历史
            print("\n[2] 查询分配历史...")
            history_count = db.query(AllocationHistory).count()
            print(f"   [OK] 分配历史记录数: {history_count}")
            
            if history_count > 0:
                recent_history = db.query(AllocationHistory).order_by(
                    AllocationHistory.created_at.desc()
                ).limit(5).all()
                
                print("   最近的分配记录:")
                for record in recent_history:
                    print(f"      - 账号: {record.account_id}, 服务器: {record.server_id}, "
                          f"类型: {record.allocation_type}, 策略: {record.strategy}")
            
            # 3. 查询已分配账号
            print("\n[3] 查询已分配账号...")
            allocated_count = db.query(GroupAIAccount).filter(
                GroupAIAccount.server_id.isnot(None)
            ).count()
            print(f"   [OK] 已分配账号数: {allocated_count}")
            
            return True
            
        finally:
            db.close()
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_configuration_loading():
    """测试配置加载"""
    print("\n" + "="*60)
    print("端到端测试: 配置加载")
    print("="*60)
    
    try:
        allocator = IntelligentAllocator()
        
        # 检查配置
        print("\n[1] 检查分配配置...")
        config = allocator.config
        
        if "allocation" in config:
            allocation_config = config["allocation"]
            print(f"   [OK] 默认策略: {allocation_config.get('default_strategy', 'N/A')}")
            
            account_type_strategies = allocation_config.get("account_type_strategies", {})
            if account_type_strategies:
                print("   账号类型策略:")
                for account_type, strategy in account_type_strategies.items():
                    print(f"      - {account_type}: {strategy}")
        else:
            print("   [WARN] 配置文件中没有allocation配置")
        
        # 检查服务器配置
        print("\n[2] 检查服务器配置...")
        server_configs = allocator.server_monitor.server_configs
        
        if server_configs:
            print(f"   [OK] 加载了 {len(server_configs)} 个服务器配置:")
            for node_id, config in server_configs.items():
                max_accounts = config.get("max_accounts", "N/A")
                location = config.get("location", "N/A")
                print(f"      - {node_id}: max_accounts={max_accounts}, location={location}")
        else:
            print("   [WARN] 没有加载服务器配置")
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("智能分配系统端到端测试")
    print("="*60)
    
    results = []
    
    # 测试配置加载
    results.append(("配置加载", await test_configuration_loading()))
    
    # 测试账号分配流程
    results.append(("账号分配流程", await test_account_allocation_flow()))
    
    # 测试数据库分配流程
    results.append(("数据库分配流程", await test_allocation_with_db()))
    
    # 输出测试结果
    print("\n" + "="*60)
    print("端到端测试结果总结")
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

