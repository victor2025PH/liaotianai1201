#!/usr/bin/env python3
"""
更新安全配置脚本
帮助用户更新JWT_SECRET和管理员密码
"""
import sys
import os
import secrets
from pathlib import Path
import getpass

def generate_jwt_secret(length=64):
    """生成随机JWT密钥"""
    return secrets.token_urlsafe(length)

def update_env_file(env_path: Path, jwt_secret: str = None, admin_password: str = None):
    """更新.env文件"""
    if not env_path.exists():
        print(f"⚠ .env文件不存在: {env_path}")
        print("创建新的.env文件...")
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.touch()
    
    # 读取现有内容
    lines = []
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    # 更新或添加配置
    updated = False
    jwt_updated = False
    password_updated = False
    
    new_lines = []
    for line in lines:
        stripped = line.strip()
        
        # 更新JWT_SECRET
        if stripped.startswith('JWT_SECRET=') and jwt_secret:
            new_lines.append(f'JWT_SECRET={jwt_secret}\n')
            jwt_updated = True
            updated = True
        # 更新管理员密码
        elif stripped.startswith('ADMIN_DEFAULT_PASSWORD=') and admin_password:
            new_lines.append(f'ADMIN_DEFAULT_PASSWORD={admin_password}\n')
            password_updated = True
            updated = True
        else:
            new_lines.append(line)
    
    # 如果不存在，添加新配置
    if jwt_secret and not jwt_updated:
        new_lines.append(f'JWT_SECRET={jwt_secret}\n')
        updated = True
    
    if admin_password and not password_updated:
        new_lines.append(f'ADMIN_DEFAULT_PASSWORD={admin_password}\n')
        updated = True
    
    # 写入文件
    if updated:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"✓ .env文件已更新: {env_path}")
        return True
    else:
        print("⚠ 没有需要更新的配置")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("安全配置更新工具")
    print("=" * 60)
    
    # 确定.env文件路径
    script_dir = Path(__file__).parent.parent.parent
    env_path = script_dir / "admin-backend" / ".env"
    
    print(f"\n.env文件路径: {env_path}")
    
    # 检查当前配置
    current_jwt = None
    current_password = None
    
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('JWT_SECRET='):
                    current_jwt = line.split('=', 1)[1].strip()
                elif line.startswith('ADMIN_DEFAULT_PASSWORD='):
                    current_password = line.split('=', 1)[1].strip()
    
    # 检查JWT_SECRET
    needs_jwt_update = False
    if not current_jwt or current_jwt == "change_me":
        needs_jwt_update = True
        print("\n⚠ 发现JWT_SECRET使用默认值或未设置")
    
    # 检查管理员密码
    needs_password_update = False
    if not current_password or current_password == "changeme123":
        needs_password_update = True
        print("⚠ 发现ADMIN_DEFAULT_PASSWORD使用默认值")
    
    if not needs_jwt_update and not needs_password_update:
        print("\n✓ 安全配置已是最新，无需更新")
        return 0
    
    # 生成新的JWT密钥
    new_jwt_secret = None
    if needs_jwt_update:
        print("\n生成新的JWT密钥...")
        new_jwt_secret = generate_jwt_secret()
        print(f"✓ 已生成新的JWT密钥 (长度: {len(new_jwt_secret)})")
    
    # 获取新的管理员密码
    new_password = None
    if needs_password_update:
        print("\n设置新的管理员密码:")
        print("(密码要求: 至少8个字符，建议包含大小写字母、数字和特殊字符)")
        while True:
            password1 = getpass.getpass("请输入新密码: ")
            if len(password1) < 8:
                print("⚠ 密码长度至少8个字符，请重新输入")
                continue
            password2 = getpass.getpass("请再次输入密码确认: ")
            if password1 != password2:
                print("⚠ 两次输入的密码不一致，请重新输入")
                continue
            new_password = password1
            break
        print("✓ 密码已设置")
    
    # 确认更新
    print("\n" + "=" * 60)
    print("准备更新以下配置:")
    if new_jwt_secret:
        print(f"  - JWT_SECRET: {new_jwt_secret[:20]}...")
    if new_password:
        print(f"  - ADMIN_DEFAULT_PASSWORD: {'*' * len(new_password)}")
    print("=" * 60)
    
    confirm = input("\n确认更新? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("操作已取消")
        return 1
    
    # 更新.env文件
    success = update_env_file(env_path, new_jwt_secret, new_password)
    
    if success:
        print("\n" + "=" * 60)
        print("更新完成！")
        print("=" * 60)
        print("\n下一步:")
        print("1. 重启后端服务以应用新配置:")
        print("   pm2 restart backend")
        print("\n2. 验证配置:")
        print("   python3 scripts/server/system_health_check.py")
        print("\n⚠️  请妥善保管JWT_SECRET，不要泄露！")
        return 0
    else:
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)

