#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试API路由函数
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from app.api.group_ai.account_management import scan_all_server_accounts
from app.db import SessionLocal, get_db
from app.models.user import User

async def test_api_route_function():
    """直接测试API路由函数"""
    print("\n" + "="*60)
    print("直接测试API路由函数")
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
        
        # 直接调用API路由函数
        print("="*60)
        print("调用API路由函数 scan_all_server_accounts")
        print("="*60 + "\n")
        
        try:
            print("准备调用 scan_all_server_accounts(server_id='worker-01', current_user=user, db=db)...")
            results = await scan_all_server_accounts(
                server_id="worker-01",
                current_user=user,
                db=db
            )
            print(f"[OK] API路由函数调用成功，返回 {len(results)} 个结果\n")
            
            for result in results:
                print(f"结果:")
                print(f"  server_id: {result.server_id}")
                print(f"  accounts数量: {len(result.accounts)}")
                print(f"  total_count: {result.total_count}")
                if result.accounts:
                    for acc in result.accounts:
                        print(f"    - {acc.account_id}: {acc.session_file}")
                print()
        except Exception as e:
            print(f"[ERROR] API路由函数调用失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    finally:
        db.close()
    
    print("="*60)
    print("测试完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_api_route_function())

