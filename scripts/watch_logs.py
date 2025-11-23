"""
日誌監控腳本 - 實時監控系統日誌和服務狀態
"""
import time
import requests
from datetime import datetime
import sys

def check_service(url, name, timeout=2):
    """檢查服務狀態"""
    try:
        response = requests.get(url, timeout=timeout)
        return True, response.status_code
    except requests.exceptions.RequestException as e:
        return False, str(e)

def format_time():
    """格式化時間"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    """主函數"""
    backend_url = "http://localhost:8000/health"
    frontend_url = "http://localhost:3000"
    
    print("="*70)
    print("系統服務監控 - 按 Ctrl+C 停止")
    print("="*70)
    print(f"開始時間: {format_time()}")
    print(f"後端服務: {backend_url}")
    print(f"前端服務: {frontend_url}")
    print("="*70)
    print()
    
    check_count = 0
    backend_ok_count = 0
    frontend_ok_count = 0
    
    try:
        while True:
            check_count += 1
            timestamp = format_time()
            
            # 檢查後端
            backend_ok, backend_status = check_service(backend_url, "後端")
            if backend_ok:
                backend_ok_count += 1
                status_str = f"[OK] 後端正常 (狀態碼: {backend_status})"
            else:
                status_str = f"[ERROR] 後端異常: {backend_status}"
            
            # 檢查前端
            frontend_ok, frontend_status = check_service(frontend_url, "前端")
            if frontend_ok:
                frontend_ok_count += 1
                status_str += f" | [OK] 前端正常 (狀態碼: {frontend_status})"
            else:
                status_str += f" | [ERROR] 前端異常: {frontend_status}"
            
            # 計算成功率
            backend_rate = (backend_ok_count / check_count) * 100 if check_count > 0 else 0
            frontend_rate = (frontend_ok_count / check_count) * 100 if check_count > 0 else 0
            
            # 顯示狀態
            print(f"[{timestamp}] 檢查 #{check_count}")
            print(f"  {status_str}")
            print(f"  後端成功率: {backend_rate:.1f}% ({backend_ok_count}/{check_count})")
            print(f"  前端成功率: {frontend_rate:.1f}% ({frontend_ok_count}/{check_count})")
            print()
            
            time.sleep(10)  # 每10秒檢查一次
    
    except KeyboardInterrupt:
        print()
        print("="*70)
        print("監控已停止")
        print("="*70)
        print(f"總檢查次數: {check_count}")
        print(f"後端成功: {backend_ok_count} 次 ({backend_rate:.1f}%)")
        print(f"前端成功: {frontend_ok_count} 次 ({frontend_rate:.1f}%)")
        print(f"結束時間: {format_time()}")
        print("="*70)

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("需要安裝 requests 庫: pip install requests")
        sys.exit(1)
    
    main()

