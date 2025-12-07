#!/usr/bin/env python3
"""
安全配置檢查腳本
檢查生產環境安全配置是否正確
"""
import os
import sys
import secrets
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 先讀取 .env 文件並設置環境變量（如果存在）
env_file = project_root / ".env"
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # 只設置未存在的環境變量（避免覆蓋系統環境變量）
                if key and value and key not in os.environ:
                    os.environ[key] = value

from app.core.config import get_settings

def generate_secure_secret(length: int = 64) -> str:
    """生成安全的隨機密鑰"""
    return secrets.token_urlsafe(length)

def check_jwt_secret(settings) -> tuple[bool, str]:
    """檢查 JWT Secret 是否安全"""
    default_secrets = ["change_me", "changeme", "secret", "test"]
    
    if settings.jwt_secret in default_secrets:
        return False, f"⚠️  JWT_SECRET 使用默認值 '{settings.jwt_secret}'，存在安全風險！"
    
    if len(settings.jwt_secret) < 32:
        return False, f"⚠️  JWT_SECRET 長度過短（{len(settings.jwt_secret)} 字符），建議至少 32 字符"
    
    return True, "✅ JWT_SECRET 配置正確"

def check_admin_password(settings) -> tuple[bool, str]:
    """檢查管理員密碼是否安全"""
    default_passwords = ["changeme123", "admin", "password", "123456", "admin123"]
    
    if settings.admin_default_password in default_passwords:
        return False, f"⚠️  ADMIN_DEFAULT_PASSWORD 使用默認值，存在安全風險！"
    
    if len(settings.admin_default_password) < 12:
        return False, f"⚠️  管理員密碼長度過短（{len(settings.admin_default_password)} 字符），建議至少 12 字符"
    
    return True, "✅ 管理員密碼配置正確"

def check_cors_config(settings) -> tuple[bool, str]:
    """檢查 CORS 配置"""
    if not settings.cors_origins:
        return False, "⚠️  CORS_ORIGINS 未配置"
    
    origins = settings.cors_origins.split(",")
    if "*" in origins:
        return False, "⚠️  CORS_ORIGINS 包含 '*'，這在 allow_credentials=True 時不安全"
    
    # 檢查是否包含生產環境域名
    localhost_only = all("localhost" in origin or "127.0.0.1" in origin for origin in origins)
    if localhost_only:
        return False, "⚠️  CORS_ORIGINS 僅包含 localhost，生產環境需要配置實際域名"
    
    return True, "✅ CORS 配置正確"

def check_auth_disabled(settings) -> tuple[bool, str]:
    """檢查認證是否被禁用"""
    if settings.disable_auth:
        return False, "⚠️  DISABLE_AUTH 設置為 true，生產環境必須啟用認證！"
    
    return True, "✅ 認證已啟用"

def main():
    """主函數"""
    print("=" * 60)
    print("🔒 安全配置檢查")
    print("=" * 60)
    print()
    
    settings = get_settings()
    
    checks = [
        ("JWT Secret", check_jwt_secret(settings)),
        ("管理員密碼", check_admin_password(settings)),
        ("CORS 配置", check_cors_config(settings)),
        ("認證啟用", check_auth_disabled(settings)),
    ]
    
    all_passed = True
    issues = []
    
    for name, (passed, message) in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {message}")
        
        if not passed:
            all_passed = False
            issues.append((name, message))
    
    print()
    print("=" * 60)
    
    if all_passed:
        print("✅ 所有安全檢查通過！")
        return 0
    else:
        print("❌ 發現安全問題，請修復後再部署！")
        print()
        print("建議操作：")
        print()
        
        # 生成建議的配置
        if not check_jwt_secret(settings)[0]:
            new_secret = generate_secure_secret()
            print(f"1. 設置 JWT_SECRET（建議值）：")
            print(f"   JWT_SECRET={new_secret}")
            print()
        
        if not check_admin_password(settings)[0]:
            print(f"2. 設置強密碼 ADMIN_DEFAULT_PASSWORD（至少 12 字符）")
            print()
        
        if not check_cors_config(settings)[0]:
            print(f"3. 配置 CORS_ORIGINS 為實際生產域名")
            print()
        
        if not check_auth_disabled(settings)[0]:
            print(f"4. 設置 DISABLE_AUTH=false")
            print()
        
        print("可以通過以下方式設置環境變量：")
        print("  - 在 .env 文件中設置（如果使用）")
        print("  - 在系統環境變量中設置")
        print("  - 在部署平台（如 Docker、K8s）中設置")
        print()
        
        return 1

if __name__ == "__main__":
    sys.exit(main())

