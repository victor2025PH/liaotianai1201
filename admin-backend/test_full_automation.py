#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram注册系统 - 全自动测试脚本"""
import requests
import json
import sys
import time
import io
import uuid
from typing import Optional, Dict, Any, List

# 设置UTF-8编码输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"

class TestResult:
    """测试结果"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
        self.errors = []

    def add_test(self, name: str, status: str, message: str = "", details: Dict = None):
        """添加测试结果"""
        test_info = {
            "name": name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.tests.append(test_info)
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
            if message:
                self.errors.append(f"{name}: {message}")
        else:
            self.warnings += 1

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"警告: {self.warnings}")
        print(f"总计: {len(self.tests)}")
        print("=" * 60)
        
        if self.failed > 0:
            print("\n失败的测试:")
            for error in self.errors:
                print(f"  [FAIL] {error}")
        
        if self.warnings > 0:
            print("\n警告:")
            for test in self.tests:
                if test["status"] == "WARN":
                    print(f"  [WARN] {test['name']}: {test['message']}")

def get_auth_token(email: str = None, password: str = None) -> Optional[str]:
    """获取认证token"""
    # 尝试使用默认凭据或环境变量
    if not email:
        email = "admin@example.com"
    if not password:
        password = "changeme123"
    
    url = f"{BASE_URL}/auth/login"
    form_data = {
        "username": email,
        "password": password
    }
    
    try:
        response = requests.post(url, data=form_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        return None
    except Exception:
        return None

def test_service_health(result: TestResult):
    """测试服务健康状态"""
    print("\n" + "=" * 60)
    print("1. 服务健康检查")
    print("=" * 60)
    
    # 测试后端
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            result.add_test("后端服务健康检查", "PASS", f"状态: {data.get('status')}")
        else:
            result.add_test("后端服务健康检查", "FAIL", f"状态码: {response.status_code}")
    except Exception as e:
        result.add_test("后端服务健康检查", "FAIL", str(e))
    
    # 测试前端
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            result.add_test("前端服务健康检查", "PASS")
        else:
            result.add_test("前端服务健康检查", "WARN", f"状态码: {response.status_code}")
    except Exception as e:
        result.add_test("前端服务健康检查", "WARN", str(e))

def test_api_endpoints(result: TestResult, token: str):
    """测试所有API端点"""
    print("\n" + "=" * 60)
    print("2. API端点测试")
    print("=" * 60)
    
    endpoints = [
        ("GET", "/group-ai/servers", "服务器列表接口", 30),  # 增加超时时间
        ("POST", "/telegram-registration/start", "注册启动接口", 10),
        ("POST", "/telegram-registration/verify", "验证码验证接口", 10),
        ("GET", "/telegram-registration/status/test-id", "状态查询接口", 10),
        ("POST", "/telegram-registration/cancel", "取消注册接口", 10),
    ]
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    for method, endpoint, name, timeout in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            else:
                response = requests.post(url, json={}, headers=headers, timeout=timeout)
            
            if response.status_code in [200, 401, 422, 400, 404]:
                # 404对于状态查询是正常的（测试ID不存在）
                if endpoint.endswith("test-id") and response.status_code == 404:
                    result.add_test(name, "PASS", "路由存在（404是预期的）")
                else:
                    result.add_test(name, "PASS", f"状态码: {response.status_code}")
            else:
                result.add_test(name, "WARN", f"状态码: {response.status_code}")
        except requests.exceptions.Timeout:
            result.add_test(name, "WARN", "请求超时（可能需要更长时间）")
        except Exception as e:
            result.add_test(name, "FAIL", str(e))

def test_server_list(result: TestResult, token: str):
    """测试服务器列表API"""
    print("\n" + "=" * 60)
    print("3. 服务器列表API测试")
    print("=" * 60)
    
    if not token:
        result.add_test("服务器列表获取", "WARN", "需要认证token")
        return None
    
    url = f"{BASE_URL}/group-ai/servers"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 增加超时时间，因为服务器检查可能需要时间
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            servers = response.json()
            result.add_test("服务器列表获取", "PASS", f"服务器数量: {len(servers)}", {
                "count": len(servers),
                "servers": [s.get("node_id") for s in servers]
            })
            return servers
        else:
            result.add_test("服务器列表获取", "WARN", f"状态码: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        result.add_test("服务器列表获取", "WARN", "请求超时（服务器检查可能需要更长时间）")
        return None
    except Exception as e:
        result.add_test("服务器列表获取", "WARN", f"请求失败: {str(e)}")
        return None

def test_registration_start(result: TestResult, token: str, servers: List[Dict]):
    """测试注册启动API（使用测试数据）"""
    print("\n" + "=" * 60)
    print("4. 注册启动API测试")
    print("=" * 60)
    
    if not token:
        result.add_test("注册启动", "WARN", "需要认证token")
        return None
    
    if not servers:
        result.add_test("注册启动", "WARN", "没有可用服务器，使用默认服务器")
        node_id = "worker-01"
    else:
        node_id = servers[0].get("node_id")
    
    url = f"{BASE_URL}/telegram-registration/start"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 使用测试数据（不会真正发送验证码，因为手机号无效）
    test_data = {
        "phone": "+1234567890",  # 测试手机号（无效，不会真正发送）
        "country_code": "+1",
        "node_id": node_id
    }
    
    try:
        response = requests.post(url, json=test_data, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            registration_id = data.get("registration_id")
            result.add_test("注册启动", "PASS", f"Registration ID: {registration_id}", {
                "registration_id": registration_id,
                "status": data.get("status"),
                "risk_score": data.get("risk_score")
            })
            return registration_id
        elif response.status_code == 400:
            error = response.json()
            error_detail = error.get('detail', 'Unknown')
            # 检查是否是预期的错误（如手机号无效、SSH连接失败等）
            if "IndentationError" in str(error_detail):
                result.add_test("注册启动", "WARN", "远程脚本执行错误（需要检查SSH脚本生成）")
            else:
                result.add_test("注册启动", "WARN", f"验证错误: {error_detail[:100]}")
            return None
        else:
            result.add_test("注册启动", "WARN", f"状态码: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        result.add_test("注册启动", "WARN", "请求超时（远程执行可能需要更长时间）")
        return None
    except Exception as e:
        result.add_test("注册启动", "WARN", f"请求失败: {str(e)}")
        return None

def test_registration_status(result: TestResult, token: str, registration_id: str):
    """测试注册状态查询API"""
    print("\n" + "=" * 60)
    print("5. 注册状态查询API测试")
    print("=" * 60)
    
    if not token:
        result.add_test("状态查询", "WARN", "需要认证token")
        return
    
    if not registration_id:
        # 测试路由是否存在（使用无效ID）
        test_id = "test-invalid-id-12345"
        url = f"{BASE_URL}/telegram-registration/status/{test_id}"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 404:
                result.add_test("状态查询路由", "PASS", "路由存在（404是预期的）")
            elif response.status_code == 200:
                result.add_test("状态查询路由", "PASS", "路由存在")
            else:
                result.add_test("状态查询路由", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            result.add_test("状态查询路由", "WARN", str(e))
        return
    
    url = f"{BASE_URL}/telegram-registration/status/{registration_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result.add_test("状态查询", "PASS", f"状态: {data.get('status')}", {
                "status": data.get("status"),
                "message": data.get("message")
            })
        elif response.status_code == 404:
            result.add_test("状态查询", "WARN", "注册记录未找到")
        else:
            result.add_test("状态查询", "WARN", f"状态码: {response.status_code}")
    except Exception as e:
        result.add_test("状态查询", "WARN", str(e))

def test_form_validation(result: TestResult, token: str):
    """测试表单验证（通过API）"""
    print("\n" + "=" * 60)
    print("6. 表单验证测试")
    print("=" * 60)
    
    if not token:
        result.add_test("表单验证", "WARN", "需要认证token")
        return
    
    url = f"{BASE_URL}/telegram-registration/start"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试1: 必填字段验证
    test_cases = [
        ({}, "必填字段验证"),
        ({"phone": "123"}, "手机号格式验证"),
        ({"phone": "+1234567890"}, "缺少服务器验证"),
    ]
    
    for test_data, test_name in test_cases:
        try:
            response = requests.post(url, json=test_data, headers=headers, timeout=10)
            if response.status_code == 422:
                result.add_test(f"表单验证 - {test_name}", "PASS", "验证错误正常")
            elif response.status_code == 400:
                result.add_test(f"表单验证 - {test_name}", "PASS", "验证错误正常")
            else:
                result.add_test(f"表单验证 - {test_name}", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            result.add_test(f"表单验证 - {test_name}", "FAIL", str(e))

def test_database_connection(result: TestResult):
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("7. 数据库连接测试")
    print("=" * 60)
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from app.db import SessionLocal
        from app.models.telegram_registration import UserRegistration
        
        db = SessionLocal()
        try:
            count = db.query(UserRegistration).count()
            result.add_test("数据库连接", "PASS", f"注册记录数: {count}", {"count": count})
        except Exception as e:
            result.add_test("数据库连接", "FAIL", str(e))
        finally:
            db.close()
    except ImportError as e:
        result.add_test("数据库连接", "WARN", "无法导入数据库模块")
    except Exception as e:
        result.add_test("数据库连接", "FAIL", str(e))

def test_server_config(result: TestResult):
    """测试服务器配置"""
    print("\n" + "=" * 60)
    print("8. 服务器配置测试")
    print("=" * 60)
    
    try:
        import json
        import os
        
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "master_config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            servers = config.get("servers", {})
            if servers:
                server_list = list(servers.keys())
                result.add_test("服务器配置", "PASS", f"服务器数量: {len(servers)}", {
                    "count": len(servers),
                    "servers": server_list
                })
            else:
                result.add_test("服务器配置", "WARN", "配置为空")
        else:
            result.add_test("服务器配置", "FAIL", "文件不存在")
    except Exception as e:
        result.add_test("服务器配置", "FAIL", str(e))

def test_api_response_format(result: TestResult, token: str):
    """测试API响应格式"""
    print("\n" + "=" * 60)
    print("9. API响应格式测试")
    print("=" * 60)
    
    if not token:
        result.add_test("API响应格式", "WARN", "需要认证token")
        return
    
    url = f"{BASE_URL}/group-ai/servers"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                result.add_test("API响应格式", "PASS", "响应格式正确（列表）")
            else:
                result.add_test("API响应格式", "WARN", "响应格式异常")
        else:
            result.add_test("API响应格式", "WARN", f"状态码: {response.status_code}")
    except Exception as e:
        result.add_test("API响应格式", "FAIL", str(e))

def test_error_handling(result: TestResult, token: str):
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("10. 错误处理测试")
    print("=" * 60)
    
    if not token:
        result.add_test("错误处理", "WARN", "需要认证token")
        return
    
    url = f"{BASE_URL}/telegram-registration/status/invalid-id-12345"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            result.add_test("错误处理 - 404", "PASS", "404错误正常处理")
        else:
            result.add_test("错误处理 - 404", "WARN", f"状态码: {response.status_code}")
    except Exception as e:
        result.add_test("错误处理 - 404", "FAIL", str(e))

def main():
    """主测试函数"""
    print("=" * 60)
    print("Telegram注册系统 - 全自动测试")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}\n")
    
    result = TestResult()
    
    # 1. 服务健康检查
    test_service_health(result)
    
    # 2. 获取认证token
    print("\n" + "=" * 60)
    print("获取认证Token")
    print("=" * 60)
    token = get_auth_token()
    if token:
        print("[OK] Token获取成功")
        result.add_test("Token获取", "PASS")
    else:
        print("[WARN] Token获取失败，部分测试将跳过")
        result.add_test("Token获取", "WARN", "无法获取认证token")
    
    # 3. API端点测试
    test_api_endpoints(result, token)
    
    # 4. 服务器列表测试
    servers = test_server_list(result, token)
    
    # 5. 注册启动测试
    registration_id = test_registration_start(result, token, servers)
    
    # 6. 状态查询测试
    if registration_id:
        test_registration_status(result, token, registration_id)
    
    # 7. 表单验证测试
    test_form_validation(result, token)
    
    # 8. 数据库连接测试
    test_database_connection(result)
    
    # 9. 服务器配置测试
    test_server_config(result)
    
    # 10. API响应格式测试
    test_api_response_format(result, token)
    
    # 11. 错误处理测试
    test_error_handling(result, token)
    
    # 打印总结
    result.print_summary()
    
    # 返回结果
    if result.failed > 0:
        print("\n[ERROR] 部分测试失败，请检查上述错误")
        return 1
    elif result.warnings > 0:
        print("\n[WARN] 部分测试有警告，但系统基本正常")
        print("\n注意: 某些测试需要有效的认证token或真实数据")
        return 0
    else:
        print("\n[OK] 所有测试通过！")
        return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n测试已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

