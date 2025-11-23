#!/usr/bin/env python3
"""
測試覆蓋率分析腳本

分析當前測試覆蓋率，識別需要補充測試的模塊
"""
import sys
import subprocess
from pathlib import Path

def run_coverage_analysis():
    """運行測試覆蓋率分析"""
    project_root = Path(__file__).parent.parent
    
    print("=" * 60)
    print("測試覆蓋率分析")
    print("=" * 60)
    print()
    
    # 後端測試覆蓋率
    print("1. 分析後端測試覆蓋率...")
    backend_dir = project_root / "admin-backend"
    
    if backend_dir.exists():
        try:
            result = subprocess.run(
                ["poetry", "run", "pytest", "--cov=app", "--cov-report=term-missing", "--cov-report=html"],
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            print("後端測試結果:")
            print(result.stdout)
            if result.stderr:
                print("錯誤:", result.stderr)
            
            if result.returncode == 0:
                print("✅ 後端測試通過")
            else:
                print("⚠️ 後端測試有失敗")
        except Exception as e:
            print(f"⚠️ 後端測試執行失敗: {e}")
    else:
        print("⚠️ 後端目錄不存在")
    
    print()
    
    # 主程序測試覆蓋率
    print("2. 分析主程序測試覆蓋率...")
    scripts_dir = project_root / "scripts"
    
    # 查找測試文件
    test_files = list(scripts_dir.glob("test_*.py"))
    print(f"找到 {len(test_files)} 個測試文件:")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    print()
    
    # 分析需要測試的模塊
    print("3. 分析需要測試的模塊...")
    group_ai_service_dir = project_root / "group_ai_service"
    
    if group_ai_service_dir.exists():
        python_files = list(group_ai_service_dir.glob("*.py"))
        python_files = [f for f in python_files if f.name != "__init__.py"]
        
        print(f"找到 {len(python_files)} 個 Python 模塊:")
        for py_file in python_files:
            # 檢查是否有對應的測試文件
            test_file = scripts_dir / f"test_{py_file.stem}.py"
            if test_file.exists():
                print(f"  ✅ {py_file.name} - 有測試")
            else:
                print(f"  ⚠️ {py_file.name} - 缺少測試")
    
    print()
    print("=" * 60)
    print("分析完成")
    print("=" * 60)

if __name__ == "__main__":
    run_coverage_analysis()

