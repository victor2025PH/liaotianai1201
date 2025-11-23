"""檢查服務器路由狀態"""
import requests

try:
    # 檢查OpenAPI
    r = requests.get('http://localhost:8000/openapi.json', timeout=5)
    openapi = r.json()
    
    all_paths = list(openapi['paths'].keys())
    review_paths = [p for p in all_paths if 'submit-review' in p or ('/review' in p and 'alert-rules' not in p) or '/publish' in p or 'revert-to-draft' in p]
    
    print(f"總路由數: {len(all_paths)}")
    print(f"\n審核相關路由 ({len(review_paths)}):")
    if review_paths:
        for p in sorted(review_paths):
            methods = list(openapi['paths'][p].keys())
            print(f"  - {p} {methods}")
    else:
        print("  未找到審核路由")
    
    # 檢查scripts路由
    scripts_paths = [p for p in all_paths if '/scripts' in p and 'version' not in p]
    print(f"\nscripts相關路由 (前10個):")
    for p in sorted(scripts_paths)[:10]:
        methods = list(openapi['paths'][p].keys())
        print(f"  - {p} {methods}")
    
    # 測試實際請求
    print(f"\n測試實際請求:")
    test_r = requests.post(
        'http://localhost:8000/api/v1/group-ai/scripts/test_review_api/submit-review',
        json={'change_summary': 'test'},
        timeout=5
    )
    print(f"  POST /api/v1/group-ai/scripts/test_review_api/submit-review")
    print(f"  Status: {test_r.status_code}")
    if test_r.status_code == 404:
        print(f"  Response: {test_r.text[:200]}")
    
except Exception as e:
    print(f"錯誤: {e}")
    import traceback
    traceback.print_exc()

