#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前端集成测试 - 验证前端可以正常调用后端API"""
import requests
import json
import sys
import io
from typing import Optional, Dict, Any

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

    def add_test(self, name: str, status: str, message: str = ""):
        """添加测试结果"""
        self.tests.append({
            "name": name,
            "status": status,
            "message": message
        })
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
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
            for test in self.tests:
                if test["status"] == "FAIL":
                    print(f"  [FAIL] {test['name']}: {test['message']}")
        
        if self.warnings > 0:
            print("\n警告:")
            for test in self.tests:
                if test["status"] == "WARN":
                    print(f"  [WARN] {test['name']}: {test['message']}")

def test_frontend_access(result: TestResult):
    """测试前端页面访问"""
    print("\n" + "=" * 60)
    print("1. 前端页面访问测试")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("[OK] 前端页面可访问")
            result.add_test("前端页面访问", "PASS")
        else:
            print(f"[WARN] 前端页面响应异常: {response.status_code}")
            result.add_test("前端页面访问", "WARN", f"状态码: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] 前端页面不可访问: {e}")
        result.add_test("前端页面访问", "FAIL", str(e))

def test_api_endpoints_exist(result: TestResult):
    """测试API端点是否存在"""
    print("\n" + "=" * 60)
    print("2. API端点存在性测试")
    print("=" * 60)
    
    endpoints = [
        ("/auth/login", "POST", "登录接口"),
        ("/group-ai/servers", "GET", "服务器列表接口"),
        ("/telegram-registration/start", "POST", "注册启动接口"),
        ("/telegram-registration/verify", "POST", "验证码验证接口"),
        ("/telegram-registration/status/{id}", "GET", "状态查询接口"),
        ("/telegram-registration/cancel", "POST", "取消注册接口"),
    ]
    
    for endpoint, method, name in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            # 替换路径参数
            url = url.replace("{id}", "test-id")
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json={}, timeout=5)
            
            # 401是预期的（需要认证），404表示路由不存在，422表示参数验证
            if response.status_code in [401, 422]:
                print(f"[OK] {name} 存在（需要认证或参数验证）")
                result.add_test(name, "PASS")
            elif response.status_code == 404:
                print(f"[ERROR] {name} 不存在")
                result.add_test(name, "FAIL", "路由不存在")
            else:
                print(f"[WARN] {name} 响应: {response.status_code}")
                result.add_test(name, "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] {name} 测试失败: {e}")
            result.add_test(name, "FAIL", str(e))

def test_api_response_format(result: TestResult):
    """测试API响应格式"""
    print("\n" + "=" * 60)
    print("3. API响应格式测试")
    print("=" * 60)
    
    # 测试登录接口响应格式
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": "test", "password": "test"},
            timeout=5
        )
        
        if response.status_code == 401:
            # 401表示认证失败，这是正常的（因为我们没有提供有效凭据）
            print("[OK] 登录接口响应格式正常（401认证失败）")
            result.add_test("登录接口响应格式", "PASS")
        elif response.status_code == 422:
            # 422表示参数验证失败，这也是正常的
            print("[OK] 登录接口响应格式正常（422参数验证）")
            result.add_test("登录接口响应格式", "PASS")
        else:
            # 尝试解析JSON
            try:
                data = response.json()
                print(f"[OK] 登录接口响应格式正常: {list(data.keys())}")
                result.add_test("登录接口响应格式", "PASS")
            except:
                print(f"[WARN] 登录接口响应格式异常: {response.status_code}")
                result.add_test("登录接口响应格式", "WARN", "无法解析JSON")
    except Exception as e:
        print(f"[ERROR] 登录接口响应格式测试失败: {e}")
        result.add_test("登录接口响应格式", "FAIL", str(e))

def test_cors_configuration(result: TestResult):
    """测试CORS配置"""
    print("\n" + "=" * 60)
    print("4. CORS配置测试")
    print("=" * 60)
    
    try:
        # 发送OPTIONS请求测试CORS
        response = requests.options(
            f"{BASE_URL}/group-ai/servers",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            },
            timeout=5
        )
        
        if response.status_code in [200, 204]:
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            }
            
            if cors_headers["Access-Control-Allow-Origin"]:
                print(f"[OK] CORS配置正常: {cors_headers['Access-Control-Allow-Origin']}")
                result.add_test("CORS配置", "PASS")
            else:
                print("[WARN] CORS配置可能不完整")
                result.add_test("CORS配置", "WARN", "CORS头信息不完整")
        else:
            print(f"[WARN] CORS预检请求响应: {response.status_code}")
            result.add_test("CORS配置", "WARN", f"状态码: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] CORS配置测试失败: {e}")
        result.add_test("CORS配置", "FAIL", str(e))

def test_api_documentation(result: TestResult):
    """测试API文档"""
    print("\n" + "=" * 60)
    print("5. API文档测试")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("[OK] API文档可访问")
            result.add_test("API文档", "PASS")
        else:
            print(f"[WARN] API文档响应异常: {response.status_code}")
            result.add_test("API文档", "WARN", f"状态码: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] API文档不可访问: {e}")
        result.add_test("API文档", "FAIL", str(e))
    
    try:
        response = requests.get("http://localhost:8000/openapi.json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            paths = data.get("paths", {})
            print(f"[OK] OpenAPI规范可访问（{len(paths)} 个路径）")
            result.add_test("OpenAPI规范", "PASS")
        else:
            print(f"[WARN] OpenAPI规范响应异常: {response.status_code}")
            result.add_test("OpenAPI规范", "WARN", f"状态码: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] OpenAPI规范不可访问: {e}")
        result.add_test("OpenAPI规范", "FAIL", str(e))

def main():
    """主测试函数"""
    print("=" * 60)
    print("前端集成测试")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}\n")
    
    result = TestResult()
    
    # 1. 前端页面访问测试
    test_frontend_access(result)
    
    # 2. API端点存在性测试
    test_api_endpoints_exist(result)
    
    # 3. API响应格式测试
    test_api_response_format(result)
    
    # 4. CORS配置测试
    test_cors_configuration(result)
    
    # 5. API文档测试
    test_api_documentation(result)
    
    # 打印总结
    result.print_summary()
    
    # 返回结果
    if result.failed > 0:
        print("\n[ERROR] 部分测试失败，请检查上述错误")
        return 1
    elif result.warnings > 0:
        print("\n[WARN] 部分测试有警告，但系统基本正常")
        print("\n建议:")
        print("1. 访问前端页面进行手动测试: http://localhost:3000/accounts")
        print("2. 使用Swagger UI测试API: http://localhost:8000/docs")
        return 0
    else:
        print("\n[OK] 所有测试通过！")
        print("\n下一步:")
        print("1. 访问前端页面进行功能测试: http://localhost:3000/accounts")
        print("2. 登录系统并测试Telegram注册功能")
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

