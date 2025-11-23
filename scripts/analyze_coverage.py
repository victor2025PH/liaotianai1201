"""
分析測試覆蓋率腳本
"""
import subprocess
import re
import sys
from pathlib import Path

def get_coverage_report():
    """獲取測試覆蓋率報告"""
    project_root = Path(__file__).parent.parent
    admin_backend = project_root / "admin-backend"
    
    # 運行測試並獲取覆蓋率報告
    result = subprocess.run(
        ["poetry", "run", "pytest", "tests/", "--cov=group_ai_service", "--cov-report=term", "--tb=no", "-q"],
        cwd=admin_backend,
        capture_output=True,
        text=True
    )
    
    return result.stdout + result.stderr

def parse_coverage_report(output):
    """解析覆蓋率報告"""
    lines = output.split('\n')
    
    modules = []
    total_stmts = 0
    total_miss = 0
    
    for line in lines:
        # 匹配模塊行: group_ai_service\xxx.py   123   45   63%
        match = re.match(r'^group_ai_service[\\/]([^\s]+)\s+(\d+)\s+(\d+)\s+(\d+)%', line)
        if match:
            module_name = match.group(1)
            stmts = int(match.group(2))
            miss = int(match.group(3))
            cover = int(match.group(4))
            
            modules.append({
                'name': module_name,
                'stmts': stmts,
                'miss': miss,
                'cover': cover
            })
            total_stmts += stmts
            total_miss += miss
        
        # 匹配總計行
        total_match = re.search(r'TOTAL.*?(\d+)\s+(\d+)\s+(\d+)%', line)
        if total_match:
            total_stmts = int(total_match.group(1))
            total_miss = int(total_match.group(2))
            total_cover = int(total_match.group(3))
    
    return modules, total_stmts, total_miss, total_cover

def analyze_coverage():
    """分析覆蓋率"""
    print("正在獲取測試覆蓋率報告...")
    output = get_coverage_report()
    
    modules, total_stmts, total_miss, total_cover = parse_coverage_report(output)
    
    if not modules:
        print("無法解析覆蓋率報告，輸出原始結果：")
        print(output[-2000:])  # 輸出最後 2000 字符
        return
    
    print(f"\n{'='*80}")
    print(f"group_ai_service 模塊測試覆蓋率分析")
    print(f"{'='*80}\n")
    
    # 按覆蓋率排序
    modules_sorted = sorted(modules, key=lambda x: x['cover'])
    
    # 高覆蓋率模塊（80%+）
    high_coverage = [m for m in modules_sorted if m['cover'] >= 80]
    # 中等覆蓋率模塊（60-80%）
    medium_coverage = [m for m in modules_sorted if 60 <= m['cover'] < 80]
    # 低覆蓋率模塊（<60%）
    low_coverage = [m for m in modules_sorted if m['cover'] < 60]
    
    print(f"📊 總體統計:")
    print(f"   總模塊數: {len(modules)}")
    print(f"   總代碼行: {total_stmts}")
    print(f"   未覆蓋行: {total_miss}")
    print(f"   總體覆蓋率: {total_cover}%\n")
    
    print(f"✅ 高覆蓋率模塊（80%+）: {len(high_coverage)} 個")
    for m in sorted(high_coverage, key=lambda x: x['cover'], reverse=True):
        print(f"   {m['name']:50s} {m['cover']:3d}% ({m['stmts']-m['miss']}/{m['stmts']})")
    
    print(f"\n🔄 中等覆蓋率模塊（60-80%）: {len(medium_coverage)} 個")
    for m in sorted(medium_coverage, key=lambda x: x['cover'], reverse=True):
        print(f"   {m['name']:50s} {m['cover']:3d}% ({m['stmts']-m['miss']}/{m['stmts']})")
    
    print(f"\n⚠️  低覆蓋率模塊（<60%）: {len(low_coverage)} 個")
    for m in sorted(low_coverage, key=lambda x: x['cover']):
        print(f"   {m['name']:50s} {m['cover']:3d}% ({m['stmts']-m['miss']}/{m['stmts']})")
    
    print(f"\n{'='*80}")
    print(f"建議優先補充測試的模塊（覆蓋率 < 60%）:")
    for m in sorted(low_coverage, key=lambda x: x['cover'])[:10]:
        print(f"   - {m['name']} ({m['cover']}%)")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    analyze_coverage()

