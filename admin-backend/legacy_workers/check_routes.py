"""檢查API路由"""
import requests

try:
    r = requests.get('http://localhost:8000/openapi.json', timeout=5)
    openapi = r.json()
    
    all_paths = list(openapi['paths'].keys())
    review_paths = [p for p in all_paths if 'submit-review' in p or '/review' in p or '/publish' in p or '/disable' in p or 'revert-to-draft' in p]
    
    print(f"總路由數: {len(all_paths)}")
    print(f"\n審核相關路由 ({len(review_paths)}):")
    if review_paths:
        for p in sorted(review_paths):
            print(f"  - {p}")
    else:
        print("  未找到審核路由")
        print("\n所有scripts相關路由:")
        scripts_paths = [p for p in all_paths if '/scripts' in p]
        for p in sorted(scripts_paths)[:20]:  # 只顯示前20個
            print(f"  - {p}")
    
except Exception as e:
    print(f"錯誤: {e}")

