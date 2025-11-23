#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试HTTP API，模拟完整的请求处理流程
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_api.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

def test_http_api_direct():
    """直接测试HTTP API"""
    print("\n" + "="*60)
    print("直接测试HTTP API（使用TestClient）")
    print("="*60 + "\n")
    
    # 创建测试客户端
    client = TestClient(app)
    
    # 获取用户并创建token
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if not user:
            print("[ERROR] 未找到用户 admin@example.com")
            return
        
        # 创建访问token
        from datetime import timedelta
        token = create_access_token(
            subject=user.email,
            expires_delta=timedelta(hours=24)
        )
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"[OK] 创建token成功，用户: {user.email}")
        print()
        
        # 调用API
        print("="*60)
        print("调用HTTP API")
        print("="*60 + "\n")
        
        try:
            print("准备调用 GET /api/v1/group-ai/account-management/scan-server-accounts?server_id=worker-01")
            response = client.get(
                "/api/v1/group-ai/account-management/scan-server-accounts?server_id=worker-01",
                headers=headers,
                timeout=30.0
            )
            
            print(f"[OK] HTTP响应状态码: {response.status_code}")
            print(f"[OK] HTTP响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[OK] 响应JSON解析成功")
                    print(f"   响应类型: {type(data)}")
                    print(f"   响应内容: {data}")
                    
                    if isinstance(data, list) and len(data) > 0:
                        first_result = data[0]
                        print(f"\n第一个结果:")
                        print(f"   server_id: {first_result.get('server_id')}")
                        print(f"   accounts数量: {len(first_result.get('accounts', []))}")
                        print(f"   total_count: {first_result.get('total_count')}")
                        
                        if first_result.get('accounts'):
                            print(f"\n账号列表:")
                            for acc in first_result.get('accounts', []):
                                print(f"   - {acc.get('account_id')}: {acc.get('session_file')}")
                        else:
                            print(f"\n⚠️  账号列表为空")
                    else:
                        print(f"\n⚠️  响应为空或格式不正确")
                except Exception as json_error:
                    print(f"[ERROR] JSON解析失败: {json_error}")
                    print(f"   响应内容: {response.text[:500]}")
            else:
                print(f"[ERROR] HTTP响应状态码: {response.status_code}")
                print(f"   响应内容: {response.text[:500]}")
        except Exception as e:
            print(f"[ERROR] API调用失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_http_api_direct()

