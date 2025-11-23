#!/usr/bin/env python3
"""
生產環境配置檢查腳本

檢查生產環境部署前的必要配置項
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_env_file(file_path: Path, required_vars: List[str], optional_vars: List[str] = None) -> Tuple[bool, List[str]]:
    """檢查環境變量文件"""
    errors = []
    warnings = []
    
    if not file_path.exists():
        errors.append(f"環境變量文件不存在: {file_path}")
        return False, errors
    
    # 讀取環境變量
    env_vars = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    # 檢查必填變量
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            errors.append(f"缺少必填環境變量: {var}")
        elif var == 'JWT_SECRET' and len(env_vars[var]) < 32:
            errors.append(f"JWT_SECRET 長度不足 32 字符（安全要求）")
        elif var == 'ADMIN_DEFAULT_PASSWORD' and len(env_vars[var]) < 8:
            errors.append(f"ADMIN_DEFAULT_PASSWORD 長度不足 8 字符（安全要求）")
    
    # 檢查可選變量
    if optional_vars:
        for var in optional_vars:
            if var not in env_vars or not env_vars[var]:
                warnings.append(f"缺少可選環境變量: {var}（建議配置）")
    
    # 檢查生產環境特定配置
    if 'DISABLE_AUTH' in env_vars:
        if env_vars['DISABLE_AUTH'].lower() in ('true', '1', 'yes', 'on'):
            errors.append("⚠️  警告: DISABLE_AUTH=true 在生產環境中不安全！")
    
    if 'DATABASE_URL' in env_vars:
        if 'sqlite' in env_vars['DATABASE_URL'].lower():
            warnings.append("⚠️  建議: 生產環境使用 PostgreSQL 而非 SQLite")
    
    return len(errors) == 0, errors + warnings


def check_alembic_migrations() -> Tuple[bool, List[str]]:
    """檢查 Alembic 遷移狀態"""
    errors = []
    warnings = []
    
    alembic_dir = project_root / 'admin-backend' / 'alembic'
    versions_dir = alembic_dir / 'versions'
    
    if not alembic_dir.exists():
        errors.append("Alembic 目錄不存在")
        return False, errors
    
    if not versions_dir.exists():
        errors.append("Alembic versions 目錄不存在")
        return False, errors
    
    # 檢查遷移文件
    migration_files = list(versions_dir.glob('*.py'))
    if not migration_files:
        warnings.append("未找到 Alembic 遷移文件")
    else:
        print(f"✓ 找到 {len(migration_files)} 個遷移文件")
    
    return len(errors) == 0, errors + warnings


def main():
    """主函數"""
    print("=" * 60)
    print("生產環境配置檢查")
    print("=" * 60)
    print()
    
    all_errors = []
    all_warnings = []
    
    # 檢查後端環境變量
    print("1. 檢查後端環境變量...")
    backend_env = project_root / 'admin-backend' / '.env'
    required_backend_vars = [
        'JWT_SECRET',
        'ADMIN_DEFAULT_EMAIL',
        'ADMIN_DEFAULT_PASSWORD',
    ]
    optional_backend_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'DISABLE_AUTH',
    ]
    
    backend_ok, backend_issues = check_env_file(backend_env, required_backend_vars, optional_backend_vars)
    if backend_ok:
        print("  ✓ 後端環境變量檢查通過")
    else:
        print("  ✗ 後端環境變量檢查失敗")
        all_errors.extend([issue for issue in backend_issues if issue.startswith('缺少') or issue.startswith('⚠️')])
        all_warnings.extend([issue for issue in backend_issues if issue not in all_errors])
    
    for issue in backend_issues:
        if issue.startswith('⚠️'):
            print(f"  {issue}")
        elif issue.startswith('缺少'):
            print(f"  ✗ {issue}")
        else:
            print(f"  ⚠ {issue}")
    
    print()
    
    # 檢查主程序環境變量
    print("2. 檢查主程序環境變量...")
    main_env = project_root / '.env'
    required_main_vars = [
        'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH',
    ]
    optional_main_vars = [
        'AI_PROVIDER',
        'AI_API_KEY',
    ]
    
    main_ok, main_issues = check_env_file(main_env, required_main_vars, optional_main_vars)
    if main_ok:
        print("  ✓ 主程序環境變量檢查通過")
    else:
        print("  ✗ 主程序環境變量檢查失敗")
        all_errors.extend([issue for issue in main_issues if issue.startswith('缺少')])
        all_warnings.extend([issue for issue in main_issues if issue not in all_errors])
    
    for issue in main_issues:
        if issue.startswith('缺少'):
            print(f"  ✗ {issue}")
        else:
            print(f"  ⚠ {issue}")
    
    print()
    
    # 檢查 Alembic 遷移
    print("3. 檢查 Alembic 遷移...")
    alembic_ok, alembic_issues = check_alembic_migrations()
    if alembic_ok:
        print("  ✓ Alembic 遷移檢查通過")
    else:
        print("  ✗ Alembic 遷移檢查失敗")
        all_errors.extend(alembic_issues)
    
    for issue in alembic_issues:
        if issue.startswith('未找到'):
            print(f"  ⚠ {issue}")
        else:
            print(f"  ✗ {issue}")
    
    print()
    
    # 總結
    print("=" * 60)
    print("檢查結果")
    print("=" * 60)
    
    if all_errors:
        print(f"\n✗ 發現 {len(all_errors)} 個錯誤:")
        for error in all_errors:
            print(f"  - {error}")
    
    if all_warnings:
        print(f"\n⚠ 發現 {len(all_warnings)} 個警告:")
        for warning in all_warnings:
            print(f"  - {warning}")
    
    if not all_errors and not all_warnings:
        print("\n✓ 所有檢查通過！可以部署到生產環境。")
        return 0
    elif not all_errors:
        print("\n⚠ 有警告，但可以繼續部署。建議修復警告項。")
        return 0
    else:
        print("\n✗ 發現錯誤，請修復後再部署。")
        return 1


if __name__ == '__main__':
    sys.exit(main())

