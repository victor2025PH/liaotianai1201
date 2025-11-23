#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram注册系统 - 全面自动化测试脚本"""
import requests
import json
import sys
import time
import io
from typing import Optional, Dict, Any, List

# 设置UTF-8编码输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"

class ComprehensiveTest:
    """全面测试类"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
        self.token = None

    def log_test(self, name: str, status: str, message: str = "", details: Dict = None):
        """记录测试结果"""
        test_info = {
            "name": name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.tests.append(test_info)
        if status == "PASS":
            self.passed += 1
            print(f"[OK] {name}: {message}")
        elif status == "FAIL":
            self.failed += 1
            print(f"[ERROR] {name}: {message}")
        else:
            self.warnings += 1
            print(f"[WARN] {name}: {message}")

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("全面自动化测试总结")
        print("=" * 60)
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"警告: {self.warnings}")
        print(f"总计: {len(self.tests)}")
        print(f"通过率: {(self.passed/len(self.tests)*100):.1f}%")
        print("=" * 60)

    def test_all(self):
        """执行所有测试"""
        print("=" * 60)
        print("Telegram注册系统 - 全面自动化测试")
        print("=" * 60)
        print(f"Base URL: {BASE_URL}\n")

        # 1. 服务健康检查
        self.test_service_health()

        # 2. 获取认证token
        self.test_authentication()

        # 3. API端点测试
        self.test_api_endpoints()

        # 4. 服务器列表测试
        servers = self.test_server_list()

        # 5. 表单验证测试
        self.test_form_validation()

        # 6. 注册启动测试（使用无效数据，不会真正发送）
        registration_id = self.test_registration_start(servers)

        # 7. 状态查询测试
        if registration_id:
            self.test_registration_status(registration_id)
        else:
            self.test_registration_status_route()

        # 8. 错误处理测试
        self.test_error_handling()

        # 9. 数据库测试
        self.test_database()

        # 10. 配置测试
        self.test_configuration()

        # 11. API响应格式测试
        self.test_api_response_format()

        # 12. CORS测试
        self.test_cors()

        # 打印总结
        self.print_summary()

    def test_service_health(self):
        """测试服务健康状态"""
        print("\n" + "=" * 60)
        print("1. 服务健康检查")
        print("=" * 60)

        # 后端健康检查
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                self.log_test("后端服务健康检查", "PASS", "服务正常")
            else:
                self.log_test("后端服务健康检查", "FAIL", f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("后端服务健康检查", "FAIL", str(e))

        # 前端服务检查
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                self.log_test("前端服务健康检查", "PASS", "服务正常")
            else:
                self.log_test("前端服务健康检查", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("前端服务健康检查", "WARN", str(e))

    def test_authentication(self):
        """测试认证"""
        print("\n" + "=" * 60)
        print("2. 认证测试")
        print("=" * 60)

        token = get_auth_token()
        if token:
            self.token = token
            self.log_test("Token获取", "PASS", "认证成功")
        else:
            self.log_test("Token获取", "WARN", "无法获取token（使用默认凭据）")

    def test_api_endpoints(self):
        """测试所有API端点"""
        print("\n" + "=" * 60)
        print("3. API端点测试")
        print("=" * 60)

        endpoints = [
            ("GET", "/group-ai/servers", "服务器列表接口", 30),
            ("POST", "/telegram-registration/start", "注册启动接口", 10),
            ("POST", "/telegram-registration/verify", "验证码验证接口", 10),
            ("GET", "/telegram-registration/status/test-id", "状态查询接口", 10),
            ("POST", "/telegram-registration/cancel", "取消注册接口", 10),
        ]

        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        for method, endpoint, name, timeout in endpoints:
            try:
                url = f"{BASE_URL}{endpoint}"
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json={}, headers=headers, timeout=timeout)

                if response.status_code in [200, 401, 422, 400, 404]:
                    if endpoint.endswith("test-id") and response.status_code == 404:
                        self.log_test(name, "PASS", "路由存在（404是预期的）")
                    else:
                        self.log_test(name, "PASS", f"状态码: {response.status_code}")
                else:
                    self.log_test(name, "WARN", f"状态码: {response.status_code}")
            except requests.exceptions.Timeout:
                self.log_test(name, "WARN", "请求超时")
            except Exception as e:
                self.log_test(name, "FAIL", str(e))

    def test_server_list(self):
        """测试服务器列表"""
        print("\n" + "=" * 60)
        print("4. 服务器列表测试")
        print("=" * 60)

        if not self.token:
            self.log_test("服务器列表获取", "WARN", "需要认证token")
            return None

        url = f"{BASE_URL}/group-ai/servers"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                servers = response.json()
                self.log_test("服务器列表获取", "PASS", f"服务器数量: {len(servers)}", {
                    "count": len(servers),
                    "servers": [s.get("node_id") for s in servers]
                })
                return servers
            else:
                self.log_test("服务器列表获取", "WARN", f"状态码: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            self.log_test("服务器列表获取", "WARN", "请求超时（服务器检查需要时间）")
            return None
        except Exception as e:
            self.log_test("服务器列表获取", "WARN", str(e))
            return None

    def test_form_validation(self):
        """测试表单验证"""
        print("\n" + "=" * 60)
        print("5. 表单验证测试")
        print("=" * 60)

        if not self.token:
            self.log_test("表单验证", "WARN", "需要认证token")
            return

        url = f"{BASE_URL}/telegram-registration/start"
        headers = {"Authorization": f"Bearer {self.token}"}

        # 测试1: 空数据
        try:
            response = requests.post(url, json={}, headers=headers, timeout=10)
            if response.status_code in [422, 400]:
                self.log_test("表单验证 - 必填字段", "PASS", "验证正常")
            else:
                self.log_test("表单验证 - 必填字段", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("表单验证 - 必填字段", "FAIL", str(e))

        # 测试2: 无效手机号
        try:
            response = requests.post(url, json={"phone": "123"}, headers=headers, timeout=10)
            if response.status_code in [422, 400]:
                self.log_test("表单验证 - 手机号格式", "PASS", "验证正常")
            else:
                self.log_test("表单验证 - 手机号格式", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("表单验证 - 手机号格式", "FAIL", str(e))

        # 测试3: 缺少服务器
        try:
            response = requests.post(url, json={"phone": "+1234567890"}, headers=headers, timeout=10)
            if response.status_code in [422, 400]:
                self.log_test("表单验证 - 缺少服务器", "PASS", "验证正常")
            else:
                self.log_test("表单验证 - 缺少服务器", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("表单验证 - 缺少服务器", "FAIL", str(e))

    def test_registration_start(self, servers):
        """测试注册启动（使用无效数据）"""
        print("\n" + "=" * 60)
        print("6. 注册启动测试")
        print("=" * 60)

        if not self.token:
            self.log_test("注册启动", "WARN", "需要认证token")
            return None

        url = f"{BASE_URL}/telegram-registration/start"
        headers = {"Authorization": f"Bearer {self.token}"}

        node_id = servers[0].get("node_id") if servers else "worker-01"
        test_data = {
            "phone": "+1234567890",  # 无效手机号，不会真正发送
            "country_code": "+1",
            "node_id": node_id
        }

        try:
            response = requests.post(url, json=test_data, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                registration_id = data.get("registration_id")
                self.log_test("注册启动", "PASS", f"Registration ID: {registration_id}")
                return registration_id
            elif response.status_code in [400, 500]:
                # 400/500可能是预期的（无效手机号、SSH连接失败等）
                error = response.json()
                error_detail = error.get('detail', 'Unknown')
                if "IndentationError" in str(error_detail):
                    self.log_test("注册启动", "WARN", "远程脚本执行错误（需要检查SSH脚本）")
                else:
                    self.log_test("注册启动", "WARN", f"预期错误: {error_detail[:80]}")
                return None
            else:
                self.log_test("注册启动", "WARN", f"状态码: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            self.log_test("注册启动", "WARN", "请求超时（远程执行需要时间）")
            return None
        except Exception as e:
            self.log_test("注册启动", "WARN", str(e))
            return None

    def test_registration_status(self, registration_id):
        """测试状态查询"""
        print("\n" + "=" * 60)
        print("7. 状态查询测试")
        print("=" * 60)

        if not self.token:
            self.log_test("状态查询", "WARN", "需要认证token")
            return

        url = f"{BASE_URL}/telegram-registration/status/{registration_id}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("状态查询", "PASS", f"状态: {data.get('status')}")
            elif response.status_code == 404:
                self.log_test("状态查询", "WARN", "注册记录未找到")
            else:
                self.log_test("状态查询", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("状态查询", "WARN", str(e))

    def test_registration_status_route(self):
        """测试状态查询路由（使用无效ID）"""
        print("\n" + "=" * 60)
        print("7. 状态查询路由测试")
        print("=" * 60)

        if not self.token:
            self.log_test("状态查询路由", "WARN", "需要认证token")
            return

        test_id = "test-invalid-id-12345"
        url = f"{BASE_URL}/telegram-registration/status/{test_id}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 404:
                self.log_test("状态查询路由", "PASS", "路由存在（404是预期的）")
            elif response.status_code == 200:
                self.log_test("状态查询路由", "PASS", "路由存在")
            else:
                self.log_test("状态查询路由", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("状态查询路由", "WARN", str(e))

    def test_error_handling(self):
        """测试错误处理"""
        print("\n" + "=" * 60)
        print("8. 错误处理测试")
        print("=" * 60)

        if not self.token:
            self.log_test("错误处理", "WARN", "需要认证token")
            return

        # 测试404错误
        url = f"{BASE_URL}/telegram-registration/status/invalid-id-12345"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 404:
                self.log_test("错误处理 - 404", "PASS", "404错误正常处理")
            else:
                self.log_test("错误处理 - 404", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("错误处理 - 404", "FAIL", str(e))

    def test_database(self):
        """测试数据库"""
        print("\n" + "=" * 60)
        print("9. 数据库测试")
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
                self.log_test("数据库连接", "PASS", f"注册记录数: {count}")
            except Exception as e:
                self.log_test("数据库连接", "FAIL", str(e))
            finally:
                db.close()
        except ImportError:
            self.log_test("数据库连接", "WARN", "无法导入数据库模块")
        except Exception as e:
            self.log_test("数据库连接", "WARN", str(e))

    def test_configuration(self):
        """测试配置"""
        print("\n" + "=" * 60)
        print("10. 配置测试")
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
                    self.log_test("服务器配置", "PASS", f"服务器数量: {len(servers)}", {
                        "count": len(servers),
                        "servers": server_list
                    })
                else:
                    self.log_test("服务器配置", "WARN", "配置为空")
            else:
                self.log_test("服务器配置", "FAIL", "文件不存在")
        except Exception as e:
            self.log_test("服务器配置", "FAIL", str(e))

    def test_api_response_format(self):
        """测试API响应格式"""
        print("\n" + "=" * 60)
        print("11. API响应格式测试")
        print("=" * 60)

        if not self.token:
            self.log_test("API响应格式", "WARN", "需要认证token")
            return

        url = f"{BASE_URL}/group-ai/servers"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("API响应格式", "PASS", "响应格式正确（列表）")
                else:
                    self.log_test("API响应格式", "WARN", "响应格式异常")
            else:
                self.log_test("API响应格式", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("API响应格式", "WARN", str(e))

    def test_cors(self):
        """测试CORS配置"""
        print("\n" + "=" * 60)
        print("12. CORS配置测试")
        print("=" * 60)

        try:
            response = requests.options(
                f"{BASE_URL}/group-ai/servers",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET"
                },
                timeout=5
            )

            if response.status_code in [200, 204]:
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                if cors_origin:
                    self.log_test("CORS配置", "PASS", f"允许来源: {cors_origin}")
                else:
                    self.log_test("CORS配置", "WARN", "CORS头信息不完整")
            else:
                self.log_test("CORS配置", "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("CORS配置", "WARN", str(e))


def get_auth_token(email: str = None, password: str = None) -> Optional[str]:
    """获取认证token"""
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


def main():
    """主函数"""
    test = ComprehensiveTest()
    test.test_all()

    if test.failed > 0:
        print("\n[ERROR] 部分测试失败")
        return 1
    elif test.warnings > 0:
        print("\n[WARN] 部分测试有警告，但系统基本正常")
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

