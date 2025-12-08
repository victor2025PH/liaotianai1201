#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram注册系统 - 完整流程测试脚本"""
import requests
import json
import sys
import time
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
                    print(f"  ❌ {test['name']}: {test['message']}")
        
        if self.warnings > 0:
            print("\n警告:")
            for test in self.tests:
                if test["status"] == "WARN":
                    print(f"  ⚠️  {test['name']}: {test['message']}")

def test_service_health(result: TestResult):
    """测试服务健康状态"""
    print("\n" + "=" * 60)
    print("1. 服务健康检查")
    print("=" * 60)
    
    # 测试后端
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("[OK] 后端服务正常")
            result.add_test("后端服务", "PASS")
        else:
            print(f"[WARN] 后端服务响应异常: {response.status_code}")
            result.add_test("后端服务", "WARN", f"状态码: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] 后端服务不可访问: {e}")
        result.add_test("后端服务", "FAIL", str(e))
        return False
    
    # 测试前端
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("[OK] 前端服务正常")
            result.add_test("前端服务", "PASS")
        else:
            print(f"[WARN] 前端服务响应异常: {response.status_code}")
            result.add_test("前端服务", "WARN", f"状态码: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] 前端服务不可访问: {e}")
        result.add_test("前端服务", "FAIL", str(e))
        return False
    
    return True

def test_api_docs(result: TestResult):
    """测试API文档"""
    print("\n" + "=" * 60)
    print("2. API文档检查")
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

def test_api_endpoints(result: TestResult):
    """测试API端点（需要认证）"""
    print("\n" + "=" * 60)
    print("3. API端点检查")
    print("=" * 60)
    
    endpoints = [
        ("/auth/login", "POST", "登录接口"),
        ("/group-ai/servers", "GET", "服务器列表接口"),
        ("/telegram-registration/start", "POST", "注册启动接口"),
    ]
    
    for endpoint, method, name in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json={}, timeout=5)
            
            # 401是预期的（需要认证），404表示路由不存在
            if response.status_code == 401:
                print(f"[OK] {name} 存在（需要认证）")
                result.add_test(name, "PASS")
            elif response.status_code == 404:
                print(f"[ERROR] {name} 不存在")
                result.add_test(name, "FAIL", "路由不存在")
            elif response.status_code == 422:
                print(f"[OK] {name} 存在（参数验证）")
                result.add_test(name, "PASS")
            else:
                print(f"[WARN] {name} 响应: {response.status_code}")
                result.add_test(name, "WARN", f"状态码: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] {name} 测试失败: {e}")
            result.add_test(name, "FAIL", str(e))

def test_database_connection(result: TestResult):
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("4. 数据库连接检查")
    print("=" * 60)
    
    try:
        # 尝试导入数据库模型
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from app.db import SessionLocal
        from app.models.telegram_registration import UserRegistration
        
        db = SessionLocal()
        try:
            # 尝试查询
            count = db.query(UserRegistration).count()
            print(f"[OK] 数据库连接正常（注册记录数: {count}）")
            result.add_test("数据库连接", "PASS")
        except Exception as e:
            print(f"[ERROR] 数据库查询失败: {e}")
            result.add_test("数据库连接", "FAIL", str(e))
        finally:
            db.close()
    except ImportError as e:
        print(f"[WARN] 无法导入数据库模块: {e}")
        result.add_test("数据库连接", "WARN", "无法验证")
    except Exception as e:
        print(f"[ERROR] 数据库连接测试失败: {e}")
        result.add_test("数据库连接", "FAIL", str(e))

def test_server_config(result: TestResult):
    """测试服务器配置"""
    print("\n" + "=" * 60)
    print("5. 服务器配置检查")
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
                print(f"[OK] 服务器配置存在（{len(servers)} 个服务器）")
                for node_id in servers.keys():
                    print(f"  - {node_id}")
                result.add_test("服务器配置", "PASS")
            else:
                print("[WARN] 服务器配置为空")
                result.add_test("服务器配置", "WARN", "配置为空")
        else:
            print(f"[ERROR] 服务器配置文件不存在: {config_path}")
            result.add_test("服务器配置", "FAIL", "文件不存在")
    except Exception as e:
        print(f"[ERROR] 服务器配置检查失败: {e}")
        result.add_test("服务器配置", "FAIL", str(e))

def main():
    """主测试函数"""
    print("=" * 60)
    print("Telegram注册系统 - 完整流程测试")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}\n")
    
    result = TestResult()
    
    # 1. 服务健康检查
    if not test_service_health(result):
        print("\n[ERROR] 服务健康检查失败，请确保前后端服务正在运行")
        result.print_summary()
        return 1
    
    # 2. API文档检查
    test_api_docs(result)
    
    # 3. API端点检查
    test_api_endpoints(result)
    
    # 4. 数据库连接检查
    test_database_connection(result)
    
    # 5. 服务器配置检查
    test_server_config(result)
    
    # 打印总结
    result.print_summary()
    
    # 返回结果
    if result.failed > 0:
        print("\n[ERROR] 部分测试失败，请检查上述错误")
        return 1
    elif result.warnings > 0:
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
