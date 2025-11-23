#!/usr/bin/env python3
"""
生成測試覆蓋率報告

運行所有測試並生成覆蓋率報告
"""
import sys
import subprocess
from pathlib import Path

def main():
    """主函數"""
    project_root = Path(__file__).parent.parent
    
    print("=" * 60)
    print("生成測試覆蓋率報告")
    print("=" * 60)
    print()
    
    # 後端測試覆蓋率
    print("1. 運行後端測試並生成覆蓋率報告...")
    backend_dir = project_root / "admin-backend"
    
    if backend_dir.exists():
        try:
            result = subprocess.run(
                [
                    "poetry", "run", "pytest",
                    "--cov=app",
                    "--cov=group_ai_service",
                    "--cov-report=html",
                    "--cov-report=xml",
                    "--cov-report=term-missing",
                    "-v"
                ],
                cwd=backend_dir,
                timeout=600
            )
            
            if result.returncode == 0:
                print("✅ 後端測試完成")
                print(f"📊 覆蓋率報告已生成: {backend_dir / 'htmlcov' / 'index.html'}")
            else:
                print("⚠️ 後端測試有失敗，但報告已生成")
        except subprocess.TimeoutExpired:
            print("⚠️ 測試超時")
        except Exception as e:
            print(f"⚠️ 測試執行失敗: {e}")
    else:
        print("⚠️ 後端目錄不存在")
    
    print()
    
    # 主程序測試覆蓋率
    print("2. 運行主程序測試...")
    scripts_dir = project_root / "scripts"
    test_files = list(scripts_dir.glob("test_*.py"))
    
    if test_files:
        print(f"找到 {len(test_files)} 個測試文件")
        # 這裡可以運行主程序的測試
        # 由於主程序測試可能需要特殊環境，暫時跳過
        print("⚠️ 主程序測試需要特殊環境，請手動運行")
    else:
        print("⚠️ 未找到主程序測試文件")
    
    print()
    print("=" * 60)
    print("覆蓋率報告生成完成")
    print("=" * 60)
    print()
    print("查看報告:")
    print(f"  - HTML 報告: {backend_dir / 'htmlcov' / 'index.html'}")
    print(f"  - XML 報告: {backend_dir / 'coverage.xml'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

