"""
系統啟動腳本 - 一鍵啟動所有服務
"""
import subprocess
import sys
import os
import time
import threading
from pathlib import Path

# 設置 Windows 控制台編碼為 UTF-8
if sys.platform == 'win32':
    try:
        # 嘗試設置控制台編碼為 UTF-8
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        # 如果失敗，使用 ASCII 安全字符
        pass

def safe_print(text):
    """安全打印，處理編碼問題"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 如果無法打印 Unicode 字符，使用 ASCII 替代
        text = text.replace('✅', '[OK]').replace('❌', '[ERROR]').replace('⚠️', '[WARN]')
        print(text)

def check_dependencies():
    """檢查依賴"""
    safe_print("檢查依賴...")
    
    # 檢查 Python
    if sys.version_info < (3, 9):
        safe_print("[ERROR] Python 版本需要 3.9+")
        return False
    
    # 檢查 Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            safe_print("[ERROR] Node.js 未安裝")
            return False
    except FileNotFoundError:
        safe_print("[ERROR] Node.js 未安裝")
        return False
    
    safe_print("[OK] 依賴檢查通過")
    return True


def start_backend():
    """啟動後端服務"""
    print("\n啟動後端服務...")
    backend_dir = Path(__file__).parent.parent / "admin-backend"
    
    if not backend_dir.exists():
        safe_print("[ERROR] 後端目錄不存在")
        return None
    
    # 檢查環境變量
    env_file = backend_dir / ".env"
    env_example = backend_dir / ".env.example"
    if not env_file.exists():
        safe_print("[WARN] 未找到 .env 文件")
        if env_example.exists():
            safe_print("   提示: 可以複製 .env.example 到 .env 並修改配置")
            safe_print(f"   命令: copy {env_example} {env_file}")
        else:
            safe_print("   提示: 系統將使用默認配置，建議創建 .env 文件進行自定義配置")
    
    # 啟動 uvicorn
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False
    )
    
    safe_print("[OK] 後端服務啟動中... (PID: {})".format(process.pid))
    return process


def find_npm():
    """查找 npm 可執行文件路徑"""
    import shutil
    # 首先嘗試直接使用 shutil.which（跨平台）
    npm_path = shutil.which("npm")
    if npm_path:
        return npm_path
    
    # Windows 上嘗試使用 where 命令
    if os.name == 'nt':
        try:
            result = subprocess.run(
                ["where", "npm"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
    
    return None


def start_frontend():
    """啟動前端服務"""
    print("\n啟動前端服務...")
    frontend_dir = Path(__file__).parent.parent / "saas-demo"
    
    if not frontend_dir.exists():
        safe_print("[ERROR] 前端目錄不存在")
        return None
    
    # 查找 npm
    npm_path = find_npm()
    if not npm_path:
        safe_print("[ERROR] npm 未找到，請確保 Node.js 已安裝並在 PATH 中")
        safe_print("   提示: 可以從 https://nodejs.org/ 下載安裝 Node.js")
        return None
    
    safe_print(f"   找到 npm: {npm_path}")
    
    # 檢查 npm 是否可用
    try:
        result = subprocess.run(
            [npm_path, "--version"],
            capture_output=True,
            text=True,
            shell=(os.name == 'nt')
        )
        if result.returncode != 0:
            safe_print("[ERROR] npm 版本檢查失敗")
            return None
        safe_print(f"   npm 版本: {result.stdout.strip()}")
    except Exception as e:
        safe_print(f"[ERROR] npm 檢查失敗: {e}")
        return None
    
    # 檢查 node_modules
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        safe_print("[WARN] 未找到 node_modules，正在安裝依賴...")
        try:
            subprocess.run(
                [npm_path, "install"],
                cwd=frontend_dir,
                shell=(os.name == 'nt'),
                check=True
            )
            safe_print("[OK] 依賴安裝完成")
        except subprocess.CalledProcessError as e:
            safe_print(f"[ERROR] 依賴安裝失敗: {e}")
            return None
    
    # 啟動 Next.js
    # 在 Windows 上使用 shell=True 並使用完整命令字符串
    if os.name == 'nt':
        # Windows: 使用 cmd /c 來執行 npm 命令
        cmd = f'"{npm_path}" run dev'
        process = subprocess.Popen(
            cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
    else:
        # Linux/Mac: 直接使用路徑
        process = subprocess.Popen(
            [npm_path, "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )
    
    safe_print("[OK] 前端服務啟動中... (PID: {})".format(process.pid))
    return process


def main():
    """主函數"""
    print("="*60)
    print("Telegram 群組 AI 系統啟動腳本")
    print("="*60)
    
    # 檢查依賴
    if not check_dependencies():
        safe_print("\n[ERROR] 依賴檢查失敗，請先安裝必要的依賴")
        sys.exit(1)
    
    # 啟動服務
    backend_process = None
    frontend_process = None
    
    try:
        # 啟動後端
        backend_process = start_backend()
        if backend_process:
            time.sleep(3)  # 等待後端啟動
        
        # 啟動前端
        frontend_process = start_frontend()
        if frontend_process:
            time.sleep(3)  # 等待前端啟動
        
        safe_print("\n" + "="*60)
        safe_print("[OK] 系統啟動完成！")
        safe_print("="*60)
        safe_print("\n後端 API: http://localhost:8000")
        safe_print("前端界面: http://localhost:3000")
        safe_print("API 文檔: http://localhost:8000/docs")
        safe_print("\n按 Ctrl+C 停止服務")
        
        # 等待用戶中斷
        try:
            while True:
                time.sleep(1)
                # 檢查進程是否還在運行
                if backend_process and backend_process.poll() is not None:
                    safe_print("\n[WARN] 後端服務已停止")
                    # 讀取錯誤輸出
                    if backend_process.stderr:
                        stderr = backend_process.stderr.read().decode('utf-8', errors='ignore')
                        if stderr:
                            safe_print("後端錯誤輸出:")
                            safe_print(stderr[:500])  # 只顯示前500字符
                    break
                if frontend_process and frontend_process.poll() is not None:
                    safe_print("\n[WARN] 前端服務已停止")
                    # 讀取錯誤輸出
                    if frontend_process.stderr:
                        stderr = frontend_process.stderr.read().decode('utf-8', errors='ignore')
                        if stderr:
                            safe_print("前端錯誤輸出:")
                            safe_print(stderr[:500])  # 只顯示前500字符
                    break
        except Exception as e:
            safe_print(f"\n[WARN] 監控進程時發生錯誤: {e}")
    
    except KeyboardInterrupt:
        safe_print("\n\n正在停止服務...")
    
    finally:
        # 清理進程
        def wait_and_kill(proc, timeout=5):
            """等待進程結束，超時後強制終止"""
            time.sleep(timeout)
            if proc.poll() is None:
                proc.kill()
        
        if backend_process:
            try:
                backend_process.terminate()
                # 等待進程結束，最多等待5秒
                wait_thread = threading.Thread(target=wait_and_kill, args=(backend_process,))
                wait_thread.daemon = True
                wait_thread.start()
                backend_process.wait()
                safe_print("[OK] 後端服務已停止")
            except Exception as e:
                safe_print(f"[WARN] 停止後端服務時發生錯誤: {e}")
        
        if frontend_process:
            try:
                frontend_process.terminate()
                # 等待進程結束，最多等待5秒
                wait_thread = threading.Thread(target=wait_and_kill, args=(frontend_process,))
                wait_thread.daemon = True
                wait_thread.start()
                frontend_process.wait()
                safe_print("[OK] 前端服務已停止")
            except Exception as e:
                safe_print(f"[WARN] 停止前端服務時發生錯誤: {e}")
        
        safe_print("\n系統已關閉")


if __name__ == "__main__":
    main()

