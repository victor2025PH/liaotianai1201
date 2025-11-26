#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动本地前端和后端服务
监控日志并识别错误
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path
import threading
import queue

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 项目根目录
project_root = Path(__file__).parent.parent
backend_dir = project_root / "admin-backend"
frontend_dir = project_root / "saas-demo"

# 进程列表
processes = []
log_queue = queue.Queue()
errors = []

def log_monitor(process_name, pipe, log_file):
    """监控进程输出"""
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            for line in iter(pipe.readline, ''):
                if not line:
                    break
                line = line.rstrip()
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{timestamp}][{process_name}] {line}\n"
                print(log_entry, end='')
                f.write(log_entry)
                f.flush()
                
                # 检测错误
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ['error', 'exception', 'failed', 'traceback', 'cannot', 'module']):
                    errors.append({
                        'time': timestamp,
                        'service': process_name,
                        'error': line
                    })
                    log_queue.put(('error', process_name, line))
    except Exception as e:
        print(f"[ERROR] 日志监控失败 ({process_name}): {e}")

def start_backend():
    """启动后端服务"""
    print("=" * 70)
    print("启动后端服务...")
    print("=" * 70)
    
    os.chdir(backend_dir)
    
    # 检查虚拟环境
    venv_python = backend_dir / ".venv" / "Scripts" / "python.exe" if sys.platform == 'win32' else backend_dir / ".venv" / "bin" / "python3"
    
    if not venv_python.exists():
        print("[ERROR] 虚拟环境不存在，请先创建:")
        print(f"  cd {backend_dir}")
        print("  python -m venv .venv")
        print("  .venv\\Scripts\\activate  # Windows")
        print("  pip install -r requirements.txt")
        return None
    
    # 启动命令
    cmd = [
        str(venv_python),
        "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    log_file = backend_dir / "backend_local.log"
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # 启动日志监控线程
        monitor_thread = threading.Thread(
            target=log_monitor,
            args=("BACKEND", process.stdout, log_file),
            daemon=True
        )
        monitor_thread.start()
        
        print(f"[OK] 后端服务已启动 (PID: {process.pid})")
        print(f"     日志文件: {log_file}")
        print(f"     API 地址: http://localhost:8000")
        print(f"     API 文档: http://localhost:8000/docs")
        
        return process
    except Exception as e:
        print(f"[ERROR] 启动后端服务失败: {e}")
        return None

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
            subprocess.run(["npm", "install"], check=True, cwd=frontend_dir)
        except Exception as e:
            print(f"[ERROR] 安装依赖失败: {e}")
            return None
    
    # 检查 .env.local
    env_file = frontend_dir / ".env.local"
    if not env_file.exists():
        print("[WARNING] .env.local 不存在，正在创建...")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("NEXT_PUBLIC_API_BASE_URL=http://localhost:8000\n")
    
    # 启动命令
    cmd = ["npm", "run", "dev"]
    
    log_file = frontend_dir / "frontend_local.log"
    
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
            shell=sys.platform == 'win32'
        )
        
        # 启动日志监控线程
        monitor_thread = threading.Thread(
            target=log_monitor,
            args=("FRONTEND", process.stdout, log_file),
            daemon=True
        )
        monitor_thread.start()
        
        print(f"[OK] 前端服务已启动 (PID: {process.pid})")
        print(f"     日志文件: {log_file}")
        print(f"     前端地址: http://localhost:3000")
        
        return process
    except Exception as e:
        print(f"[ERROR] 启动前端服务失败: {e}")
        return None

def check_services():
    """检查服务状态"""
    import requests
    
    print("\n" + "=" * 70)
    print("检查服务状态...")
    print("=" * 70)
    
    # 检查后端
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("[OK] 后端服务运行正常")
        else:
            print(f"[WARNING] 后端服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] 后端服务不可访问: {e}")
    
    # 检查前端
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("[OK] 前端服务运行正常")
        else:
            print(f"[WARNING] 前端服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] 前端服务不可访问: {e}")

def signal_handler(sig, frame):
    """处理退出信号"""
    print("\n\n" + "=" * 70)
    print("正在停止服务...")
    print("=" * 70)
    
    for process in processes:
        if process and process.poll() is None:
            print(f"停止进程 (PID: {process.pid})...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    # 输出错误摘要
    if errors:
        print("\n" + "=" * 70)
        print("错误摘要")
        print("=" * 70)
        for error in errors[-10:]:  # 只显示最后10个错误
            print(f"[{error['time']}] [{error['service']}] {error['error']}")
    
    sys.exit(0)

def main():
    """主函数"""
    print("=" * 70)
    print("本地服务启动脚本")
    print("=" * 70)
    print(f"项目根目录: {project_root}")
    print(f"后端目录: {backend_dir}")
    print(f"前端目录: {frontend_dir}")
    print("\n按 Ctrl+C 停止所有服务\n")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动后端
    backend_process = start_backend()
    if backend_process:
        processes.append(backend_process)
        time.sleep(3)  # 等待后端启动
    
    # 启动前端
    frontend_process = start_frontend()
    if frontend_process:
        processes.append(frontend_process)
        time.sleep(5)  # 等待前端启动
    
    # 检查服务
    time.sleep(2)
    check_services()
    
    print("\n" + "=" * 70)
    print("服务运行中...")
    print("=" * 70)
    print("后端: http://localhost:8000")
    print("前端: http://localhost:3000")
    print("\n按 Ctrl+C 停止所有服务\n")
    
    # 定期检查服务状态和错误
    try:
        while True:
            time.sleep(10)
            
            # 检查进程是否还在运行
            for i, process in enumerate(processes):
                if process and process.poll() is not None:
                    service_name = "后端" if i == 0 else "前端"
                    print(f"\n[WARNING] {service_name}服务已退出 (退出码: {process.returncode})")
            
            # 检查是否有新错误
            try:
                while True:
                    msg_type, service, msg = log_queue.get_nowait()
                    if msg_type == 'error':
                        print(f"\n[ERROR] [{service}] {msg}")
            except queue.Empty:
                pass
            
            # 定期检查服务健康状态
            check_services()
            
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()

