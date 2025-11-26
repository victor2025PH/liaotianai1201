#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重启前端服务并清除 Next.js 路由缓存
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path
import shutil

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
frontend_dir = project_root / "saas-demo"
next_cache_dir = frontend_dir / ".next"

def kill_frontend_processes():
    """终止前端进程"""
    print("=" * 70)
    print("终止前端进程...")
    print("=" * 70)
    
    try:
        if sys.platform == 'win32':
            # Windows: 查找并终止 node.exe 进程（Next.js）
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq node.exe", "/FO", "CSV"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "node.exe" in result.stdout:
                print("  发现 node.exe 进程，正在终止...")
                subprocess.run(
                    ["taskkill", "/F", "/IM", "node.exe"],
                    capture_output=True,
                    timeout=10
                )
                print("  [OK] 前端进程已终止")
            else:
                print("  [INFO] 未发现运行中的前端进程")
        else:
            # Linux/Mac: 使用 pkill
            subprocess.run(["pkill", "-f", "next"], timeout=5)
            print("  [OK] 前端进程已终止")
    except subprocess.TimeoutExpired:
        print("  [WARNING] 终止进程超时")
    except Exception as e:
        print(f"  [WARNING] 终止进程时出错: {e}")
    
    time.sleep(2)

def clear_next_cache():
    """清除 Next.js 缓存"""
    print("\n" + "=" * 70)
    print("清除 Next.js 缓存...")
    print("=" * 70)
    
    if next_cache_dir.exists():
        try:
            print(f"  删除缓存目录: {next_cache_dir}")
            shutil.rmtree(next_cache_dir)
            print("  [OK] 缓存已清除")
        except Exception as e:
            print(f"  [ERROR] 清除缓存失败: {e}")
            return False
    else:
        print("  [INFO] 缓存目录不存在，无需清除")
    
    return True

def start_frontend():
    """启动前端服务"""
    print("\n" + "=" * 70)
    print("启动前端服务...")
    print("=" * 70)
    
    os.chdir(frontend_dir)
    
    # 检查 node_modules
    if not (frontend_dir / "node_modules").exists():
        print("[WARNING] node_modules 不存在，正在安装依赖...")
        try:
            subprocess.run(["npm", "install"], check=True, cwd=frontend_dir, timeout=300)
        except Exception as e:
            print(f"[ERROR] 安装依赖失败: {e}")
            return None
    
    # 检查 .env.local
    env_file = frontend_dir / ".env.local"
    if not env_file.exists():
        print("[WARNING] .env.local 不存在，正在创建...")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("NEXT_PUBLIC_API_BASE_URL=http://localhost:8000\n")
        print("  [OK] .env.local 已创建")
    
    # 启动命令
    cmd = ["npm", "run", "dev"]
    
    log_file = frontend_dir / "frontend_restart.log"
    
    try:
        print(f"  启动命令: {' '.join(cmd)}")
        print(f"  工作目录: {frontend_dir}")
        print(f"  日志文件: {log_file}")
        
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
        
        print(f"\n  [OK] 前端服务已启动 (PID: {process.pid})")
        print(f"      前端地址: http://localhost:3000")
        print(f"      登录页面: http://localhost:3000/login")
        print(f"\n  等待服务启动...")
        
        # 等待服务启动
        time.sleep(10)
        
        # 检查服务是否运行
        if process.poll() is None:
            print("  [OK] 前端服务正在运行")
        else:
            print(f"  [ERROR] 前端服务已退出 (退出码: {process.returncode})")
            # 读取错误输出
            try:
                output, _ = process.communicate(timeout=1)
                if output:
                    print("  错误输出:")
                    for line in output.split('\n')[-10:]:
                        if line.strip():
                            print(f"    {line}")
            except:
                pass
            return None
        
        return process
    except Exception as e:
        print(f"[ERROR] 启动前端服务失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_frontend():
    """检查前端服务"""
    print("\n" + "=" * 70)
    print("检查前端服务...")
    print("=" * 70)
    
    import requests
    
    # 检查主页
    for i in range(10):
        try:
            response = requests.get("http://localhost:3000", timeout=3)
            if response.status_code == 200:
                print("  ✓ 主页可访问 (http://localhost:3000)")
                break
        except:
            if i < 9:
                time.sleep(1)
            else:
                print("  ✗ 主页不可访问")
                return False
    
    # 检查登录页面
    for i in range(10):
        try:
            response = requests.get("http://localhost:3000/login", timeout=3)
            if response.status_code == 200:
                print("  ✓ 登录页面可访问 (http://localhost:3000/login)")
                if "登錄" in response.text or "登录" in response.text or "Login" in response.text:
                    print("  ✓ 登录页面内容正常")
                return True
            elif response.status_code == 404:
                print("  ✗ 登录页面返回404")
                return False
        except:
            if i < 9:
                time.sleep(1)
            else:
                print("  ✗ 登录页面不可访问")
                return False
    
    return False

def main():
    print("=" * 70)
    print("重启前端服务并清除 Next.js 路由缓存")
    print("=" * 70)
    print(f"项目根目录: {project_root}")
    print(f"前端目录: {frontend_dir}")
    print()
    
    # 步骤1: 终止现有进程
    kill_frontend_processes()
    
    # 步骤2: 清除缓存
    if not clear_next_cache():
        print("\n[ERROR] 清除缓存失败，继续尝试启动服务...")
    
    # 步骤3: 启动服务
    process = start_frontend()
    
    if process:
        # 步骤4: 检查服务
        if check_frontend():
            print("\n" + "=" * 70)
            print("✓ 前端服务重启成功！")
            print("=" * 70)
            print("\n下一步操作：")
            print("  1. 访问登录页面: http://localhost:3000/login")
            print("  2. 使用默认账号登录:")
            print("     邮箱: admin@liaotian.cc")
            print("     密码: admin123456")
            print("  3. 登录后应该自动跳转到主页，显示完整应用界面")
            print("\n按 Ctrl+C 停止服务\n")
            
            try:
                while True:
                    time.sleep(1)
                    if process.poll() is not None:
                        print(f"\n[WARNING] 前端服务已退出 (退出码: {process.returncode})")
                        break
            except KeyboardInterrupt:
                print("\n\n正在停止服务...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                print("服务已停止")
        else:
            print("\n" + "=" * 70)
            print("⚠️  前端服务已启动，但登录页面可能仍有问题")
            print("=" * 70)
            print("\n建议：")
            print("  1. 检查浏览器控制台是否有错误")
            print("  2. 等待几秒钟后再次访问 http://localhost:3000/login")
            print("  3. 如果仍然404，检查 Next.js 路由配置")
    else:
        print("\n" + "=" * 70)
        print("✗ 前端服务启动失败")
        print("=" * 70)
        print("\n请检查：")
        print("  1. node_modules 是否已安装")
        print("  2. 端口 3000 是否被占用")
        print("  3. 查看前端日志文件了解详细错误")

if __name__ == "__main__":
    main()

