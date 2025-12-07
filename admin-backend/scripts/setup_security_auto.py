#!/usr/bin/env python3
"""
自動設置生產環境安全配置（非交互式）
用於 CI/CD 或自動化部署
"""
import os
import sys
import secrets
from pathlib import Path

def generate_secure_secret(length: int = 64) -> str:
    """生成安全的隨機密鑰"""
    return secrets.token_urlsafe(length)

def generate_secure_password(length: int = 16) -> str:
    """生成安全的隨機密碼"""
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def setup_security_config_auto():
    """自動設置安全配置（非交互式）"""
    print("=" * 60)
    print("🔒 自動設置生產環境安全配置")
    print("=" * 60)
    print()
    
    # 生成安全配置
    jwt_secret = generate_secure_secret()
    admin_password = generate_secure_password()
    
    print("✅ 已生成安全配置：")
    print(f"   JWT_SECRET: {jwt_secret[:20]}... (64 字符)")
    print(f"   ADMIN_DEFAULT_PASSWORD: {admin_password}")
    print()
    
    # 保存到環境變量文件（如果存在）
    env_file = Path(".env")
    if env_file.exists():
        print(f"📝 更新 {env_file} 文件...")
        
        # 讀取現有內容
        lines = []
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 更新配置
        updated = False
        new_lines = []
        for line in lines:
            if line.strip().startswith('JWT_SECRET='):
                new_lines.append(f"JWT_SECRET={jwt_secret}\n")
                updated = True
            elif line.strip().startswith('ADMIN_DEFAULT_PASSWORD='):
                new_lines.append(f"ADMIN_DEFAULT_PASSWORD={admin_password}\n")
                updated = True
            else:
                new_lines.append(line)
        
        # 如果沒有找到，添加新行
        if not updated:
            new_lines.append(f"\n# 自動生成的安全配置\n")
            new_lines.append(f"JWT_SECRET={jwt_secret}\n")
            new_lines.append(f"ADMIN_DEFAULT_PASSWORD={admin_password}\n")
        
        # 寫入文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"✅ 配置已更新到 {env_file.absolute()}")
    else:
        print("⚠️  .env 文件不存在，請手動設置環境變量：")
        print()
        print(f"JWT_SECRET={jwt_secret}")
        print(f"ADMIN_DEFAULT_PASSWORD={admin_password}")
        print()
    
    # 輸出到標準輸出（用於 CI/CD）
    print()
    print("=" * 60)
    print("📋 環境變量（用於 CI/CD）")
    print("=" * 60)
    print(f"export JWT_SECRET='{jwt_secret}'")
    print(f"export ADMIN_DEFAULT_PASSWORD='{admin_password}'")
    print()
    
    # 保存到文件（可選）
    secrets_file = Path("secrets.txt")
    if not secrets_file.exists():
        with open(secrets_file, 'w', encoding='utf-8') as f:
            f.write(f"JWT_SECRET={jwt_secret}\n")
            f.write(f"ADMIN_DEFAULT_PASSWORD={admin_password}\n")
        print(f"⚠️  敏感信息已保存到 {secrets_file.absolute()}")
        print("⚠️  請妥善保管此文件，部署後請刪除！")
        print()
    
    return True

def main():
    """主函數"""
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)
    
    try:
        setup_security_config_auto()
        return 0
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

