#!/usr/bin/env python3
"""
生成安全的JWT密钥
"""
import secrets
import sys

def generate_jwt_secret(length=64):
    """生成随机JWT密钥"""
    return secrets.token_urlsafe(length)

if __name__ == "__main__":
    secret = generate_jwt_secret()
    print("=" * 60)
    print("JWT密钥生成器")
    print("=" * 60)
    print(f"\n生成的JWT密钥:")
    print(secret)
    print(f"\n长度: {len(secret)} 字符")
    print("\n使用方法:")
    print("1. 复制上面的密钥")
    print("2. 编辑 .env 文件，设置:")
    print(f"   JWT_SECRET={secret}")
    print("3. 重启后端服务: pm2 restart backend")
    print("\n⚠️  请妥善保管此密钥，不要泄露！")
    print("=" * 60)

