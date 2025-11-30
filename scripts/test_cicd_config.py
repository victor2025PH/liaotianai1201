"""
CI/CD 配置驗證腳本
驗證所有 CI/CD 工作流配置是否正確
"""
import os
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any

def check_yaml_syntax(file_path: Path) -> tuple[bool, str]:
    """檢查 YAML 文件語法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        return True, "✅ YAML 語法正確"
    except yaml.YAMLError as e:
        return False, f"❌ YAML 語法錯誤: {e}"
    except Exception as e:
        return False, f"❌ 讀取文件失敗: {e}"

def check_workflow_required_fields(workflow_data: Dict[str, Any]) -> List[str]:
    """檢查工作流必需字段"""
    errors = []
    
    if 'name' not in workflow_data:
        errors.append("缺少 'name' 字段")
    
    if 'on' not in workflow_data:
        errors.append("缺少 'on' 觸發條件")
    
    if 'jobs' not in workflow_data:
        errors.append("缺少 'jobs' 定義")
    
    return errors

def check_ci_workflow_features(workflow_data: Dict[str, Any]) -> Dict[str, bool]:
    """檢查 CI 工作流的關鍵功能"""
    features = {
        "覆蓋率檢查": False,
        "綜合檢查": False,
        "後端測試": False,
        "前端構建": False
    }
    
    if 'jobs' not in workflow_data:
        return features
    
    jobs = workflow_data['jobs']
    
    # 檢查覆蓋率檢查
    if 'backend-test' in jobs:
        steps = jobs['backend-test'].get('steps', [])
        for step in steps:
            run = step.get('run', '')
            if '--cov-fail-under=70' in run or 'cov-fail-under' in run:
                features["覆蓋率檢查"] = True
                break
    
    # 檢查綜合檢查
    if 'check-all' in jobs:
        features["綜合檢查"] = True
    
    # 檢查後端測試
    if 'backend-test' in jobs:
        features["後端測試"] = True
    
    # 檢查前端構建
    if 'frontend-build' in jobs:
        features["前端構建"] = True
    
    return features

def validate_all_workflows() -> Dict[str, Any]:
    """驗證所有工作流文件"""
    project_root = Path(__file__).parent.parent
    workflows_dir = project_root / '.github' / 'workflows'
    
    results = {
        "總數": 0,
        "通過": 0,
        "失敗": 0,
        "詳細結果": []
    }
    
    if not workflows_dir.exists():
        return {
            "錯誤": f"工作流目錄不存在: {workflows_dir}",
            **results
        }
    
    workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
    
    print("=" * 60)
    print("CI/CD 工作流配置驗證")
    print("=" * 60)
    print()
    
    for workflow_file in workflow_files:
        results["總數"] += 1
        print(f"檢查: {workflow_file.name}")
        
        # 檢查 YAML 語法
        syntax_ok, syntax_msg = check_yaml_syntax(workflow_file)
        print(f"  {syntax_msg}")
        
        if not syntax_ok:
            results["失敗"] += 1
            results["詳細結果"].append({
                "文件": workflow_file.name,
                "狀態": "失敗",
                "錯誤": syntax_msg
            })
            print()
            continue
        
        # 檢查必需字段
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = yaml.safe_load(f)
            
            errors = check_workflow_required_fields(workflow_data)
            if errors:
                print(f"  ❌ 缺少必需字段: {', '.join(errors)}")
                results["失敗"] += 1
                results["詳細結果"].append({
                    "文件": workflow_file.name,
                    "狀態": "失敗",
                    "錯誤": errors
                })
            else:
                print(f"  ✅ 必需字段完整")
                
                # 如果是 CI 工作流，檢查關鍵功能
                if workflow_file.name == 'ci.yml':
                    features = check_ci_workflow_features(workflow_data)
                    print(f"  關鍵功能檢查:")
                    for feature, enabled in features.items():
                        status = "✅" if enabled else "⚠️"
                        print(f"    {status} {feature}")
                    
                    results["詳細結果"].append({
                        "文件": workflow_file.name,
                        "狀態": "通過",
                        "功能": features
                    })
                else:
                    results["詳細結果"].append({
                        "文件": workflow_file.name,
                        "狀態": "通過"
                    })
                
                results["通過"] += 1
        except Exception as e:
            print(f"  ❌ 解析失敗: {e}")
            results["失敗"] += 1
            results["詳細結果"].append({
                "文件": workflow_file.name,
                "狀態": "失敗",
                "錯誤": str(e)
            })
        
        print()
    
    return results

def check_coverage_threshold_config() -> Dict[str, Any]:
    """檢查覆蓋率閾值配置"""
    project_root = Path(__file__).parent.parent
    
    results = {
        "ci_yml": False,
        "test_coverage_yml": False,
        "codecov_yml": False
    }
    
    # 檢查 ci.yml
    ci_file = project_root / '.github' / 'workflows' / 'ci.yml'
    if ci_file.exists():
        with open(ci_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '--cov-fail-under=70' in content or 'cov-fail-under=70' in content:
                results["ci_yml"] = True
    
    # 檢查 test-coverage.yml
    test_cov_file = project_root / '.github' / 'workflows' / 'test-coverage.yml'
    if test_cov_file.exists():
        with open(test_cov_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '--cov-fail-under=70' in content or 'cov-fail-under=70' in content:
                results["test_coverage_yml"] = True
    
    # 檢查 .codecov.yml
    codecov_file = project_root / '.codecov.yml'
    if codecov_file.exists():
        with open(codecov_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'target: 80%' in content or 'target: 70%' in content:
                results["codecov_yml"] = True
    
    return results

def main():
    """主函數"""
    print("=" * 60)
    print("CI/CD 配置驗證工具")
    print("=" * 60)
    print()
    
    # 1. 驗證所有工作流
    print("步驟 1: 驗證工作流文件")
    print("-" * 60)
    workflow_results = validate_all_workflows()
    
    print()
    print("=" * 60)
    print("驗證結果摘要")
    print("=" * 60)
    print(f"總工作流文件數: {workflow_results['總數']}")
    print(f"✅ 通過: {workflow_results['通過']}")
    print(f"❌ 失敗: {workflow_results['失敗']}")
    print()
    
    # 2. 檢查覆蓋率配置
    print("步驟 2: 檢查覆蓋率閾值配置")
    print("-" * 60)
    coverage_config = check_coverage_threshold_config()
    
    print(f"CI 工作流覆蓋率檢查: {'✅ 已配置' if coverage_config['ci_yml'] else '❌ 未配置'}")
    print(f"測試覆蓋率工作流: {'✅ 已配置' if coverage_config['test_coverage_yml'] else '❌ 未配置'}")
    print(f"Codecov 配置: {'✅ 已配置' if coverage_config['codecov_yml'] else '❌ 未配置'}")
    print()
    
    # 3. 檢查新工作流
    print("步驟 3: 檢查新增的工作流")
    print("-" * 60)
    project_root = Path(__file__).parent.parent
    workflows_dir = project_root / '.github' / 'workflows'
    
    new_workflows = ['notification.yml', 'performance-test.yml', 'lint-and-fix.yml']
    for workflow_name in new_workflows:
        workflow_file = workflows_dir / workflow_name
        if workflow_file.exists():
            print(f"✅ {workflow_name} - 存在")
        else:
            print(f"❌ {workflow_name} - 不存在")
    print()
    
    # 4. 最終總結
    print("=" * 60)
    print("最終總結")
    print("=" * 60)
    
    all_passed = (
        workflow_results['失敗'] == 0 and
        coverage_config['ci_yml'] and
        coverage_config['test_coverage_yml']
    )
    
    if all_passed:
        print("✅ 所有 CI/CD 配置驗證通過！")
        print()
        print("建議下一步:")
        print("  1. 提交代碼觸發 CI 工作流")
        print("  2. 查看 GitHub Actions 頁面驗證運行結果")
        print("  3. 檢查覆蓋率報告和綜合檢查結果")
        return 0
    else:
        print("⚠️ 部分配置需要檢查")
        print()
        if workflow_results['失敗'] > 0:
            print(f"  - {workflow_results['失敗']} 個工作流文件有問題")
        if not coverage_config['ci_yml']:
            print("  - CI 工作流缺少覆蓋率檢查")
        if not coverage_config['test_coverage_yml']:
            print("  - 測試覆蓋率工作流缺少覆蓋率檢查")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ 驗證中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
