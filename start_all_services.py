#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动所有服务（后端和前端）并实时监控日志
在Cursor终端中运行，不打开外部窗口
"""
import subprocess
import sys
import time
import threading
import requests
import webbrowser
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class ServiceMonitor:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.errors = []
        
    def log(self, service, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{service}]"
        if level == "ERROR":
            print(f"{prefix} ❌ {msg}")
            self.errors.append(f"{timestamp} - {service}: {msg}")
        elif level == "SUCCESS":
            print(f"{prefix} ✅ {msg}")
        else:
            print(f"{prefix} ℹ️  {msg}")
    
    def start_backend(self):
        """启动后端服务"""
        self.log("后端", "正在启动...")
        backend_dir = Path("admin-backend")
        if not backend_dir.exists():
            self.log("后端", "admin-backend目录不存在", "ERROR")
            return False
        
        try:
            self.backend_process = subprocess.Popen(
                ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                cwd=str(backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 启动监控线程
            threading.Thread(target=self.monitor_backend, daemon=True).start()
            return True
        except Exception as e:
            self.log("后端", f"启动失败: {e}", "ERROR")
            return False
    
    def monitor_backend(self):
        """监控后端日志"""
        if not self.backend_process:
            return
        
        for line in self.backend_process.stdout:
            print(f"[后端] {line}", end='')
            
            # 检测启动成功
            if "Uvicorn running on" in line or "Application startup complete" in line:
                self.log("后端", "服务启动成功！", "SUCCESS")
            
            # 检测错误
            if any(kw in line.lower() for kw in ['error', 'exception', 'traceback']):
                if len(self.errors) < 10:  # 只记录前10个错误
                    self.log("后端", f"错误: {line.strip()[:100]}", "ERROR")
    
    def start_frontend(self):
        """启动前端服务"""
        self.log("前端", "正在启动...")
        frontend_dir = Path("admin-frontend")
        if not frontend_dir.exists():
            self.log("前端", "admin-frontend目录不存在", "ERROR")
            return False
        
        try:
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(frontend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 启动监控线程
            threading.Thread(target=self.monitor_frontend, daemon=True).start()
            return True
        except Exception as e:
            self.log("前端", f"启动失败: {e}", "ERROR")
            return False
    
    def monitor_frontend(self):
        """监控前端日志"""
        if not self.frontend_process:
            return
        
        for line in self.frontend_process.stdout:
            print(f"[前端] {line}", end='')
            
            # 检测启动成功
            if "Local:" in line or "ready" in line.lower():
                self.log("前端", "服务启动成功！", "SUCCESS")
            
            # 检测错误
            if any(kw in line.lower() for kw in ['error', 'failed', 'exception']):
                if len(self.errors) < 10:
                    self.log("前端", f"错误: {line.strip()[:100]}", "ERROR")
    
    def wait_for_services(self, timeout=120):
        """等待服务启动"""
        self.log("监控", f"等待服务启动（最多{timeout}秒）...")
        start_time = time.time()
        
        backend_ready = False
        frontend_ready = False
        
        while time.time() - start_time < timeout:
            # 检查后端
            if not backend_ready:
                try:
                    resp = requests.get(f"{BASE_URL}/health", timeout=2)
                    if resp.status_code == 200:
                        backend_ready = True
                        self.log("后端", "服务已就绪", "SUCCESS")
                except:
                    pass
            
            # 检查前端
            if not frontend_ready:
                try:
                    resp = requests.get(FRONTEND_URL, timeout=2)
                    if resp.status_code == 200:
                        frontend_ready = True
                        self.log("前端", "服务已就绪", "SUCCESS")
                except:
                    pass
            
            if backend_ready and frontend_ready:
                return True
            
            time.sleep(2)
        
        return False
    
    def open_browser(self):
        """打开浏览器进行测试"""
        test_url = f"{FRONTEND_URL}/group-ai/groups"
        self.log("浏览器", f"打开测试页面: {test_url}")
        try:
            webbrowser.open(test_url)
            self.log("浏览器", "已打开", "SUCCESS")
        except Exception as e:
            self.log("浏览器", f"打开失败: {e}", "ERROR")
            self.log("浏览器", f"请手动访问: {test_url}")
    
    def stop(self):
        """停止所有服务"""
        self.log("监控", "正在停止服务...")
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait(timeout=10)
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process.wait(timeout=10)
        self.log("监控", "所有服务已停止", "SUCCESS")
    
    def print_summary(self):
        """打印错误摘要"""
        if self.errors:
            print("\n" + "=" * 50)
            print("错误摘要")
            print("=" * 50)
            for error in self.errors[:10]:
                print(f"  - {error}")

def main():
    print("=" * 50)
    print("启动所有服务并监控")
    print("=" * 50)
    print("所有服务将在Cursor终端中运行，不打开外部窗口")
    print("")
    
    monitor = ServiceMonitor()
    
    try:
        # 启动后端
        if not monitor.start_backend():
            return 1
        
        # 启动前端
        if not monitor.start_frontend():
            return 1
        
        # 等待服务启动
        if monitor.wait_for_services():
            print("\n" + "=" * 50)
            print("所有服务已启动")
            print("=" * 50)
            
            # 打开浏览器
            time.sleep(2)
            monitor.open_browser()
            
            print("\n" + "=" * 50)
            print("测试说明")
            print("=" * 50)
            print("1. 在浏览器中登录（admin@example.com / changeme123）")
            print("2. 进入群组管理页面")
            print("3. 创建新群组")
            print("4. 添加成员到群组")
            print("5. 启动自动聊天功能")
            print("6. 在Telegram中测试自动回复")
            print("\n按Ctrl+C停止所有服务...")
            
            # 保持运行
            while True:
                time.sleep(10)
                # 定期检查服务状态
                try:
                    requests.get(f"{BASE_URL}/health", timeout=2)
                except:
                    monitor.log("后端", "服务可能已停止", "ERROR")
        else:
            monitor.log("监控", "服务启动超时", "ERROR")
            monitor.print_summary()
            return 1
            
    except KeyboardInterrupt:
        print("\n")
        monitor.log("监控", "收到停止信号", "INFO")
        monitor.stop()
        monitor.print_summary()
        return 0
    except Exception as e:
        monitor.log("监控", f"发生错误: {e}", "ERROR")
        monitor.stop()
        monitor.print_summary()
        return 1

if __name__ == "__main__":
    exit(main())

