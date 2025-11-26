#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并修复前端服务连接问题
"""

import requests
import sys
import time
import subprocess
from pathlib import Path

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
frontend_dir = project_root / "saas-demo"

def check_backend():
    """检查后端服务"""
    try:
        response = requests.get("http://localhost:8000", timeout=3)
        if response.status_code == 200:
            print("✓ 后端服务运行正常 (http://localhost:8000)")
            return True
    except:
        pass
    return False

def check_frontend(port=3001):
    """检查前端服务"""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=3)
        if response.status_code == 200:
            print(f"✓ 前端服务运行正常 (http://localhost:{port})")
            return True
    except:
        pass
    return False

def start_frontend():
    """启动前端服务"""
    print("\n" + "=" * 70)
    print("启动前端服务...")
    print("=" * 70)
    
    os.chdir(frontend_dir)
    
    cmd = ["npm", "run", "dev"]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace',
            shell=sys.platform == 'win32',
            cwd=str(frontend_dir)
        )
        
        print(f"  [OK] 前端服务已启动 (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"  [ERROR] 启动失败: {e}")
        return None

def main():
    print("=" * 70)
    print("检查并修复前端服务连接问题")
    print("=" * 70)
    
    # 检查后端
    print("\n检查后端服务...")
    if not check_backend():
        print("✗ 后端服务不可访问")
        print("  请先启动后端服务")
        return
    
    # 检查前端（尝试多个端口）
    print("\n检查前端服务...")
    frontend_ok = False
    for port in [3001, 3000, 3002]:
        if check_frontend(port):
            frontend_ok = True
            print(f"\n✓ 前端服务在端口 {port} 上运行")
            print(f"  访问地址: http://localhost:{port}")
            print(f"  登录页面: http://localhost:{port}/login")
            break
    
    if not frontend_ok:
        print("✗ 前端服务不可访问")
        print("\n正在启动前端服务...")
        process = start_frontend()
        
        if process:
            print("\n等待服务启动（15秒）...")
            time.sleep(15)
            
            # 再次检查
            for port in [3001, 3000, 3002]:
                if check_frontend(port):
                    print(f"\n✓ 前端服务已成功启动在端口 {port}")
                    print(f"  访问地址: http://localhost:{port}")
                    print(f"  登录页面: http://localhost:{port}/login")
                    break
            else:
                print("\n⚠️  前端服务可能还在启动中，请稍等片刻后再次访问")
                print("  或者查看控制台输出了解启动状态")
        else:
            print("\n✗ 无法启动前端服务")
            print("  请手动运行: cd saas-demo && npm run dev")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    import os
    main()

