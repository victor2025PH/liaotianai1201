#!/usr/bin/env python3
"""
全自動測試和修復系統
監測運行日誌，自動修復錯誤，直到所有功能正常
"""
import os
import sys
import time
import subprocess
import requests
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import re

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoTester:
    """自動測試和修復系統"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root
        self.frontend_dir = self.project_root.parent / "saas-demo"
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.backend_process = None
        self.frontend_process = None
        self.errors_found = []
        self.fixes_applied = []
        
    def check_service(self, url: str, timeout: int = 5) -> bool:
        """檢查服務是否運行"""
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except:
            return False
    
    def wait_for_service(self, url: str, max_wait: int = 60) -> bool:
        """等待服務啟動"""
        logger.info(f"等待服務啟動: {url}")
        for i in range(0, max_wait, 2):
            if self.check_service(url):
                logger.info(f"✅ 服務已啟動: {url}")
                return True
            time.sleep(2)
            if i % 10 == 0:
                logger.info(f"⏳ 等待中... ({i}/{max_wait}秒)")
        return False
    
    def fix_database_config(self) -> bool:
        """修復數據庫配置"""
        logger.info("🔧 修復數據庫配置...")
        
        # 確保使用 SQLite
        env_file = self.backend_dir / ".env"
        if not env_file.exists():
            logger.info("創建 .env 文件...")
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write("DATABASE_URL=sqlite:///./admin.db\n")
            self.fixes_applied.append("創建 .env 文件")
        else:
            # 檢查並更新 DATABASE_URL
            content = env_file.read_text(encoding='utf-8')
            if 'DATABASE_URL=' not in content:
                with open(env_file, 'a', encoding='utf-8') as f:
                    f.write("\nDATABASE_URL=sqlite:///./admin.db\n")
                self.fixes_applied.append("添加 DATABASE_URL 到 .env")
            elif 'postgresql://' in content:
                # 替換 PostgreSQL 為 SQLite
                content = re.sub(r'DATABASE_URL=.*', 'DATABASE_URL=sqlite:///./admin.db', content)
                env_file.write_text(content, encoding='utf-8')
                self.fixes_applied.append("將數據庫切換為 SQLite")
        
        # 確保配置類讀取 .env
        config_file = self.backend_dir / "app" / "core" / "config.py"
        if config_file.exists():
            content = config_file.read_text(encoding='utf-8')
            if 'env_file = None' in content:
                content = content.replace('env_file = None', 'env_file = ".env"')
                config_file.write_text(content, encoding='utf-8')
                self.fixes_applied.append("啟用 .env 文件讀取")
        
        return True
    
    def init_database(self) -> bool:
        """初始化數據庫"""
        logger.info("🔧 初始化數據庫...")
        
        # 設置環境變量
        os.environ["DATABASE_URL"] = "sqlite:///./admin.db"
        
        try:
            # 運行初始化腳本
            result = subprocess.run(
                [sys.executable, "init_db_tables.py"],
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=30,
                env=os.environ.copy()
            )
            
            if result.returncode == 0:
                logger.info("✅ 數據庫初始化成功")
                self.fixes_applied.append("初始化數據庫表")
                return True
            else:
                logger.error(f"❌ 數據庫初始化失敗: {result.stderr}")
                self.errors_found.append(f"數據庫初始化失敗: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ 數據庫初始化異常: {e}")
            self.errors_found.append(f"數據庫初始化異常: {e}")
            return False
    
    def start_backend(self) -> bool:
        """啟動後端服務"""
        logger.info("🚀 啟動後端服務...")
        
        # 檢查是否已在運行
        if self.check_service(f"{self.backend_url}/health"):
            logger.info("✅ 後端服務已在運行")
            return True
        
        # 設置環境變量
        env = os.environ.copy()
        env["DATABASE_URL"] = "sqlite:///./admin.db"
        
        # 直接使用 uvicorn 啟動
        try:
            logger.info("使用 uvicorn 啟動服務...")
            self.backend_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1
            )
            
            # 監測啟動日誌
            logger.info("監測啟動日誌...")
            start_time = time.time()
            max_wait = 90  # 增加等待時間
            last_output = ""
            
            # 使用線程讀取輸出
            import threading
            output_lines = []
            
            def read_output():
                try:
                    for line in iter(self.backend_process.stdout.readline, ''):
                        if line:
                            output_lines.append(line.strip())
                            # 檢查關鍵錯誤
                            if 'ERROR' in line or 'Exception' in line or 'Traceback' in line:
                                logger.warning(f"檢測到錯誤: {line.strip()[:100]}")
                except:
                    pass
            
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()
            
            while time.time() - start_time < max_wait:
                # 檢查進程是否還在運行
                if self.backend_process.poll() is not None:
                    # 進程已結束，讀取所有輸出
                    time.sleep(1)  # 等待輸出線程
                    output = '\n'.join(output_lines[-50:])  # 最後50行
                    logger.error(f"服務進程已退出，最後輸出:\n{output}")
                    self.errors_found.append("服務進程意外退出")
                    # 嘗試從輸出中提取錯誤信息
                    for line in output_lines:
                        if 'ERROR' in line or 'Exception' in line:
                            self.errors_found.append(line[:200])
                    return False
                
                # 檢查服務是否可用
                if self.check_service(f"{self.backend_url}/health"):
                    logger.info("✅ 後端服務啟動成功")
                    # 顯示啟動成功的關鍵信息
                    success_lines = [l for l in output_lines if 'Started' in l or 'Uvicorn running' in l]
                    if success_lines:
                        logger.info(f"啟動信息: {success_lines[-1]}")
                    return True
                
                # 每10秒顯示一次進度
                elapsed = int(time.time() - start_time)
                if elapsed % 10 == 0 and elapsed > 0:
                    logger.info(f"⏳ 等待服務啟動... ({elapsed}/{max_wait}秒)")
                
                time.sleep(2)
            
            logger.error("❌ 後端服務啟動超時")
            self.errors_found.append("後端服務啟動超時")
            return False
        except Exception as e:
            logger.error(f"❌ 啟動後端服務失敗: {e}")
            self.errors_found.append(f"啟動後端服務失敗: {e}")
            return False
    
    def check_backend_health(self) -> Tuple[bool, List[str]]:
        """檢查後端健康狀態"""
        issues = []
        
        try:
            # 檢查健康端點
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code != 200:
                issues.append(f"健康檢查失敗: HTTP {response.status_code}")
            
            # 檢查詳細健康信息
            response = requests.get(f"{self.backend_url}/health?detailed=true", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") != "healthy":
                    issues.append(f"系統狀態不健康: {data.get('status')}")
        except Exception as e:
            issues.append(f"健康檢查異常: {e}")
        
        return len(issues) == 0, issues
    
    def check_api_endpoints(self) -> Tuple[bool, List[str]]:
        """檢查 API 端點"""
        issues = []
        endpoints = [
            "/health",
            "/healthz",
            "/docs",
            "/api/v1/auth/login",
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                if response.status_code not in [200, 401, 405]:
                    issues.append(f"{endpoint}: HTTP {response.status_code}")
            except Exception as e:
                issues.append(f"{endpoint}: {e}")
        
        return len(issues) == 0, issues
    
    def check_frontend(self) -> bool:
        """檢查前端服務"""
        if self.check_service(self.frontend_url):
            logger.info("✅ 前端服務運行中")
            return True
        else:
            logger.warning("⚠️ 前端服務未運行（可選）")
            return False
    
    def run_tests(self) -> Tuple[bool, List[str]]:
        """運行測試"""
        logger.info("🧪 運行測試...")
        issues = []
        
        # 運行安全配置檢查
        try:
            result = subprocess.run(
                [sys.executable, "scripts/check_security_config.py"],
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                issues.append("安全配置檢查失敗")
        except Exception as e:
            issues.append(f"安全配置檢查異常: {e}")
        
        return len(issues) == 0, issues
    
    def monitor_logs(self, duration: int = 30) -> List[str]:
        """監測運行日誌"""
        logger.info(f"📊 監測運行日誌 ({duration}秒)...")
        errors = []
        
        # 檢查日誌文件
        log_file = self.backend_dir.parent / "logs" / "backend.log"
        if log_file.exists():
            # 讀取最近的錯誤
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 檢查最後 100 行中的錯誤
                    for line in lines[-100:]:
                        if 'ERROR' in line or 'Exception' in line or 'Traceback' in line:
                            errors.append(line.strip())
            except Exception as e:
                logger.warning(f"讀取日誌文件失敗: {e}")
        
        return errors
    
    def auto_fix_errors(self, errors: List[str]) -> bool:
        """自動修復錯誤"""
        logger.info("🔧 嘗試自動修復錯誤...")
        
        fixed = False
        
        for error in errors:
            # 數據庫相關錯誤
            if 'group_ai_scripts' in error or 'UndefinedTable' in error:
                logger.info("檢測到數據庫表缺失，嘗試初始化...")
                if self.init_database():
                    fixed = True
            
            # 配置相關錯誤
            if 'DATABASE_URL' in error or 'postgresql' in error.lower():
                logger.info("檢測到數據庫配置問題，嘗試修復...")
                if self.fix_database_config():
                    fixed = True
        
        return fixed
    
    def run_full_test(self) -> bool:
        """運行完整測試流程"""
        logger.info("=" * 60)
        logger.info("🚀 開始全自動測試和修復")
        logger.info("=" * 60)
        logger.info("")
        
        # 步驟 1: 修復配置
        logger.info("[1/6] 檢查和修復配置...")
        self.fix_database_config()
        
        # 步驟 2: 初始化數據庫
        logger.info("[2/6] 初始化數據庫...")
        if not self.init_database():
            logger.error("❌ 數據庫初始化失敗，無法繼續")
            return False
        
        # 步驟 3: 啟動後端服務
        logger.info("[3/6] 啟動後端服務...")
        if not self.start_backend():
            logger.error("❌ 後端服務啟動失敗")
            return False
        
        # 步驟 4: 檢查後端健康
        logger.info("[4/6] 檢查後端健康狀態...")
        healthy, issues = self.check_backend_health()
        if not healthy:
            logger.warning(f"⚠️ 發現健康問題: {issues}")
            self.errors_found.extend(issues)
        
        # 步驟 5: 檢查 API 端點
        logger.info("[5/6] 檢查 API 端點...")
        api_ok, api_issues = self.check_api_endpoints()
        if not api_ok:
            logger.warning(f"⚠️ API 端點問題: {api_issues}")
            self.errors_found.extend(api_issues)
        
        # 步驟 6: 監測日誌
        logger.info("[6/6] 監測運行日誌...")
        log_errors = self.monitor_logs(duration=10)
        if log_errors:
            logger.warning(f"⚠️ 發現日誌錯誤: {len(log_errors)} 個")
            self.errors_found.extend(log_errors[:5])  # 只記錄前5個
        
        # 嘗試自動修復
        if self.errors_found:
            logger.info("🔧 嘗試自動修復錯誤...")
            self.auto_fix_errors(self.errors_found)
        
        # 生成報告
        self.generate_report()
        
        return len(self.errors_found) == 0
    
    def generate_report(self):
        """生成測試報告"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 測試報告")
        logger.info("=" * 60)
        logger.info("")
        
        logger.info(f"✅ 應用的修復: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            logger.info(f"  - {fix}")
        
        logger.info("")
        logger.info(f"{'✅' if len(self.errors_found) == 0 else '❌'} 發現的問題: {len(self.errors_found)}")
        for error in self.errors_found[:10]:  # 只顯示前10個
            logger.info(f"  - {error[:100]}")  # 截斷長錯誤
        
        logger.info("")
        if len(self.errors_found) == 0:
            logger.info("🎉 所有測試通過！系統運行正常！")
        else:
            logger.warning("⚠️ 發現問題，請檢查上述錯誤")
    
    def cleanup(self):
        """清理資源"""
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
            except:
                self.backend_process.kill()

def main():
    """主函數"""
    tester = AutoTester()
    
    try:
        success = tester.run_full_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\n❌ 用戶中斷")
        return 1
    except Exception as e:
        logger.error(f"❌ 異常: {e}", exc_info=True)
        return 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    sys.exit(main())

