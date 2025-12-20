#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成安全的随机密钥（用于 JWT_SECRET 等配置）
适用于 Windows 和 Linux
"""
import secrets
import sys

def generate_secret_key(length=64):
    """生成 URL 安全的随机密钥"""
    return secrets.token_urlsafe(length)

if __name__ == "__main__":
    # 默认生成 64 字符的密钥
    key_length = 64
    if len(sys.argv) > 1:
        try:
            key_length = int(sys.argv[1])
        except ValueError:
            print(f"错误：'{sys.argv[1]}' 不是有效的数字")
            print(f"使用方法: python {sys.argv[0]} [长度]")
            sys.exit(1)
    
    secret_key = generate_secret_key(key_length)
    print(secret_key)
