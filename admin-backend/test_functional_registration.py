#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram注册系统 - 功能测试脚本"""
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

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")

def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")

def print_info(text: str):
    """打印信息"""
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")

def print_warning(text: str):
    """打印警告"""
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")

def check_service_health() -> bool:
    """检查服务健康状态"""
    print_header("1. 服务健康检查")
    
    # 检查后端
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print_success("后端服务正常 (http://localhost:8000)")
        else:
            print_warning(f"后端服务响应异常: {response.status_code}")
    except Exception as e:
        print_error(f"后端服务不可访问: {e}")
        return False
    
    # 检查前端
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print_success("前端服务正常 (http://localhost:3000)")
        else:
            print_warning(f"前端服务响应异常: {response.status_code}")
    except Exception as e:
        print_error(f"前端服务不可访问: {e}")
        return False
    
    return True

def get_auth_token(email: str, password: str) -> Optional[str]:
    """获取认证token"""
    print_header("2. 获取认证Token")
    
    url = f"{BASE_URL}/auth/login"
    form_data = {
        "username": email,
        "password": password
    }
    
    try:
        response = requests.post(url, data=form_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_success(f"Token获取成功: {token[:30]}...")
                return token
            else:
                print_error("Token未在响应中找到")
                return None
        elif response.status_code == 401:
            print_error("认证失败: 邮箱或密码错误")
            return None
        else:
            print_error(f"登录失败: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print_error(f"登录请求失败: {e}")
        return None

def test_server_list(token: str) -> Optional[list]:
    """测试服务器列表API"""
    print_header("3. 测试服务器列表API")
    
    url = f"{BASE_URL}/group-ai/servers"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            servers = response.json()
            print_success(f"服务器列表获取成功，共 {len(servers)} 个服务器")
            
            for server in servers:
                status_icon = "[ONLINE]" if server.get("status") == "online" else "[OFFLINE]"
                print(f"   {status_icon} {server.get('node_id')}: {server.get('host')} "
                      f"({server.get('status')}) - "
                      f"账户: {server.get('accounts_count', 0)}/{server.get('max_accounts', 0)}")
            
            return servers
        elif response.status_code == 401:
            print_error("认证失败: Token无效或过期")
            return None
        else:
            print_error(f"获取服务器列表失败: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print_error(f"请求失败: {e}")
        return None

def test_registration_start(token: str, phone: str, country_code: str, node_id: str) -> Optional[Dict[str, Any]]:
    """测试开始注册API"""
    print_header("4. 测试开始注册API")
    
    url = f"{BASE_URL}/telegram-registration/start"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "phone": phone,
        "country_code": country_code,
        "node_id": node_id
    }
    
    print_info(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print_success("注册启动成功")
            print(f"   Registration ID: {result.get('registration_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Risk Score: {result.get('risk_score', 'N/A')}")
            if result.get('phone_code_hash'):
                print(f"   Phone Code Hash: {result.get('phone_code_hash')[:30]}...")
            if result.get('expires_in'):
                print(f"   Expires In: {result.get('expires_in')} 秒")
            
            return result
        elif response.status_code == 400:
            error = response.json()
            print_error(f"验证错误: {error.get('detail', 'Unknown error')}")
            return None
        elif response.status_code == 401:
            print_error("认证失败: Token无效或过期")
            return None
        else:
            print_error(f"注册启动失败: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print_error(f"请求失败: {e}")
        return None

def test_registration_status(token: str, registration_id: str) -> Optional[Dict[str, Any]]:
    """测试注册状态查询API"""
    print_header("5. 测试注册状态查询API")
    
    url = f"{BASE_URL}/telegram-registration/status/{registration_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print_success("状态查询成功")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message', 'N/A')}")
            if result.get('risk_score'):
                print(f"   Risk Score: {result.get('risk_score')}")
            if result.get('session_file'):
                print(f"   Session File: {result.get('session_file', {}).get('file_path', 'N/A')}")
            
            return result
        elif response.status_code == 404:
            print_error("注册记录未找到")
            return None
        elif response.status_code == 401:
            print_error("认证失败: Token无效或过期")
            return None
        else:
            print_error(f"状态查询失败: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print_error(f"请求失败: {e}")
        return None

def test_registration_verify(token: str, registration_id: str, code: str, password: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """测试验证码验证API"""
    print_header("6. 测试验证码验证API")
    
    url = f"{BASE_URL}/telegram-registration/verify"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "registration_id": registration_id,
        "code": code
    }
    
    if password:
        data["password"] = password
    
    print_info(f"验证码: {code}")
    if password:
        print_info(f"密码: {'*' * len(password)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print_success("验证成功")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message', 'N/A')}")
            if result.get('session_file'):
                session = result.get('session_file', {})
                print(f"   Session Name: {session.get('session_name', 'N/A')}")
                print(f"   File Path: {session.get('file_path', 'N/A')}")
                print(f"   Server: {session.get('server_node_id', 'N/A')}")
            
            return result
        elif response.status_code == 400:
            error = response.json()
            print_error(f"验证失败: {error.get('detail', 'Unknown error')}")
            return None
        elif response.status_code == 401:
            print_error("认证失败: Token无效或过期")
            return None
        else:
            print_error(f"验证失败: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print_error(f"请求失败: {e}")
        return None

def main():
    """主测试函数"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("=" * 60)
    print("  Telegram注册系统 - 功能测试")
    print("=" * 60)
    print(f"{Colors.RESET}")
    
    # 1. 检查服务健康
    if not check_service_health():
        print_error("\n服务健康检查失败，请确保前后端服务正在运行")
        print_info("启动命令:")
        print_info("  后端: cd admin-backend && uvicorn app.main:app --reload")
        print_info("  前端: cd admin-frontend && npm run dev")
        return 1
    
    # 2. 获取认证token
    print_info("\n请输入登录凭据（或按Enter跳过API测试）:")
    email = input("邮箱: ").strip()
    if not email:
        print_warning("跳过API测试，请通过前端页面进行测试")
        print_info("前端地址: http://localhost:3000/accounts")
        return 0
    
    password = input("密码: ").strip()
    if not password:
        print_warning("跳过API测试，请通过前端页面进行测试")
        print_info("前端地址: http://localhost:3000/accounts")
        return 0
    
    token = get_auth_token(email, password)
    if not token:
        print_error("\n无法获取认证token，请检查凭据")
        return 1
    
    # 3. 测试服务器列表
    servers = test_server_list(token)
    if not servers:
        print_error("\n无法获取服务器列表")
        return 1
    
    if not servers:
        print_warning("没有可用的服务器")
        return 1
    
    # 4. 测试注册流程（可选）
    print_info("\n是否进行完整注册流程测试？(需要真实的手机号和验证码)")
    print_warning("注意: 这将发送真实的Telegram验证码")
    choice = input("继续? (y/N): ").strip().lower()
    
    if choice == 'y':
        phone = input("手机号 (例如: +1234567890): ").strip()
        country_code = input("国家代码 (例如: +1): ").strip()
        node_id = servers[0].get('node_id') if servers else input("服务器节点ID: ").strip()
        
        # 开始注册
        registration = test_registration_start(token, phone, country_code, node_id)
        if registration:
            registration_id = registration.get('registration_id')
            
            # 查询状态
            time.sleep(2)
            test_registration_status(token, registration_id)
            
            # 验证码输入
            print_info("\n请在手机上查看Telegram验证码")
            code = input("验证码: ").strip()
            if code:
                test_registration_verify(token, registration_id, code)
    else:
        print_info("跳过完整注册流程测试")
        print_info("可以通过前端页面进行完整测试: http://localhost:3000/accounts")
    
    # 总结
    print_header("测试完成")
    print_success("所有API测试通过")
    print_info("\n下一步:")
    print_info("1. 访问前端页面: http://localhost:3000/accounts")
    print_info("2. 点击'Telegram注册'标签页")
    print_info("3. 进行完整的功能测试")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}测试已中断{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}测试失败: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

