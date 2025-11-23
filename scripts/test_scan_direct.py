#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试扫描函数
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "admin-backend"))

from app.api.group_ai.session_uploader import SessionUploader, ServerNode
from app.api.group_ai.account_management import scan_server_accounts
from app.db import SessionLocal

def test_scan():
    """测试扫描函数"""
    print("\n" + "="*60)
    print("直接测试扫描函数")
    print("="*60 + "\n")
    
    # 获取服务器节点
    uploader = SessionUploader()
    if "worker-01" not in uploader.servers:
        print("❌ 未找到服务器 worker-01")
        return
    
    server_node = uploader.servers["worker-01"]
    print(f"服务器: {server_node.node_id}")
    print(f"主机: {server_node.host}")
    print(f"部署目录: {server_node.deploy_dir}")
    print()
    
    # 获取数据库会话
    db = SessionLocal()
    try:
        # 调用扫描函数
        print("开始扫描...")
        accounts = scan_server_accounts(server_node, db)
        
        print(f"\n扫描结果: 找到 {len(accounts)} 个账号\n")
        
        if accounts:
            for acc in accounts:
                print(f"  - account_id: {acc.account_id}")
                print(f"    session_file: {acc.session_file}")
                print(f"    file_size: {acc.file_size}")
                print(f"    modified_time: {acc.modified_time}")
                print()
        else:
            print("⚠️  未找到任何账号")
    except Exception as e:
        print(f"❌ 扫描失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("="*60)
    print("测试完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_scan()

