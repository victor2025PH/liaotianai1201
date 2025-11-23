#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试API路由，诊断问题
"""
import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "admin-backend"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from app.api.group_ai.session_uploader import SessionUploader
from app.api.group_ai.account_management import scan_server_accounts
from app.db import SessionLocal
from app.models.user import User

def test_api_route():
    """测试API路由逻辑"""
    print("\n" + "="*60)
    print("测试API路由逻辑")
    print("="*60 + "\n")
    
    # 获取数据库会话
    db = SessionLocal()
    try:
        # 获取用户（模拟current_user）
        from app.models.user import User
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
        
        # 调用扫描函数（模拟API路由中的调用）
        print("开始调用扫描函数（模拟API路由）...")
        print("-" * 60)
        
        try:
            accounts = scan_server_accounts(server_node, db)
            print(f"\n[OK] 扫描成功: 找到 {len(accounts)} 个账号\n")
            
            if accounts:
                for acc in accounts:
                    print(f"  - account_id: {acc.account_id}")
                    print(f"    session_file: {acc.session_file}")
                    print(f"    file_size: {acc.file_size}")
                    print(f"    modified_time: {acc.modified_time}")
                    print()
            else:
                print("[WARNING] 未找到任何账号")
                
            # 模拟API路由的返回格式
            from app.api.group_ai.account_management import ScanServerAccountsResponse
            result = ScanServerAccountsResponse(
                server_id=server_node.node_id,
                accounts=accounts,
                total_count=len(accounts)
            )
            print(f"\nAPI路由返回格式:")
            print(f"  server_id: {result.server_id}")
            print(f"  accounts: {len(result.accounts)} 个")
            print(f"  total_count: {result.total_count}")
            
        except Exception as e:
            print(f"[ERROR] 扫描失败: {e}")
            import traceback
            traceback.print_exc()
            
    finally:
        db.close()
    
    print("="*60)
    print("测试完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_api_route()

