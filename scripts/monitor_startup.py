"""
啟動監控腳本 - 監控系統啟動過程和日誌
"""
import subprocess
import sys
import time
import requests
from pathlib import Path
from threading import Thread
import queue

def check_service(url, name, timeout=2):
    """檢查服務是否可用"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200, response.status_code
    except requests.exceptions.RequestException:
        return False, None

def monitor_services():
    """監控服務狀態"""
    backend_url = "http://localhost:8000/health"
    frontend_url = "http://localhost:3000"
    
    print("\n" + "="*60)
    print("開始監控服務狀態...")
    print("="*60)
    
    backend_ready = False
    frontend_ready = False
    
    for i in range(60):  # 最多監控60秒
        time.sleep(2)
        
        # 檢查後端
        if not backend_ready:
            is_ready, status = check_service(backend_url, "後端")
            if is_ready:
                print(f"✅ [{time.strftime('%H:%M:%S')}] 後端服務已啟動 (狀態碼: {status})")
                backend_ready = True
        
        # 檢查前端
        if not frontend_ready:
            is_ready, status = check_service(frontend_url, "前端")
            if is_ready:
                print(f"✅ [{time.strftime('%H:%M:%S')}] 前端服務已啟動 (狀態碼: {status})")
                frontend_ready = True
        
        # 如果兩個服務都啟動了，退出監控
        if backend_ready and frontend_ready:
            print("\n" + "="*60)
            print("✅ 所有服務已成功啟動！")
            print("="*60)
            print(f"\n後端 API: {backend_url}")
            print(f"前端界面: {frontend_url}")
            print(f"API 文檔: http://localhost:8000/docs")
            return True
        
        # 顯示進度
        if i % 5 == 0 and i > 0:
            status = []
            if backend_ready:
                status.append("後端✅")
            else:
                status.append("後端⏳")
            if frontend_ready:
                status.append("前端✅")
            else:
                status.append("前端⏳")
            print(f"[{time.strftime('%H:%M:%S')}] 等待服務啟動... {' | '.join(status)}")
    
    print("\n⚠️  監控超時，部分服務可能尚未啟動")
    return False

def read_process_output(process, output_queue, name):
    """讀取進程輸出"""
    try:
        for line in iter(process.stdout.readline, b''):
            if line:
                output_queue.put((name, line.decode('utf-8', errors='ignore').strip()))
    except Exception as e:
        output_queue.put((name, f"讀取錯誤: {e}"))

def main():
    """主函數"""
    print("="*60)
    print("Telegram 群組 AI 系統啟動監控")
    print("="*60)
    
    # 啟動系統
    print("\n正在啟動系統...")
    process = subprocess.Popen(
        [sys.executable, "scripts/start_system.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
        cwd=Path(__file__).parent.parent
    )
    
    # 啟動監控線程
    output_queue = queue.Queue()
    monitor_thread = Thread(target=monitor_services, daemon=True)
    monitor_thread.start()
    
    # 讀取輸出
    print("\n啟動日誌:")
    print("-" * 60)
    
    try:
        while True:
            # 檢查進程是否還在運行
            if process.poll() is not None:
                print("\n⚠️  啟動進程已結束")
                break
            
            # 讀取輸出
            try:
                line = process.stdout.readline()
                if line:
                    print(line.rstrip())
            except Exception:
                break
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n正在停止監控...")
        process.terminate()
    
    finally:
        if process.poll() is None:
            process.terminate()
        print("\n監控已停止")

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("需要安裝 requests 庫: pip install requests")
        sys.exit(1)
    
    main()

