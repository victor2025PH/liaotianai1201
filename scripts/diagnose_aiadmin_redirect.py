#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断 aiadmin.usdt2026.cc 跳转错误问题
"""

import subprocess
import sys
import re
from pathlib import Path

NGINX_CONFIG = "/etc/nginx/sites-available/aiadmin.usdt2026.cc"
NGINX_ENABLED = "/etc/nginx/sites-enabled/aiadmin.usdt2026.cc"
DOMAIN = "aiadmin.usdt2026.cc"

def run_cmd(cmd, check=False):
    """执行命令"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 60)
    print("诊断 aiadmin.usdt2026.cc 跳转错误")
    print("=" * 60)
    print()
    
    # 1. 检查 Nginx 配置文件
    print("1. 检查 Nginx 配置文件")
    print("-" * 60)
    config_path = Path(NGINX_CONFIG)
    if config_path.exists():
        print(f"✅ 配置文件存在: {NGINX_CONFIG}")
        print()
        print("当前配置内容：")
        print("-" * 60)
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
        print("-" * 60)
        print()
        
        # 检查 location / 的 proxy_pass
        match = re.search(r'location\s+/\s*\{[^}]*proxy_pass\s+([^;]+);', content, re.DOTALL)
        if match:
            proxy_pass = match.group(1).strip()
            print(f"找到 location / 的 proxy_pass: {proxy_pass}")
            port_match = re.search(r':(\d+)', proxy_pass)
            if port_match:
                port = port_match.group(1)
                print(f"检测到的代理端口: {port}")
                if port == "3007":
                    print("✅ 端口正确 (应该是 3007)")
                else:
                    print(f"❌ 端口错误！应该是 3007，但当前是 {port}")
            else:
                print("⚠️  无法从 proxy_pass 中提取端口号")
        else:
            print("❌ 未找到 location / 的 proxy_pass 配置")
    else:
        print(f"❌ 配置文件不存在: {NGINX_CONFIG}")
    
    # 检查软链接
    enabled_path = Path(NGINX_ENABLED)
    if enabled_path.exists():
        if enabled_path.is_symlink():
            link_target = enabled_path.readlink()
            print(f"✅ 软链接存在: {NGINX_ENABLED} -> {link_target}")
            if str(link_target) == NGINX_CONFIG or str(link_target.absolute()) == config_path.absolute():
                print("✅ 软链接指向正确")
            else:
                print(f"❌ 软链接指向错误！应该指向: {NGINX_CONFIG}")
        else:
            print(f"⚠️  {NGINX_ENABLED} 存在但不是软链接")
    else:
        print(f"❌ 软链接不存在: {NGINX_ENABLED}")
    
    print()
    
    # 2. 检查 PM2 进程
    print("2. 检查 PM2 进程状态")
    print("-" * 60)
    success, output, _ = run_cmd("pm2 list")
    if success:
        lines = output.split('\n')
        found_admin = False
        for line in lines:
            if 'sites-admin-frontend' in line:
                print(line)
                found_admin = True
        if not found_admin:
            print("❌ 未找到 sites-admin-frontend 进程")
        print()
        print("所有前端相关进程：")
        for line in lines[:25]:
            if 'frontend' in line.lower() or 'id' in line.lower() or 'name' in line.lower():
                print(line)
    else:
        print("⚠️  无法执行 pm2 list")
    
    print()
    
    # 3. 检查端口占用
    print("3. 检查端口占用情况")
    print("-" * 60)
    ports = [3007, 8000, 3003, 3001, 3002]
    for port in ports:
        # 尝试使用 lsof
        success, output, _ = run_cmd(f"sudo lsof -ti:{port}", check=False)
        if success and output.strip():
            pid = output.strip()
            # 获取进程信息
            _, proc_info, _ = run_cmd(f"ps -p {pid} -o comm= 2>/dev/null || ps -p {pid} -o args= 2>/dev/null", check=False)
            print(f"端口 {port}: 被进程 {pid} ({proc_info.strip()}) 占用")
        else:
            # 尝试使用 ss
            success, output, _ = run_cmd(f"sudo ss -tlnp | grep ':{port} '", check=False)
            if success and output.strip():
                print(f"端口 {port}: 被占用")
                print(f"  {output.strip()[:100]}")
            else:
                print(f"端口 {port}: 未被占用")
    
    print()
    
    # 4. 检查服务实际响应
    print("4. 检查服务实际响应")
    print("-" * 60)
    
    # 测试端口 3007
    print("测试本地端口 3007（管理后台前端）：")
    success, output, _ = run_cmd("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3007 2>&1", check=False)
    if success:
        http_code = output.strip()
        if http_code == "200":
            print(f"✅ 端口 3007 响应正常 (HTTP {http_code})")
            # 获取内容预览
            _, content, _ = run_cmd("curl -s http://127.0.0.1:3007 2>&1 | head -c 200", check=False)
            print(f"响应内容预览: {content[:200]}...")
            
            # 检查内容特征
            _, full_content, _ = run_cmd("curl -s http://127.0.0.1:3007 2>&1", check=False)
            if '智控王' in full_content or 'aizkw' in full_content.lower():
                print("❌ 警告：端口 3007 返回的是 aizkw 网站内容！")
            elif '三个展示网站管理后台' in full_content or 'sites-admin' in full_content.lower():
                print("✅ 端口 3007 返回的是管理后台内容")
            else:
                print("⚠️  无法识别端口 3007 的内容类型")
        else:
            print(f"❌ 端口 3007 响应异常 (HTTP {http_code})")
    else:
        print("❌ 无法连接到端口 3007")
    
    print()
    
    # 测试端口 3003
    print("测试本地端口 3003（aizkw 前端）：")
    success, output, _ = run_cmd("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3003 2>&1", check=False)
    if success:
        http_code = output.strip()
        if http_code == "200":
            print(f"✅ 端口 3003 响应正常 (HTTP {http_code})")
            _, content, _ = run_cmd("curl -s http://127.0.0.1:3003 2>&1 | head -c 200", check=False)
            print(f"响应内容预览: {content[:200]}...")
        else:
            print(f"⚠️  端口 3003 响应异常 (HTTP {http_code})")
    
    print()
    
    # 测试域名
    print("5. 检查域名实际响应")
    print("-" * 60)
    print(f"测试 {DOMAIN}：")
    success, output, _ = run_cmd(f"curl -s -o /dev/null -w '%{{http_code}}' http://{DOMAIN} 2>&1", check=False)
    if success:
        http_code = output.strip()
        print(f"HTTP 状态码: {http_code}")
        
        if http_code == "200":
            _, domain_content, _ = run_cmd(f"curl -s http://{DOMAIN} 2>&1", check=False)
            print("响应内容预览（前300字符）：")
            print(domain_content[:300])
            print()
            
            # 检查内容特征
            if '智控王' in domain_content or 'aizkw' in domain_content.lower() or '数字霸权' in domain_content:
                print("❌ 发现 aizkw 网站内容！域名指向了错误的网站")
            else:
                print("✅ 未发现 aizkw 网站内容")
            
            if '三个展示网站管理后台' in domain_content or 'sites-admin' in domain_content.lower() or '站点概览' in domain_content:
                print("✅ 发现管理后台内容")
            else:
                print("❌ 未发现管理后台内容")
    
    print()
    
    # 6. 检查 Nginx 配置语法
    print("6. 检查 Nginx 配置语法")
    print("-" * 60)
    success, output, error = run_cmd("sudo nginx -t", check=False)
    if success:
        print("✅ Nginx 配置语法正确")
        print(output)
    else:
        print("❌ Nginx 配置语法错误")
        print(error)
    
    print()
    print("=" * 60)
    print("诊断完成")
    print("=" * 60)
    print()
    print("根据以上信息，检查：")
    print("1. Nginx location / 的 proxy_pass 是否指向 3007 端口")
    print("2. 端口 3007 是否有服务在运行，且返回的是管理后台内容")
    print("3. PM2 中 sites-admin-frontend 是否正常运行")
    print("4. 域名响应内容是否匹配管理后台（而不是 aizkw 网站）")

if __name__ == "__main__":
    main()

