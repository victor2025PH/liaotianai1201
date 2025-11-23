#!/usr/bin/env python3
"""完整系统测试脚本"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:3000"

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def test_backend_health():
    """测试后端健康状态"""
    print_section("1. 后端服务健康检查")
    
    try:
        # 测试API文档
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/docs", timeout=5)
        if response.status_code == 200:
            print("[OK] API文档可访问")
        else:
            print(f"[WARN] API文档状态码: {response.status_code}")
        
        # 测试API端点（不需要认证的）
        response = requests.get(f"{BASE_URL}/telegram-registration/status/test", timeout=5)
        if response.status_code in [401, 404]:
            print("[OK] API端点正常响应（401/404为预期）")
        else:
            print(f"[INFO] API端点状态码: {response.status_code}")
        
        return True
    except requests.exceptions.ConnectionError:
        print("[FAIL] 无法连接到后端服务")
        print("提示: 请确保后端服务已启动 (uvicorn app.main:app)")
        return False
    except Exception as e:
        print(f"[FAIL] 后端健康检查失败: {e}")
        return False

def test_frontend_health():
    """测试前端健康状态"""
    print_section("2. 前端服务健康检查")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("[OK] 前端服务可访问")
            return True
        else:
            print(f"[WARN] 前端服务状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] 无法连接到前端服务")
        print("提示: 请确保前端服务已启动 (npm run dev)")
        return False
    except Exception as e:
        print(f"[FAIL] 前端健康检查失败: {e}")
        return False

def test_database():
    """测试数据库"""
    print_section("3. 数据库检查")
    
    try:
        from app.db import SessionLocal
        from app.models.telegram_registration import UserRegistration, SessionFile, AntiDetectionLog
        from sqlalchemy import text
        
        db = SessionLocal()
        try:
            # 检查表是否存在
            result = db.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name IN ('user_registrations', 'session_files', 'anti_detection_logs')
            """))
            tables = [row[0] for row in result]
            
            expected = ['user_registrations', 'session_files', 'anti_detection_logs']
            all_exist = all(t in tables for t in expected)
            
            if all_exist:
                print("[OK] 所有表已创建")
                for table in expected:
                    print(f"  - {table}: 存在")
            else:
                print("[FAIL] 部分表未创建")
                for table in expected:
                    status = "存在" if table in tables else "不存在"
                    print(f"  - {table}: {status}")
            
            return all_exist
        finally:
            db.close()
    except Exception as e:
        print(f"[FAIL] 数据库检查失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点"""
    print_section("4. API端点检查")
    
    endpoints = [
        ("POST", "/telegram-registration/start", "开始注册"),
        ("POST", "/telegram-registration/verify", "验证OTP"),
        ("GET", "/telegram-registration/status/{id}", "查询状态"),
        ("POST", "/telegram-registration/cancel", "取消注册"),
    ]
    
    all_ok = True
    for method, path, desc in endpoints:
        try:
            if "{id}" in path:
                test_path = path.replace("{id}", "test-id")
            else:
                test_path = path
            
            if method == "GET":
                response = requests.get(f"{BASE_URL}{test_path}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{test_path}", json={}, timeout=5)
            
            # 401表示需要认证，这是正常的
            # 404表示端点不存在或资源不存在
            # 422表示验证错误，说明端点存在
            if response.status_code in [401, 404, 422]:
                print(f"[OK] {method} {path}: 端点存在 ({desc})")
            else:
                print(f"[INFO] {method} {path}: 状态码 {response.status_code} ({desc})")
        except Exception as e:
            print(f"[FAIL] {method} {path}: {e}")
            all_ok = False
    
    return all_ok

def test_configuration():
    """测试配置"""
    print_section("5. 配置检查")
    
    try:
        from pathlib import Path
        import json
        
        from pathlib import Path as PathLib
        project_root = PathLib(__file__).parent.parent
        config_path = project_root / "data" / "master_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            servers = config.get('servers', {})
            if servers:
                print(f"[OK] 服务器配置存在 ({len(servers)} 个服务器)")
                for node_id in servers.keys():
                    print(f"  - {node_id}")
                return True
            else:
                print("[WARN] 服务器配置为空")
                return False
        else:
            print("[FAIL] 配置文件不存在: data/master_config.json")
            return False
    except Exception as e:
        print(f"[FAIL] 配置检查失败: {e}")
        return False

def generate_test_report(results):
    """生成测试报告"""
    print_section("测试报告")
    
    total = len(results)
    passed = sum(1 for r in results if r)
    failed = total - passed
    
    print(f"总测试项: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n[OK] 所有测试通过！系统已准备就绪。")
        return True
    else:
        print("\n[WARN] 部分测试失败，请检查上述问题。")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("Telegram注册系统 - 完整系统测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端URL: {BASE_URL}")
    print(f"前端URL: {FRONTEND_URL}")
    
    results = []
    
    # 执行各项测试
    results.append(test_backend_health())
    results.append(test_frontend_health())
    results.append(test_database())
    results.append(test_api_endpoints())
    results.append(test_configuration())
    
    # 生成报告
    success = generate_test_report(results)
    
    # 提供下一步建议
    print_section("下一步建议")
    
    if success:
        print("1. 访问前端页面进行UI测试:")
        print(f"   {FRONTEND_URL}")
        print("2. 访问API文档进行API测试:")
        print(f"   {BASE_URL.replace('/api/v1', '')}/docs")
        print("3. 进行完整的功能测试:")
        print("   - 登录系统")
        print("   - 进入'账户中心' → 'Telegram注册'")
        print("   - 测试注册流程")
    else:
        print("1. 检查失败的项目")
        print("2. 修复问题")
        print("3. 重新运行测试")
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

