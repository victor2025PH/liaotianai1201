#!/usr/bin/env python3
"""验证Telegram注册功能集成"""
import sys
from pathlib import Path

def verify_backend_integration():
    """验证后端集成"""
    print("=" * 60)
    print("后端集成验证")
    print("=" * 60)
    
    checks = []
    
    # 1. 检查API路由
    try:
        from app.api import router
        routes = [r.path for r in router.routes if 'telegram-registration' in r.path]
        if routes:
            print(f"[OK] API路由已注册: {len(routes)} 个路由")
            for route in routes:
                print(f"     - {route}")
            checks.append(True)
        else:
            print("[FAIL] API路由未找到")
            checks.append(False)
    except Exception as e:
        print(f"[FAIL] 导入API路由失败: {e}")
        checks.append(False)
    
    # 2. 检查服务类
    try:
        from app.services.telegram_registration_service import TelegramRegistrationService
        from app.services.anti_detection_service import AntiDetectionService
        from app.services.rate_limiter_service import RateLimiterService
        print("[OK] 所有服务类可导入")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] 服务类导入失败: {e}")
        checks.append(False)
    
    # 3. 检查数据模型
    try:
        from app.models.telegram_registration import UserRegistration, SessionFile, AntiDetectionLog
        print("[OK] 所有数据模型可导入")
        checks.append(True)
    except Exception as e:
        print(f"[FAIL] 数据模型导入失败: {e}")
        checks.append(False)
    
    # 4. 检查数据库表
    try:
        from app.db import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name IN ('user_registrations', 'session_files', 'anti_detection_logs')
            """))
            tables = [row[0] for row in result]
            if len(tables) == 3:
                print("[OK] 所有数据库表已创建")
                checks.append(True)
            else:
                print(f"[WARN] 部分表未创建: {tables}")
                checks.append(False)
        finally:
            db.close()
    except Exception as e:
        print(f"[FAIL] 数据库检查失败: {e}")
        checks.append(False)
    
    return all(checks)

def verify_frontend_files():
    """验证前端文件"""
    print("\n" + "=" * 60)
    print("前端文件验证")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    frontend_path = project_root / "admin-frontend" / "src"
    
    checks = []
    
    # 检查关键文件
    files_to_check = [
        "pages/TelegramRegister.tsx",
        "pages/Accounts.tsx",
        "services/api.ts"
    ]
    
    for file_path in files_to_check:
        full_path = frontend_path / file_path
        if full_path.exists():
            print(f"[OK] {file_path} 存在")
            checks.append(True)
        else:
            print(f"[FAIL] {file_path} 不存在")
            checks.append(False)
    
    # 检查TelegramRegister组件是否被导入
    accounts_file = frontend_path / "pages" / "Accounts.tsx"
    if accounts_file.exists():
        content = accounts_file.read_text(encoding='utf-8')
        if 'TelegramRegister' in content and 'import' in content:
            print("[OK] TelegramRegister已集成到Accounts页面")
            checks.append(True)
        else:
            print("[FAIL] TelegramRegister未集成到Accounts页面")
            checks.append(False)
    
    return all(checks)

def verify_configuration():
    """验证配置"""
    print("\n" + "=" * 60)
    print("配置验证")
    print("=" * 60)
    
    checks = []
    
    # 检查vite配置
    project_root = Path(__file__).parent.parent
    vite_config = project_root / "admin-frontend" / "vite.config.ts"
    if vite_config.exists():
        content = vite_config.read_text(encoding='utf-8')
        if 'port: 3000' in content:
            print("[OK] 前端端口配置为3000")
            checks.append(True)
        else:
            print("[WARN] 前端端口配置可能不正确")
            checks.append(False)
    
    # 检查服务器配置
    config_file = project_root / "data" / "master_config.json"
    if config_file.exists():
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        servers = config.get('servers', {})
        if servers:
            print(f"[OK] 服务器配置存在 ({len(servers)} 个服务器)")
            checks.append(True)
        else:
            print("[WARN] 服务器配置为空")
            checks.append(False)
    else:
        print("[WARN] 服务器配置文件不存在")
        checks.append(False)
    
    return all(checks)

def main():
    """主验证函数"""
    print("=" * 60)
    print("Telegram注册功能集成验证")
    print("=" * 60)
    
    results = []
    
    results.append(verify_backend_integration())
    results.append(verify_frontend_files())
    results.append(verify_configuration())
    
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results)
    
    print(f"总检查项: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n[OK] 所有验证通过！系统已正确集成。")
        print("\n下一步:")
        print("1. 访问 http://localhost:3000")
        print("2. 登录系统")
        print("3. 进入'账户中心' → 'Telegram注册'")
        print("4. 开始功能测试")
        return 0
    else:
        print("\n[WARN] 部分验证失败，请检查上述问题。")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n验证已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

