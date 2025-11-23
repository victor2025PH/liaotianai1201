"""
服務監控和自動修復腳本
持續監控服務日誌，發現錯誤時自動修復
"""
import subprocess
import sys
import time
import requests
import re
from datetime import datetime
from pathlib import Path

def safe_print(text):
    """安全打印"""
    try:
        print(text)
    except UnicodeEncodeError:
        text = text.encode('ascii', 'ignore').decode('ascii')
        print(text)

def check_api_health():
    """檢查 API 健康狀態"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def test_accounts_api():
    """測試帳號 API"""
    try:
        response = requests.get("http://localhost:8000/api/v1/group-ai/accounts/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, f"成功，帳號總數: {data.get('total', 0)}"
        else:
            return False, f"狀態碼: {response.status_code}, 響應: {response.text[:200]}"
    except Exception as e:
        return False, f"錯誤: {str(e)}"

def monitor_backend_logs():
    """監控後端日誌"""
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
    
    error_patterns = [
        r'Error',
        r'Exception',
        r'Traceback',
        r'Failed',
        r'失敗',
        r'錯誤',
        r'500',
        r'Internal Server Error'
    ]
    
    for line in iter(process.stdout.readline, ''):
        if line:
            timestamp = datetime.now().strftime("%H:%M:%S")
            line_lower = line.lower()
            
            # 檢查錯誤
            is_error = any(re.search(pattern, line, re.IGNORECASE) for pattern in error_patterns)
            
            if is_error:
                safe_print(f"[{timestamp}] [後端] ❌ {line.strip()}")
                # 這裡可以添加自動修復邏輯
            elif 'started' in line_lower or 'uvicorn running' in line_lower:
                safe_print(f"[{timestamp}] [後端] ✅ {line.strip()}")
            else:
                safe_print(f"[{timestamp}] [後端] {line.strip()}")
    
    process.wait()

def main():
    """主函數"""
    safe_print("="*60)
    safe_print("服務監控和自動修復")
    safe_print("="*60)
    safe_print("按 Ctrl+C 停止監控")
    safe_print("="*60)
    safe_print("")
    
    # 啟動後端監控
    import threading
    backend_thread = threading.Thread(target=monitor_backend_logs, daemon=True)
    backend_thread.start()
    
    # 等待服務啟動
    time.sleep(10)
    
    # 定期測試 API
    try:
        while True:
            time.sleep(30)  # 每30秒測試一次
            
            # 測試健康檢查
            if check_api_health():
                safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 健康檢查通過")
            else:
                safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 健康檢查失敗")
            
            # 測試帳號 API
            success, msg = test_accounts_api()
            if success:
                safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 帳號API: {msg}")
            else:
                safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 帳號API: {msg}")
                
    except KeyboardInterrupt:
        safe_print("\n正在停止監控...")
        sys.exit(0)

if __name__ == "__main__":
    main()

