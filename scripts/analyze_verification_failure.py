#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析验证码失效问题
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin@example.com"
PASSWORD = "changeme123"

def login():
    """登录获取token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_registration_details(token, registration_id):
    """获取注册详情"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/telegram-registration/{registration_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()

def analyze_verification_failure(phone="+639542360349"):
    """分析验证码失效问题"""
    print("=" * 80)
    print("验证码失效问题分析")
    print("=" * 80)
    print(f"手机号: {phone}")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    try:
        token = login()
        headers = {"Authorization": f"Bearer {token}"}
        
        # 获取所有注册记录
        response = requests.get(
            f"{BASE_URL}/telegram-registration/list",
            headers=headers,
            params={"limit": 10}
        )
        response.raise_for_status()
        registrations = response.json()
        
        # 查找匹配的记录
        matching_regs = [
            r for r in registrations 
            if r.get('phone') == phone or r.get('phone') == phone.replace('+', '')
        ]
        
        if not matching_regs:
            print(f"❌ 未找到手机号 {phone} 的注册记录")
            return
        
        # 获取最新的记录
        latest_reg = max(matching_regs, key=lambda x: x.get('created_at', ''))
        reg_id = latest_reg['id']
        
        print(f"📋 找到注册记录: {reg_id}")
        print()
        
        # 获取详细信息
        details = get_registration_details(token, reg_id)
        
        print("=" * 80)
        print("注册记录详细信息")
        print("=" * 80)
        print(f"注册ID: {details.get('registration_id')}")
        print(f"手机号: {details.get('phone')}")
        print(f"状态: {details.get('status')}")
        print(f"服务器: {details.get('node_id')}")
        print(f"创建时间: {details.get('created_at')}")
        print(f"更新时间: {details.get('updated_at')}")
        print(f"Phone Code Hash: {details.get('phone_code_hash')}")
        print(f"错误信息: {details.get('error_message')}")
        print(f"重试次数: {details.get('retry_count', 0)}")
        print()
        
        # 分析可能的原因
        print("=" * 80)
        print("问题分析")
        print("=" * 80)
        
        status = details.get('status')
        phone_code_hash = details.get('phone_code_hash')
        error_message = details.get('error_message', '')
        updated_at = details.get('updated_at')
        created_at = details.get('created_at')
        
        issues = []
        
        # 检查1: 状态是否正确
        if status != 'code_sent':
            issues.append(f"❌ 状态不正确: {status} (应该是 'code_sent')")
        else:
            print("✅ 状态正确: code_sent")
        
        # 检查2: phone_code_hash 是否存在
        if not phone_code_hash:
            issues.append("❌ Phone Code Hash 不存在，验证码无法验证")
        else:
            print(f"✅ Phone Code Hash 存在: {phone_code_hash[:20]}...")
        
        # 检查3: 是否多次点击"开始注册"
        if updated_at and created_at:
            try:
                updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_diff = (updated - created).total_seconds()
                
                # 如果更新时间与创建时间相差很大，可能是多次点击
                if time_diff > 300:  # 5分钟
                    issues.append(f"⚠️  注册记录已存在 {time_diff:.0f} 秒，可能多次点击了'开始注册'")
                    print(f"⚠️  注册记录已存在 {time_diff:.0f} 秒")
            except:
                pass
        
        # 检查4: 错误信息分析
        if error_message:
            print(f"📝 错误信息: {error_message}")
            if '无效' in error_message or 'invalid' in error_message.lower():
                issues.append("❌ 验证码被 Telegram API 标记为无效")
                print("   可能原因:")
                print("   - 验证码已过期（Telegram 验证码有效期通常为几分钟）")
                print("   - Phone Code Hash 不匹配（多次点击'开始注册'会生成新的 hash）")
                print("   - 验证码输入错误")
            elif 'expired' in error_message.lower() or '过期' in error_message:
                issues.append("❌ 验证码已过期")
                print("   可能原因:")
                print("   - Telegram 验证码有效期已过（通常为几分钟）")
                print("   - 验证码生成时间过长")
        
        # 检查5: 重试次数
        retry_count = details.get('retry_count', 0)
        if retry_count > 0:
            print(f"⚠️  重试次数: {retry_count}")
            if retry_count >= 3:
                issues.append(f"❌ 重试次数过多 ({retry_count})，可能触发 Telegram 限制")
        
        print()
        
        # 总结
        print("=" * 80)
        print("问题总结")
        print("=" * 80)
        
        if issues:
            print("发现的问题:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("✅ 未发现明显问题")
        
        print()
        print("=" * 80)
        print("建议解决方案")
        print("=" * 80)
        
        if status != 'code_sent':
            print("1. 重新开始注册流程")
            print("   - 点击'开始注册'重新获取验证码")
            print("   - 确保状态为 'code_sent'")
        
        if not phone_code_hash:
            print("2. Phone Code Hash 缺失")
            print("   - 重新开始注册流程")
            print("   - 确保验证码发送成功")
        
        if '多次点击' in str(issues):
            print("3. 避免多次点击'开始注册'")
            print("   - 每次点击都会生成新的 phone_code_hash")
            print("   - 旧的验证码无法用新的 hash 验证")
            print("   - 等待验证码后再点击，或使用最新的验证码")
        
        if '无效' in error_message or 'invalid' in error_message.lower():
            print("4. 验证码无效")
            print("   - 检查验证码是否正确输入")
            print("   - 验证码可能已过期，重新获取")
            print("   - 确保使用与验证码对应的 phone_code_hash")
        
        print()
        print("=" * 80)
        print("详细调试信息")
        print("=" * 80)
        print(json.dumps(details, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    phone = sys.argv[1] if len(sys.argv) > 1 else "+639542360349"
    analyze_verification_failure(phone)

