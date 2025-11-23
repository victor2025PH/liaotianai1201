#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试API扫描功能，模拟API调用环境
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
from app.db import SessionLocal, get_db
from app.models.user import User

def test_api_scan():
    """测试API扫描功能"""
    print("\n" + "="*60)
    print("直接测试API扫描功能（模拟API调用环境）")
    print("="*60 + "\n")
    
    # 获取数据库会话（模拟FastAPI的get_db依赖）
    db_gen = get_db()
    db = next(db_gen)
    try:
        print(f"[OK] 数据库会话: {db is not None}, {type(db)}")
        
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
        print(f"     host: {server_node.host}")
        print(f"     deploy_dir: {server_node.deploy_dir}")
        print()
        
        # 调用扫描函数（模拟API路由中的调用）
        print("="*60)
        print("调用扫描函数（模拟API路由）")
        print("="*60 + "\n")
        
        try:
            print("准备调用 scan_server_accounts...")
            accounts = scan_server_accounts(server_node, db)
            print(f"[OK] 扫描完成，找到 {len(accounts)} 个账号\n")
            
            if accounts:
                for acc in accounts:
                    print(f"  - account_id: {acc.account_id}")
                    print(f"    session_file: {acc.session_file}")
                    print(f"    file_size: {acc.file_size}")
                    print(f"    modified_time: {acc.modified_time}")
                    print()
            else:
                print("[WARNING] 未找到任何账号")
        except Exception as e:
            print(f"[ERROR] 扫描失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    finally:
        db.close()
    
    print("="*60)
    print("测试完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_api_scan()

