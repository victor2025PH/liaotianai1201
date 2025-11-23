"""
全自动测试所有功能
测试账号管理、去重、智能分配、服务器监控等所有功能
"""
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.db import SessionLocal
from app.core.intelligent_allocator import IntelligentAllocator
from app.core.load_balancer import AllocationStrategy
from app.core.server_monitor import ServerMonitor
from app.models.group_ai import GroupAIAccount, AllocationHistory
from app.api.group_ai.account_management import (
    scan_server_accounts,
    compare_local_and_server_accounts,
    extract_account_id_from_filename
)
from app.api.group_ai.session_uploader import SessionUploader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 禁用一些不必要的日志
logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class TestResults:
    """测试结果收集器"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed.append({"test": test_name, "message": message})
        print(f"   [PASS] {test_name}" + (f": {message}" if message else ""))
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append({"test": test_name, "error": error})
        print(f"   [FAIL] {test_name}: {error}")
    
    def add_warn(self, test_name: str, message: str):
        self.warnings.append({"test": test_name, "message": message})
        print(f"   [WARN] {test_name}: {message}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        pass_rate = len(self.passed) / total * 100 if total > 0 else 0
        return {
            "total": total,
            "passed": len(self.passed),
            "failed": len(self.failed),
            "warnings": len(self.warnings),
            "pass_rate": pass_rate
        }


def test_account_id_extraction():
    """测试账号ID提取功能"""
    print("\n" + "="*60)
    print("测试1: 账号ID提取功能")
    print("="*60)
    
    results = TestResults()
    
    test_cases = [
        ("639277356598.session", "639277356598"),
        ("639277356598.session.encrypted", "639277356598"),
        ("/path/to/639277356598.session", "639277356598"),
        ("/home/ubuntu/sessions/639277356598.session", "639277356598"),
        ("test.session", None),  # 不是纯数字
        ("abc123.session", None),  # 包含字母
    ]
    
    for filename, expected in test_cases:
        result = extract_account_id_from_filename(filename)
        if result == expected:
            results.add_pass(f"提取 {filename}", f"得到 {result}")
        else:
            results.add_fail(f"提取 {filename}", f"期望 {expected}, 得到 {result}")
    
    return results


async def test_server_account_scanning():
    """测试服务器账号扫描功能"""
    print("\n" + "="*60)
    print("测试2: 服务器账号扫描功能")
    print("="*60)
    
    results = TestResults()
    
    try:
        uploader = SessionUploader()
        
        if not uploader.servers:
            results.add_warn("服务器扫描", "没有可用的服务器配置")
            return results
        
        print(f"\n[2.1] 扫描所有服务器...")
        for server_id, server_node in uploader.servers.items():
            try:
                accounts = scan_server_accounts(server_node)
                results.add_pass(
                    f"扫描服务器 {server_id}",
                    f"找到 {len(accounts)} 个账号"
                )
                
                if accounts:
                    print(f"      账号列表: {[acc.account_id for acc in accounts[:5]]}")
            except Exception as e:
                results.add_fail(f"扫描服务器 {server_id}", str(e))
        
    except Exception as e:
        results.add_fail("服务器扫描", str(e))
    
    return results


async def test_account_comparison():
    """测试账号对比功能"""
    print("\n" + "="*60)
    print("测试3: 账号对比功能")
    print("="*60)
    
    results = TestResults()
    
    try:
        db = SessionLocal()
        try:
            # 获取本地账号
            local_accounts = db.query(GroupAIAccount).all()
            local_count = len(local_accounts)
            
            results.add_pass("获取本地账号", f"找到 {local_count} 个本地账号")
            
            # 扫描服务器账号
            uploader = SessionUploader()
            if not uploader.servers:
                results.add_warn("账号对比", "没有可用的服务器配置")
                return results
            
            server_account_ids = set()
            for server_node in uploader.servers.values():
                try:
                    accounts = scan_server_accounts(server_node)
                    for acc in accounts:
                        server_account_ids.add(acc.account_id)
                except Exception as e:
                    results.add_warn(f"扫描服务器 {server_node.node_id}", str(e))
            
            server_count = len(server_account_ids)
            results.add_pass("获取服务器账号", f"找到 {server_count} 个服务器账号")
            
            # 找出重复账号
            local_account_ids = {acc.account_id for acc in local_accounts}
            duplicates = local_account_ids & server_account_ids
            
            if duplicates:
                results.add_warn(
                    "账号对比",
                    f"发现 {len(duplicates)} 个重复账号: {list(duplicates)[:5]}"
                )
            else:
                results.add_pass("账号对比", "没有发现重复账号")
            
        finally:
            db.close()
    
    except Exception as e:
        results.add_fail("账号对比", str(e))
    
    return results


async def test_server_monitoring():
    """测试服务器监控功能"""
    print("\n" + "="*60)
    print("测试4: 服务器监控功能")
    print("="*60)
    
    results = TestResults()
    
    try:
        monitor = ServerMonitor()
        
        print("\n[4.1] 检查所有服务器...")
        server_metrics = await monitor.check_all_servers()
        
        if not server_metrics:
            results.add_warn("服务器监控", "没有可用的服务器")
            return results
        
        results.add_pass("服务器监控", f"监控 {len(server_metrics)} 个服务器")
        
        for node_id, metrics in server_metrics.items():
            print(f"      - {node_id}: CPU={metrics.cpu_usage:.1f}%, "
                  f"内存={metrics.memory_usage:.1f}%, "
                  f"账号={metrics.current_accounts}/{metrics.max_accounts}, "
                  f"延迟={metrics.network_latency:.1f}ms, "
                  f"状态={metrics.status}")
            
            # 检查服务器健康状态
            is_healthy = monitor.is_server_healthy(node_id)
            if is_healthy:
                results.add_pass(f"服务器 {node_id} 健康检查", "健康")
            else:
                results.add_warn(f"服务器 {node_id} 健康检查", "不健康或已满")
    
    except Exception as e:
        results.add_fail("服务器监控", str(e))
    
    return results


async def test_load_balancer():
    """测试负载均衡器"""
    print("\n" + "="*60)
    print("测试5: 负载均衡器")
    print("="*60)
    
    results = TestResults()
    
    try:
        from app.core.load_balancer import LoadBalancer, ServerMetrics
        
        balancer = LoadBalancer()
        
        # 创建测试服务器指标
        test_servers = [
            ServerMetrics(
                node_id="server1",
                cpu_usage=20.0,
                memory_usage=40.0,
                disk_usage=30.0,
                current_accounts=1,
                max_accounts=5,
                network_latency=50.0,
                status="active"
            ),
            ServerMetrics(
                node_id="server2",
                cpu_usage=50.0,
                memory_usage=60.0,
                disk_usage=50.0,
                current_accounts=3,
                max_accounts=5,
                network_latency=100.0,
                status="active"
            ),
            ServerMetrics(
                node_id="server3",
                cpu_usage=10.0,
                memory_usage=30.0,
                disk_usage=20.0,
                current_accounts=0,
                max_accounts=5,
                network_latency=30.0,
                status="active"
            ),
        ]
        
        # 测试负载分数计算
        for server in test_servers:
            score = balancer.calculate_load_score(server)
            results.add_pass(
                f"计算服务器 {server.node_id} 负载分数",
                f"{score.total_score:.2f}"
            )
        
        # 测试服务器选择
        best_server = balancer.select_best_server(
            test_servers,
            AllocationStrategy.LOAD_BALANCE
        )
        
        if best_server:
            score = balancer.calculate_load_score(best_server)
            results.add_pass(
                "选择最优服务器",
                f"{best_server.node_id} (分数: {score.total_score:.2f})"
            )
        else:
            results.add_fail("选择最优服务器", "未找到可用服务器")
        
        # 测试不同策略
        strategies = [
            AllocationStrategy.LOAD_BALANCE,
            AllocationStrategy.LOCATION,
            AllocationStrategy.AFFINITY,
        ]
        
        for strategy in strategies:
            best = balancer.select_best_server(test_servers, strategy)
            if best:
                results.add_pass(f"策略 {strategy.value}", f"选择 {best.node_id}")
            else:
                results.add_warn(f"策略 {strategy.value}", "未找到可用服务器")
    
    except Exception as e:
        results.add_fail("负载均衡器", str(e))
        import traceback
        traceback.print_exc()
    
    return results


async def test_intelligent_allocator():
    """测试智能分配引擎"""
    print("\n" + "="*60)
    print("测试6: 智能分配引擎")
    print("="*60)
    
    results = TestResults()
    
    try:
        allocator = IntelligentAllocator()
        
        # 测试配置加载
        default_strategy = allocator.default_strategy
        results.add_pass("配置加载", f"默认策略: {default_strategy.value}")
        
        # 测试账号类型策略
        strategies = {
            "default": allocator.get_strategy_for_account_type("default"),
            "high_priority": allocator.get_strategy_for_account_type("high_priority"),
            "batch": allocator.get_strategy_for_account_type("batch"),
        }
        
        for account_type, strategy in strategies.items():
            results.add_pass(f"账号类型策略 {account_type}", strategy.value)
        
        # 测试服务器排名
        rankings = await allocator.get_server_rankings()
        if rankings:
            results.add_pass("服务器排名", f"获取到 {len(rankings)} 个服务器排名")
        else:
            results.add_warn("服务器排名", "没有可用的服务器")
        
        # 测试剧本查询
        db = SessionLocal()
        try:
            server_scripts = allocator._get_server_scripts(db)
            if server_scripts:
                results.add_pass(
                    "服务器剧本查询",
                    f"查询到 {len(server_scripts)} 个服务器的剧本分布"
                )
            else:
                results.add_pass("服务器剧本查询", "当前没有已分配的账号")
        finally:
            db.close()
    
    except Exception as e:
        results.add_fail("智能分配引擎", str(e))
        import traceback
        traceback.print_exc()
    
    return results


async def test_allocation_api():
    """测试分配API（模拟）"""
    print("\n" + "="*60)
    print("测试7: 分配API")
    print("="*60)
    
    results = TestResults()
    
    try:
        # 检查API路由是否注册
        import importlib
        allocation_module = importlib.import_module('app.api.group_ai.allocation')
        account_management_module = importlib.import_module('app.api.group_ai.account_management')
        
        if hasattr(allocation_module, 'router'):
            routes = [r.path for r in allocation_module.router.routes]
            results.add_pass("分配API路由", f"找到 {len(routes)} 个路由")
        else:
            results.add_fail("分配API路由", "路由未注册")
        
        if hasattr(account_management_module, 'router'):
            routes = [r.path for r in account_management_module.router.routes]
            results.add_pass("账号管理API路由", f"找到 {len(routes)} 个路由")
        else:
            results.add_fail("账号管理API路由", "路由未注册")
    
    except Exception as e:
        results.add_fail("分配API", str(e))
        import traceback
        traceback.print_exc()
    
    return results


async def test_database_models():
    """测试数据库模型"""
    print("\n" + "="*60)
    print("测试8: 数据库模型")
    print("="*60)
    
    results = TestResults()
    
    try:
        from sqlalchemy import inspect
        from app.db import engine
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # 检查关键表
        required_tables = [
            'group_ai_accounts',
            'group_ai_scripts',
            'allocation_history'
        ]
        
        for table in required_tables:
            if table in tables:
                results.add_pass(f"表 {table}", "存在")
            else:
                results.add_fail(f"表 {table}", "不存在")
        
        # 检查allocation_history表结构
        if 'allocation_history' in tables:
            columns = inspector.get_columns('allocation_history')
            column_names = [col['name'] for col in columns]
            required_columns = ['id', 'account_id', 'server_id', 'allocation_type', 'load_score']
            
            for col in required_columns:
                if col in column_names:
                    results.add_pass(f"字段 {col}", "存在")
                else:
                    results.add_fail(f"字段 {col}", "不存在")
    
    except Exception as e:
        results.add_fail("数据库模型", str(e))
        import traceback
        traceback.print_exc()
    
    return results


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("全自动测试所有功能")
    print("="*60)
    
    all_results = []
    
    # 测试1: 账号ID提取
    all_results.append(("账号ID提取", test_account_id_extraction()))
    
    # 测试2: 服务器账号扫描
    all_results.append(("服务器账号扫描", await test_server_account_scanning()))
    
    # 测试3: 账号对比
    all_results.append(("账号对比", await test_account_comparison()))
    
    # 测试4: 服务器监控
    all_results.append(("服务器监控", await test_server_monitoring()))
    
    # 测试5: 负载均衡器
    all_results.append(("负载均衡器", await test_load_balancer()))
    
    # 测试6: 智能分配引擎
    all_results.append(("智能分配引擎", await test_intelligent_allocator()))
    
    # 测试7: 分配API
    all_results.append(("分配API", await test_allocation_api()))
    
    # 测试8: 数据库模型
    all_results.append(("数据库模型", await test_database_models()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    total_warnings = 0
    
    for test_name, result in all_results:
        summary = result.summary()
        total_passed += summary["passed"]
        total_failed += summary["failed"]
        total_warnings += summary["warnings"]
        
        print(f"\n{test_name}:")
        print(f"  通过: {summary['passed']}, 失败: {summary['failed']}, 警告: {summary['warnings']}")
        if summary['failed'] > 0:
            for fail in result.failed:
                print(f"    - [FAIL] {fail['test']}: {fail['error']}")
    
    print("\n" + "="*60)
    print("总体统计")
    print("="*60)
    print(f"总测试数: {total_passed + total_failed}")
    print(f"通过: {total_passed}")
    print(f"失败: {total_failed}")
    print(f"警告: {total_warnings}")
    
    if total_passed + total_failed > 0:
        pass_rate = total_passed / (total_passed + total_failed) * 100
        print(f"通过率: {pass_rate:.1f}%")
    
    print("="*60)
    
    return total_failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
