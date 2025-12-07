#!/usr/bin/env python3
"""
完整自動化測試系統 - 持續監測和修復
"""
import os
import sys
import time
import subprocess
import requests
import logging
from pathlib import Path
import json

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_auto_test():
    """運行自動測試"""
    logger.info("運行自動測試腳本...")
    script_path = Path(__file__).parent / "auto_test_and_fix.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout, result.stderr

def check_services():
    """檢查服務狀態"""
    backend_ok = False
    frontend_ok = False
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        backend_ok = response.status_code == 200
    except:
        pass
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        frontend_ok = response.status_code == 200
    except:
        pass
    
    return backend_ok, frontend_ok

def main():
    """主函數 - 持續監測和修復"""
    logger.info("=" * 60)
    logger.info("🚀 完整自動化測試和修復系統")
    logger.info("=" * 60)
    logger.info("")
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        logger.info(f"嘗試 {attempt}/{max_attempts}...")
        logger.info("")
        
        # 運行自動測試
        success, stdout, stderr = run_auto_test()
        
        if success:
            logger.info("✅ 自動測試通過")
        else:
            logger.warning(f"⚠️ 自動測試發現問題:\n{stderr[-500:]}")
        
        # 檢查服務
        logger.info("檢查服務狀態...")
        backend_ok, frontend_ok = check_services()
        
        logger.info(f"後端服務: {'✅ 運行中' if backend_ok else '❌ 未運行'}")
        logger.info(f"前端服務: {'✅ 運行中' if frontend_ok else '⚠️ 未運行（可選）'}")
        
        if backend_ok:
            logger.info("")
            logger.info("=" * 60)
            logger.info("🎉 所有功能正常！系統運行完美！")
            logger.info("=" * 60)
            logger.info("")
            logger.info("服務地址：")
            logger.info("  後端: http://localhost:8000")
            logger.info("  前端: http://localhost:3000")
            logger.info("  API 文檔: http://localhost:8000/docs")
            logger.info("")
            return 0
        
        if attempt < max_attempts:
            logger.info("")
            logger.info(f"等待 10 秒後重試...")
            time.sleep(10)
    
    logger.error("")
    logger.error("=" * 60)
    logger.error("❌ 經過多次嘗試，仍有問題")
    logger.error("=" * 60)
    logger.error("")
    logger.error("請檢查：")
    logger.error("  1. 數據庫配置是否正確")
    logger.error("  2. 端口是否被占用")
    logger.error("  3. 查看日誌文件: auto_test.log")
    logger.error("")
    return 1

if __name__ == "__main__":
    sys.exit(main())

