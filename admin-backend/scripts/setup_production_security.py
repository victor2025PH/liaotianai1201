#!/usr/bin/env python3
"""
生產環境安全配置設置腳本
自動生成安全的 JWT_SECRET 和管理員密碼
"""
import os
import sys
import secrets
import getpass
from pathlib import Path

def generate_secure_secret(length: int = 64) -> str:
    """生成安全的隨機密鑰"""
    return secrets.token_urlsafe(length)

def generate_secure_password(length: int = 16) -> str:
    """生成安全的隨機密碼"""
    # 包含大小寫字母、數字和特殊字符
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def setup_env_file():
    """設置 .env 文件"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    # 如果 .env 不存在，從 .env.example 複製
    if not env_file.exists() and env_example.exists():
        print("📋 從 .env.example 創建 .env 文件...")
        import shutil
        shutil.copy(env_example, env_file)
        print("✅ .env 文件已創建")
    elif not env_file.exists():
        print("⚠️  .env.example 不存在，創建新的 .env 文件...")
        env_file.touch()
    
    # 讀取現有配置
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # 生成新的安全配置
    print()
    print("=" * 60)
    print("🔒 生產環境安全配置設置")
    print("=" * 60)
    print()
    
    # JWT Secret
    if env_vars.get('JWT_SECRET', '').strip() in ['', 'change_me', 'changeme']:
        new_secret = generate_secure_secret()
        env_vars['JWT_SECRET'] = new_secret
        print(f"✅ 已生成新的 JWT_SECRET（64 字符）")
    else:
        print(f"ℹ️  JWT_SECRET 已設置（長度: {len(env_vars.get('JWT_SECRET', ''))}）")
    
    # 管理員密碼
    if env_vars.get('ADMIN_DEFAULT_PASSWORD', '').strip() in ['', 'changeme123', 'admin', 'password']:
        print()
        print("請設置管理員密碼：")
        print("  1. 自動生成強密碼（推薦）")
        print("  2. 手動輸入密碼")
        choice = input("請選擇 (1/2，默認 1): ").strip() or "1"
        
        if choice == "1":
            new_password = generate_secure_password()
            env_vars['ADMIN_DEFAULT_PASSWORD'] = new_password
            print(f"✅ 已生成新的管理員密碼: {new_password}")
            print("⚠️  請妥善保存此密碼！")
        else:
            password = getpass.getpass("請輸入管理員密碼（至少 12 字符）: ")
            if len(password) < 12:
                print("⚠️  密碼長度不足 12 字符，建議使用更長的密碼")
                confirm = input("是否繼續？(y/N): ").strip().lower()
                if confirm != 'y':
                    print("❌ 已取消")
                    return False
            env_vars['ADMIN_DEFAULT_PASSWORD'] = password
            print("✅ 管理員密碼已設置")
    else:
        print(f"ℹ️  管理員密碼已設置（長度: {len(env_vars.get('ADMIN_DEFAULT_PASSWORD', ''))}）")
    
    # CORS 配置檢查
    cors_origins = env_vars.get('CORS_ORIGINS', '')
    if not cors_origins or 'localhost' in cors_origins.lower():
        print()
        print("⚠️  CORS_ORIGINS 包含 localhost，生產環境需要配置實際域名")
        new_origins = input("請輸入生產環境域名（逗號分隔，留空跳過）: ").strip()
        if new_origins:
            env_vars['CORS_ORIGINS'] = new_origins
            print("✅ CORS_ORIGINS 已更新")
    
    # 確保認證已啟用
    if env_vars.get('DISABLE_AUTH', '').lower() in ['true', '1', 'yes']:
        env_vars['DISABLE_AUTH'] = 'false'
        print("✅ DISABLE_AUTH 已設置為 false")
    
    # 寫入 .env 文件
    print()
    print("=" * 60)
    print("💾 保存配置到 .env 文件...")
    print("=" * 60)
    
    # 讀取 .env.example 作為模板
    lines = []
    if env_example.exists():
        with open(env_example, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        # 如果沒有 .env.example，創建基本結構
        lines = [
            "# ============================================\n",
            "# Smart TG Admin Backend 環境變量配置\n",
            "# ============================================\n",
            "\n"
        ]
    
    # 更新或添加環境變量
    updated_keys = set()
    new_lines = []
    for line in lines:
        if line.strip() and not line.strip().startswith('#') and '=' in line:
            key = line.split('=', 1)[0].strip()
            if key in env_vars:
                new_lines.append(f"{key}={env_vars[key]}\n")
                updated_keys.add(key)
                continue
        new_lines.append(line)
    
    # 添加未在模板中的新變量
    for key, value in env_vars.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")
    
    # 寫入文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ 配置已保存到 {env_file.absolute()}")
    print()
    print("⚠️  重要提示：")
    print("  1. .env 文件包含敏感信息，請勿提交到版本控制")
    print("  2. 請妥善保管 JWT_SECRET 和管理員密碼")
    print("  3. 生產環境建議使用環境變量而非 .env 文件")
    print()
    
    return True

def main():
    """主函數"""
    # 切換到腳本所在目錄的父目錄（admin-backend）
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)
    
    try:
        success = setup_env_file()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n❌ 已取消")
        return 1
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

