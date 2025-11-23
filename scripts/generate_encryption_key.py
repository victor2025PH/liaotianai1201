#!/usr/bin/env python3
"""
生成 Session 文件加密密钥工具
"""
from cryptography.fernet import Fernet
import sys

def main():
    """生成并输出加密密钥"""
    key = Fernet.generate_key()
    key_str = key.decode('utf-8')
    
    print("=" * 60)
    print("Session 文件加密密钥生成工具")
    print("=" * 60)
    print()
    print("生成的加密密钥（复制到 .env 文件的 SESSION_ENCRYPTION_KEY）:")
    print()
    print(key_str)
    print()
    print("=" * 60)
    print("使用说明:")
    print("1. 将上面的密钥复制到 .env 文件中:")
    print("   SESSION_ENCRYPTION_KEY=" + key_str)
    print()
    print("2. 启用加密存储:")
    print("   SESSION_ENCRYPTION_ENABLED=true")
    print()
    print("3. 重启服务以应用配置")
    print("=" * 60)
    
    # 如果提供了输出文件参数，保存到文件
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        with open(output_file, 'w') as f:
            f.write(key_str)
        print(f"\n密钥已保存到: {output_file}")
        print("⚠️  请妥善保管此文件，不要提交到版本控制系统！")

if __name__ == "__main__":
    main()

