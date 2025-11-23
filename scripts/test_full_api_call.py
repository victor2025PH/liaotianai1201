#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整测试API调用，包括权限检查
"""
import sys
import logging
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "admin-backend"))

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from app.api.group_ai.session_uploader import SessionUploader
from app.api.group_ai.account_management import scan_server_accounts, ScanServerAccountsResponse
from app.db import SessionLocal
from app.models.user import User

async def test_full_api_call():
    """完整测试API调用"""
    print("\n" + "="*60)
    print("完整测试API调用（包括异步）")
    print("="*60 + "\n")
    
    # 获取数据库会话
    db = SessionLocal()
    try:
        # 获取用户（模拟current_user）
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if not user:
            print("[ERROR] 未找到用户 admin@example.com")
            return
        
        print(f"[OK] 找到用户: {user.email}")
        
        # 获取服务器节点
        uploader = SessionUploader()
        if "worker-01" not in uploader.servers:
            print("[ERROR] 未找到服务器 worker-01")
            return
        
        server_node = uploader.servers["worker-01"]
        print(f"[OK] 找到服务器: {server_node.node_id}")
        print()
        
        # 模拟API路由的完整流程（异步）
        print("="*60)
        print("模拟API路由的完整流程（异步）")
        print("="*60 + "\n")
        
        results = []
        servers_to_scan = [server_node]
        
        for server_node in servers_to_scan:
            print(f"处理服务器: {server_node.node_id}")
            print("-" * 60)
            
            try:
                print("调用 asyncio.to_thread(scan_server_accounts)...")
                accounts = await asyncio.to_thread(scan_server_accounts, server_node, db)
                print(f"[OK] 扫描完成，找到 {len(accounts)} 个账号")
                
                if accounts:
                    for acc in accounts:
                        print(f"  - account_id: {acc.account_id}")
                        print(f"    session_file: {acc.session_file}")
                
                print("\n创建 ScanServerAccountsResponse...")
                result = ScanServerAccountsResponse(
                    server_id=server_node.node_id,
                    accounts=accounts,
                    total_count=len(accounts)
                )
                print(f"[OK] 创建成功: server_id={result.server_id}, total_count={result.total_count}")
                
                print("\n添加到results...")
                results.append(result)
                print(f"[OK] 已添加，results长度: {len(results)}")
                
            except Exception as e:
                print(f"[ERROR] 处理服务器 {server_node.node_id} 时出错: {e}")
                import traceback
                traceback.print_exc()
                # 添加空结果
                results.append(ScanServerAccountsResponse(
                    server_id=server_node.node_id,
                    accounts=[],
                    total_count=0
                ))
        
        print("\n" + "="*60)
        print("最终结果")
        print("="*60 + "\n")
        print(f"results长度: {len(results)}")
        for i, result in enumerate(results):
            print(f"\n结果 {i+1}:")
            print(f"  server_id: {result.server_id}")
            print(f"  accounts数量: {len(result.accounts)}")
            print(f"  total_count: {result.total_count}")
            if result.accounts:
                for acc in result.accounts:
                    print(f"    - {acc.account_id}: {acc.session_file}")
        
    finally:
        db.close()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_full_api_call())

