"""
智能分配系统测试脚本
测试分配功能、API接口、配置加载等
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
from app.core.server_monitor import ServerMonitor
from app.models.group_ai import GroupAIAccount, AllocationHistory
# 延迟导入避免循环依赖
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_server_monitor():
    """测试服务器监控器"""
    print("\n" + "="*60)
    print("测试1: 服务器监控器")
    print("="*60)
    
    try:
        monitor = ServerMonitor()
        
        # 检查所有服务器
        print("\n[1.1] 检查所有服务器...")
        server_metrics = await monitor.check_all_servers()
        
        if not server_metrics:
            print("   [WARN] 没有可用的服务器配置")
            return False
        
        print(f"   [OK] 找到 {len(server_metrics)} 个服务器")
        for node_id, metrics in server_metrics.items():
            print(f"      - {node_id}: CPU={metrics.cpu_usage:.1f}%, "
                  f"内存={metrics.memory_usage:.1f}%, "
                  f"账号={metrics.current_accounts}/{metrics.max_accounts}, "
                  f"延迟={metrics.network_latency:.1f}ms")
        
        # 检查服务器健康状态
        print("\n[1.2] 检查服务器健康状态...")
        for node_id in server_metrics.keys():
            is_healthy = monitor.is_server_healthy(node_id)
            health_status = monitor.get_server_health_status(node_id)
            status_str = "健康" if is_healthy else "故障"
            print(f"      - {node_id}: {status_str}")
            if health_status:
                print(f"        连续失败: {health_status.consecutive_failures} 次")
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_load_balancer():
    """测试负载均衡器"""
    print("\n" + "="*60)
    print("测试2: 负载均衡器")
    print("="*60)
    
    try:
        from app.core.load_balancer import LoadBalancer, ServerMetrics
        
        balancer = LoadBalancer()
        
        # 创建测试服务器指标
        print("\n[2.1] 测试负载分数计算...")
        test_metrics = ServerMetrics(
            node_id="test-server-1",
            cpu_usage=30.0,
            memory_usage=50.0,
            disk_usage=40.0,
            current_accounts=2,
            max_accounts=5,
            network_latency=50.0,
            status="active"
        )
        
        score = balancer.calculate_load_score(test_metrics)
        print(f"   [OK] 服务器负载分数: {score.total_score:.2f}")
        print(f"      - CPU分数: {score.cpu_score:.2f}")
        print(f"      - 内存分数: {score.memory_score:.2f}")
        print(f"      - 账号分数: {score.account_score:.2f}")
        print(f"      - 磁盘分数: {score.disk_score:.2f}")
        
        # 测试服务器选择
        print("\n[2.2] 测试服务器选择...")
        test_servers = [
            ServerMetrics(node_id="server1", cpu_usage=20.0, memory_usage=40.0, 
                         disk_usage=30.0, current_accounts=1, max_accounts=5, status="active"),
            ServerMetrics(node_id="server2", cpu_usage=50.0, memory_usage=60.0, 
                         disk_usage=50.0, current_accounts=3, max_accounts=5, status="active"),
            ServerMetrics(node_id="server3", cpu_usage=10.0, memory_usage=30.0, 
                         disk_usage=20.0, current_accounts=0, max_accounts=5, status="active"),
        ]
        
        best_server = balancer.select_best_server(test_servers, AllocationStrategy.LOAD_BALANCE)
        if best_server:
            print(f"   [OK] 选择的最优服务器: {best_server.node_id}")
            best_score = balancer.calculate_load_score(best_server)
            print(f"      负载分数: {best_score.total_score:.2f}")
        else:
            print("   [FAIL] 未找到可用服务器")
            return False
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_intelligent_allocator():
    """测试智能分配引擎"""
    print("\n" + "="*60)
    print("测试3: 智能分配引擎")
    print("="*60)
    
    try:
        allocator = IntelligentAllocator()
        
        # 测试配置加载
        print("\n[3.1] 测试配置加载...")
        default_strategy = allocator.default_strategy
        print(f"   [OK] 默认策略: {default_strategy.value}")
        
        # 测试账号类型策略
        print("\n[3.2] 测试账号类型策略...")
        high_priority_strategy = allocator.get_strategy_for_account_type("high_priority")
        batch_strategy = allocator.get_strategy_for_account_type("batch")
        default_type_strategy = allocator.get_strategy_for_account_type("default")
        print(f"   [OK] high_priority策略: {high_priority_strategy.value}")
        print(f"   [OK] batch策略: {batch_strategy.value}")
        print(f"   [OK] default策略: {default_type_strategy.value}")
        
        # 测试服务器排名
        print("\n[3.3] 测试服务器排名...")
        rankings = await allocator.get_server_rankings()
        if rankings:
            print(f"   [OK] 获取到 {len(rankings)} 个服务器排名")
            for i, (server_id, score) in enumerate(rankings[:3], 1):
                print(f"      {i}. {server_id}: {score:.2f}")
        else:
            print("   [WARN] 没有可用的服务器")
        
        # 测试剧本查询
        print("\n[3.4] 测试服务器剧本查询...")
        db = SessionLocal()
        try:
            server_scripts = allocator._get_server_scripts(db)
            if server_scripts:
                print(f"   [OK] 查询到 {len(server_scripts)} 个服务器的剧本分布")
                for server_id, scripts in server_scripts.items():
                    print(f"      - {server_id}: {len(scripts)} 个剧本 - {scripts}")
            else:
                print("   [INFO] 当前没有已分配的账号，无法查询剧本分布")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_model():
    """测试数据库模型"""
    print("\n" + "="*60)
    print("测试4: 数据库模型")
    print("="*60)
    
    try:
        from sqlalchemy import inspect
        from app.db import engine
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # 检查allocation_history表
        print("\n[4.1] 检查allocation_history表...")
        if 'allocation_history' in tables:
            print("   [OK] allocation_history 表已创建")
            
            # 检查表结构
            columns = inspector.get_columns('allocation_history')
            print(f"   [OK] 表包含 {len(columns)} 个字段:")
            for col in columns:
                print(f"      - {col['name']}: {col['type']}")
        else:
            print("   [FAIL] allocation_history 表不存在")
            return False
        
        # 检查其他关键表
        print("\n[4.2] 检查其他关键表...")
        required_tables = ['group_ai_accounts', 'group_ai_scripts']
        for table in required_tables:
            if table in tables:
                print(f"   [OK] {table} 表存在")
            else:
                print(f"   [FAIL] {table} 表不存在")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_allocation_api():
    """测试分配API（模拟）"""
    print("\n" + "="*60)
    print("测试5: 分配API（模拟测试）")
    print("="*60)
    
    try:
        # 检查API路由是否注册
        print("\n[5.1] 检查API路由...")
        # 延迟导入避免循环依赖
        import importlib
        allocation_module = importlib.import_module('app.api.group_ai.allocation')
        if hasattr(allocation_module, 'router'):
            routes = [r.path for r in allocation_module.router.routes]
            print(f"   [OK] 找到 {len(routes)} 个路由:")
            for route in routes:
                print(f"      - {route}")
        else:
            print("   [FAIL] allocation路由未注册")
            return False
        
        return True
        
    except Exception as e:
        print(f"   [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("智能分配系统功能测试")
    print("="*60)
    
    results = []
    
    # 测试数据库模型
    results.append(("数据库模型", test_database_model()))
    
    # 测试服务器监控器
    results.append(("服务器监控器", await test_server_monitor()))
    
    # 测试负载均衡器
    results.append(("负载均衡器", await test_load_balancer()))
    
    # 测试智能分配引擎
    results.append(("智能分配引擎", await test_intelligent_allocator()))
    
    # 测试分配API
    results.append(("分配API", await test_allocation_api()))
    
    # 输出测试结果
    print("\n" + "="*60)
    print("测试结果总结")
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

