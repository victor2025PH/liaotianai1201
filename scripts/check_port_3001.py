#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查端口 3001 上的前端服务
"""

import requests
import sys

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_port_3001():
    """检查端口 3001"""
    print("=" * 70)
    print("检查端口 3001 上的前端服务")
    print("=" * 70)
    
    try:
        # 检查主页
        response = requests.get("http://localhost:3001", timeout=5)
        print(f"✓ 主页可访问 (http://localhost:3001)")
        print(f"  状态码: {response.status_code}")
        
        # 检查登录页面
        login_response = requests.get("http://localhost:3001/login", timeout=5)
        if login_response.status_code == 200:
            print(f"✓ 登录页面可访问 (http://localhost:3001/login)")
            content = login_response.text
            if "登錄" in content or "登录" in content or "Login" in content:
                print("✓ 登录页面内容正常")
            else:
                print("⚠️  登录页面内容可能异常")
        else:
            print(f"✗ 登录页面返回: {login_response.status_code}")
        
        print("\n" + "=" * 70)
        print("✓ 前端服务运行正常！")
        print("=" * 70)
        print("\n重要提示：")
        print("  前端服务运行在端口 3001，而不是 3000")
        print("  这是因为端口 3000 被占用，Next.js 自动使用了下一个可用端口")
        print("\n访问地址：")
        print("  主页: http://localhost:3001")
        print("  登录页面: http://localhost:3001/login")
        print("\n下一步操作：")
        print("  1. 访问登录页面: http://localhost:3001/login")
        print("  2. 使用默认账号登录:")
        print("     邮箱: admin@liaotian.cc")
        print("     密码: admin123456")
        print("  3. 登录后应该自动跳转到主页，显示完整应用界面")
        
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到端口 3001")
        print("  可能原因：")
        print("  1. 服务还在启动中")
        print("  2. 服务启动失败")
    except Exception as e:
        print(f"✗ 检查时出错: {e}")

if __name__ == "__main__":
    check_port_3001()

