#!/usr/bin/env python3
"""
配置通知渠道脚本
帮助用户配置邮件、Telegram、Webhook通知
"""
import sys
import os
from pathlib import Path
import getpass

def update_env_file(env_path: Path, updates: dict):
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
    updated_keys = set()
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        updated = False
        
        for key, value in updates.items():
            if stripped.startswith(f'{key}='):
                new_lines.append(f'{key}={value}\n')
                updated_keys.add(key)
                updated = True
                break
        
        if not updated:
            new_lines.append(line)
    
    # 添加新配置
    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f'{key}={value}\n')
    
    # 写入文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✓ .env文件已更新: {env_path}")
    return True

def configure_email(env_path: Path):
    """配置邮件通知"""
    print("\n" + "=" * 60)
    print("配置邮件通知")
    print("=" * 60)
    
    enabled = input("启用邮件通知? (yes/no, 默认: no): ").strip().lower()
    if enabled not in ['yes', 'y']:
        updates = {
            'EMAIL_ENABLED': 'false'
        }
        update_env_file(env_path, updates)
        print("邮件通知已禁用")
        return
    
    smtp_host = input("SMTP服务器地址 (例如: smtp.gmail.com): ").strip()
    smtp_port = input("SMTP端口 (默认: 587): ").strip() or "587"
    smtp_user = input("SMTP用户名 (邮箱地址): ").strip()
    smtp_password = getpass.getpass("SMTP密码: ")
    email_from = input("发件人邮箱地址: ").strip()
    
    updates = {
        'EMAIL_ENABLED': 'true',
        'SMTP_HOST': smtp_host,
        'SMTP_PORT': smtp_port,
        'SMTP_USER': smtp_user,
        'SMTP_PASSWORD': smtp_password,
        'EMAIL_FROM': email_from
    }
    
    update_env_file(env_path, updates)
    print("✓ 邮件通知配置完成")

def configure_telegram(env_path: Path):
    """配置Telegram通知"""
    print("\n" + "=" * 60)
    print("配置Telegram通知")
    print("=" * 60)
    
    enabled = input("启用Telegram通知? (yes/no, 默认: no): ").strip().lower()
    if enabled not in ['yes', 'y']:
        updates = {
            'TELEGRAM_BOT_TOKEN': '',
            'TELEGRAM_CHAT_ID': ''
        }
        update_env_file(env_path, updates)
        print("Telegram通知已禁用")
        return
    
    print("\n如何获取Telegram Bot Token:")
    print("1. 在Telegram中搜索 @BotFather")
    print("2. 发送 /newbot 命令创建新bot")
    print("3. 按照提示设置bot名称和用户名")
    print("4. BotFather会返回bot token")
    print()
    
    bot_token = input("Telegram Bot Token: ").strip()
    
    print("\n如何获取Chat ID:")
    print("1. 在Telegram中搜索 @userinfobot")
    print("2. 发送任意消息给该bot")
    print("3. 它会返回您的Chat ID")
    print()
    
    chat_id = input("Telegram Chat ID: ").strip()
    
    updates = {
        'TELEGRAM_BOT_TOKEN': bot_token,
        'TELEGRAM_CHAT_ID': chat_id
    }
    
    update_env_file(env_path, updates)
    print("✓ Telegram通知配置完成")

def configure_webhook(env_path: Path):
    """配置Webhook通知"""
    print("\n" + "=" * 60)
    print("配置Webhook通知")
    print("=" * 60)
    
    enabled = input("启用Webhook通知? (yes/no, 默认: no): ").strip().lower()
    if enabled not in ['yes', 'y']:
        updates = {
            'WEBHOOK_ENABLED': 'false',
            'WEBHOOK_URL': ''
        }
        update_env_file(env_path, updates)
        print("Webhook通知已禁用")
        return
    
    webhook_url = input("Webhook URL (例如: https://hooks.slack.com/services/...): ").strip()
    
    if not webhook_url.startswith('http'):
        print("⚠ Webhook URL应该以 http:// 或 https:// 开头")
        return
    
    updates = {
        'WEBHOOK_ENABLED': 'true',
        'WEBHOOK_URL': webhook_url
    }
    
    update_env_file(env_path, updates)
    print("✓ Webhook通知配置完成")

def main():
    """主函数"""
    print("=" * 60)
    print("通知渠道配置工具")
    print("=" * 60)
    
    # 确定.env文件路径
    script_dir = Path(__file__).parent.parent.parent
    env_path = script_dir / "admin-backend" / ".env"
    
    print(f"\n.env文件路径: {env_path}")
    
    while True:
        print("\n" + "=" * 60)
        print("请选择要配置的通知渠道:")
        print("1. 邮件通知 (Email)")
        print("2. Telegram通知")
        print("3. Webhook通知")
        print("4. 完成配置")
        print("=" * 60)
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == '1':
            configure_email(env_path)
        elif choice == '2':
            configure_telegram(env_path)
        elif choice == '3':
            configure_webhook(env_path)
        elif choice == '4':
            break
        else:
            print("无效的选择，请重新输入")
    
    print("\n" + "=" * 60)
    print("配置完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 重启后端服务以应用新配置:")
    print("   pm2 restart backend")
    print("\n2. 测试通知功能（通过告警管理页面）")
    print("\n⚠️  请妥善保管敏感信息（密码、Token等），不要泄露！")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)

