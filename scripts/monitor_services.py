"""
服務監控腳本 - 監控後端和前端服務的運行狀態和日誌
"""
import subprocess
import sys
import time
import threading
import requests
from pathlib import Path
from datetime import datetime

def safe_print(text):
    """安全打印"""
    try:
        print(text)
    except UnicodeEncodeError:
        text = text.encode('ascii', 'ignore').decode('ascii')
        print(text)

def check_service(port, name):
    """檢查服務是否運行"""
    try:
        response = requests.get(f"http://localhost:{port}/health" if port == 8000 else f"http://localhost:{port}", timeout=2)
        return response.status_code in [200, 404]  # 404 也算服務運行（只是路徑不存在）
    except:
        return False

def monitor_backend():
    """監控後端服務"""
    backend_dir = Path(__file__).parent.parent / "admin-backend"
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    safe_print(f"[後端] 服務啟動中 (PID: {process.pid})...")
    
    # 實時輸出日誌
    for line in iter(process.stdout.readline, ''):
        if line:
            timestamp = datetime.now().strftime("%H:%M:%S")
            # 檢查錯誤關鍵詞
            if any(keyword in line.lower() for keyword in ['error', 'exception', 'traceback', 'failed', '失敗']):
                safe_print(f"[{timestamp}] [後端] ❌ {line.strip()}")
            elif 'started' in line.lower() or 'uvicorn running' in line.lower():
                safe_print(f"[{timestamp}] [後端] ✅ {line.strip()}")
            else:
                safe_print(f"[{timestamp}] [後端] {line.strip()}")
    
    process.wait()

def monitor_frontend():
    """監控前端服務"""
    frontend_dir = Path(__file__).parent.parent / "saas-demo"
    
    # 查找 npm
    import shutil
    npm_path = shutil.which("npm")
    if not npm_path:
        safe_print("[前端] ❌ 未找到 npm")
        return
    
    process = subprocess.Popen(
        [npm_path, "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=(sys.platform == 'win32')
    )
    
    safe_print(f"[前端] 服務啟動中 (PID: {process.pid})...")
    
    # 實時輸出日誌
    for line in iter(process.stdout.readline, ''):
        if line:
            timestamp = datetime.now().strftime("%H:%M:%S")
            # 檢查錯誤關鍵詞
            if any(keyword in line.lower() for keyword in ['error', 'failed', '失敗', 'cannot', 'missing']):
                safe_print(f"[{timestamp}] [前端] ❌ {line.strip()}")
            elif 'ready' in line.lower() or 'compiled' in line.lower():
                safe_print(f"[{timestamp}] [前端] ✅ {line.strip()}")
            else:
                safe_print(f"[{timestamp}] [前端] {line.strip()}")
    
    process.wait()

def main():
    """主函數"""
    safe_print("="*60)
    safe_print("服務監控腳本")
    safe_print("="*60)
    safe_print("按 Ctrl+C 停止服務")
    safe_print("="*60)
    safe_print("")
    
    # 啟動後端監控（在單獨線程中）
    backend_thread = threading.Thread(target=monitor_backend, daemon=True)
    backend_thread.start()
    
    # 等待後端啟動
    time.sleep(3)
    
    # 啟動前端監控（在單獨線程中）
    frontend_thread = threading.Thread(target=monitor_frontend, daemon=True)
    frontend_thread.start()
    
    # 等待服務啟動
    time.sleep(5)
    
    # 定期檢查服務狀態
    try:
        while True:
            time.sleep(10)
            backend_ok = check_service(8000, "後端")
            frontend_ok = check_service(3000, "前端")
            
            status = []
            if backend_ok:
                status.append("✅ 後端")
            else:
                status.append("❌ 後端")
            
            if frontend_ok:
                status.append("✅ 前端")
            else:
                status.append("❌ 前端")
            
            safe_print(f"[狀態] {', '.join(status)}")
            
    except KeyboardInterrupt:
        safe_print("\n正在停止服務...")
        sys.exit(0)

if __name__ == "__main__":
    main()

