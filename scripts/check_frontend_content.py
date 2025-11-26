#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查前端页面内容，分析为什么没有显示应用界面
"""

import requests
import sys
from pathlib import Path

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_frontend():
    """检查前端页面内容"""
    print("=" * 70)
    print("检查前端页面内容")
    print("=" * 70)
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)} 字符")
        
        content = response.text
        
        # 检查关键内容
        checks = {
            "總覽儀表板": "包含仪表板标题",
            "Dashboard": "包含Dashboard（英文）",
            "layout-wrapper": "包含LayoutWrapper组件",
            "前端服務運行正常": "显示简单状态页面",
            "檢查認證狀態": "正在检查认证状态",
            "/login": "包含登录页面链接",
            "Sidebar": "包含侧边栏组件",
            "Header": "包含头部组件",
            "next.js": "Next.js框架",
            "react": "React框架",
        }
        
        print("\n页面内容检查:")
        found_items = []
        for keyword, desc in checks.items():
            if keyword.lower() in content.lower():
                print(f"  ✓ {desc} ({keyword})")
                found_items.append(keyword)
            else:
                print(f"  ✗ {desc} ({keyword})")
        
        # 分析问题
        print("\n" + "=" * 70)
        print("问题分析")
        print("=" * 70)
        
        if "前端服務運行正常" in content:
            print("⚠️  问题：前端显示简单状态页面，而不是应用界面")
            print("\n可能原因：")
            print("  1. 认证检查中 - LayoutWrapper 正在检查认证状态")
            print("  2. 未认证 - 需要登录才能看到应用界面")
            print("  3. 前端路由问题 - 可能访问了错误的路由")
            print("\n解决方案：")
            print("  1. 检查浏览器控制台是否有错误")
            print("  2. 尝试访问 http://localhost:3000/login 进行登录")
            print("  3. 检查 localStorage 中是否有 access_token")
        elif "檢查認證狀態" in content:
            print("⚠️  问题：前端正在检查认证状态")
            print("\n说明：")
            print("  - LayoutWrapper 组件正在验证用户是否已登录")
            print("  - 如果未登录，会自动重定向到 /login")
            print("  - 如果已登录，会显示完整的应用界面")
        elif "總覽儀表板" in content or "Dashboard" in content:
            print("✓ 前端应用界面正常显示")
        else:
            print("⚠️  无法确定页面状态，需要进一步检查")
            print("\n建议：")
            print("  1. 打开浏览器开发者工具（F12）")
            print("  2. 查看 Console 标签页的错误信息")
            print("  3. 查看 Network 标签页的请求状态")
        
        # 检查API连接
        print("\n" + "=" * 70)
        print("检查API连接")
        print("=" * 70)
        
        try:
            api_response = requests.get("http://localhost:8000/health", timeout=5)
            if api_response.status_code == 200:
                print("✓ 后端API可访问")
            else:
                print(f"⚠️  后端API响应异常: {api_response.status_code}")
        except Exception as e:
            print(f"✗ 后端API不可访问: {e}")
        
        # 检查登录端点
        try:
            login_response = requests.get("http://localhost:3000/login", timeout=5)
            if login_response.status_code == 200:
                print("✓ 登录页面可访问")
            else:
                print(f"⚠️  登录页面响应异常: {login_response.status_code}")
        except Exception as e:
            print(f"✗ 登录页面不可访问: {e}")
        
        # 输出部分HTML内容用于调试
        print("\n" + "=" * 70)
        print("页面HTML片段（前500字符）")
        print("=" * 70)
        print(content[:500])
        print("...")
        
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到前端服务 (http://localhost:3000)")
        print("  可能原因：")
        print("  1. 前端服务未启动")
        print("  2. 端口被占用")
        print("  3. 服务启动失败")
    except Exception as e:
        print(f"✗ 检查前端时出错: {e}")

if __name__ == "__main__":
    check_frontend()

