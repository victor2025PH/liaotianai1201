#!/usr/bin/env python3
"""
修复 401 认证问题
- 更新后端 CORS 配置，添加生产域名
- 确保 Nginx 传递 Authorization header
- 重启相关服务
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

# 配置路径
BACKEND_ENV_PATH = "/home/ubuntu/liaotian/admin-backend/.env"
NGINX_CONFIG_PATH = "/etc/nginx/sites-available/aikz.usdt2026.cc"
PRODUCTION_DOMAIN = "http://aikz.usdt2026.cc"

def run_command(cmd, check=True, capture_output=False):
    """执行命令"""
    print(f"执行: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        check=check,
        capture_output=capture_output,
        text=True
    )
    if capture_output:
        return result.stdout.strip()
    return result

def backup_file(file_path):
    """备份文件"""
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.bak.{timestamp}"
        shutil.copy2(file_path, backup_path)
        print(f"[OK] 已备份: {backup_path}")
        return backup_path
    return None

def update_cors_config():
    """更新 CORS 配置"""
    print("\n>>> [2] 更新 CORS 配置...")
    
    if not os.path.exists(BACKEND_ENV_PATH):
        print(f"[错误] 文件不存在: {BACKEND_ENV_PATH}")
        return False
    
    # 读取当前配置
    with open(BACKEND_ENV_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cors_found = False
    cors_updated = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith("CORS_ORIGINS="):
            cors_found = True
            # 检查是否已包含生产域名
            if PRODUCTION_DOMAIN in line:
                print("[OK] CORS_ORIGINS 已包含生产域名")
                return True
            else:
                # 追加生产域名
                if line.strip().endswith(","):
                    lines[i] = f"{line.strip()}{PRODUCTION_DOMAIN}\n"
                else:
                    lines[i] = f"{line.strip()},{PRODUCTION_DOMAIN}\n"
                cors_updated = True
                print(f"[OK] 已添加生产域名到 CORS_ORIGINS")
                break
    
    if not cors_found:
        # 添加新行
        lines.append(f"CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,{PRODUCTION_DOMAIN}\n")
        cors_updated = True
        print("[OK] 已添加 CORS_ORIGINS 配置")
    
    if cors_updated:
        # 写入文件
        with open(BACKEND_ENV_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"[OK] 已更新: {BACKEND_ENV_PATH}")
    
    return True

def update_nginx_config():
    """更新 Nginx 配置，确保传递 Authorization header"""
    print("\n>>> [3] 检查 Nginx 配置...")
    
    if not os.path.exists(NGINX_CONFIG_PATH):
        print(f"[错误] 文件不存在: {NGINX_CONFIG_PATH}")
        return False
    
    # 读取当前配置
    with open(NGINX_CONFIG_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已包含 Authorization header
    if "proxy_set_header Authorization" in content:
        print("[OK] Nginx 已配置 Authorization header 传递")
        return True
    
    # 在 /api/ location 中添加 Authorization header
    # 查找 location /api/ 块
    lines = content.split('\n')
    in_api_location = False
    updated = False
    
    for i, line in enumerate(lines):
        if 'location /api/' in line:
            in_api_location = True
        elif in_api_location:
            if line.strip().startswith('location ') or line.strip() == '}':
                in_api_location = False
            elif 'proxy_set_header X-Forwarded-Proto' in line:
                # 在这一行后插入 Authorization header
                indent = len(line) - len(line.lstrip())
                auth_line = ' ' * indent + 'proxy_set_header Authorization $http_authorization;'
                lines.insert(i + 1, auth_line)
                updated = True
                print("[OK] 已添加 Authorization header 传递")
                break
    
    if updated:
        # 写入文件
        with open(NGINX_CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"[OK] 已更新: {NGINX_CONFIG_PATH}")
    
    return True

def test_nginx():
    """测试 Nginx 配置"""
    print("\n>>> [4] 测试 Nginx 配置...")
    try:
        run_command("sudo nginx -t", check=True)
        print("[OK] Nginx 配置测试通过")
        return True
    except subprocess.CalledProcessError:
        print("[错误] Nginx 配置测试失败")
        return False

def reload_nginx():
    """重新加载 Nginx"""
    print("\n>>> [5] 重新加载 Nginx...")
    try:
        run_command("sudo systemctl reload nginx", check=True)
        print("[OK] Nginx 已重新加载")
        return True
    except subprocess.CalledProcessError:
        print("[错误] Nginx 重新加载失败")
        return False

def restart_backend():
    """重启后端服务"""
    print("\n>>> [6] 重启后端服务...")
    try:
        run_command("sudo systemctl restart liaotian-backend", check=True)
        import time
        time.sleep(2)
        
        # 检查服务状态
        result = run_command("sudo systemctl is-active liaotian-backend", capture_output=True)
        if result == "active":
            print("[OK] 后端服务已重启")
            return True
        else:
            print("[错误] 后端服务未运行")
            run_command("sudo systemctl status liaotian-backend --no-pager | head -20", check=False)
            return False
    except subprocess.CalledProcessError:
        print("[错误] 后端服务重启失败")
        return False

def verify_config():
    """验证配置"""
    print("\n>>> [7] 验证配置...")
    
    print("\nCORS_ORIGINS:")
    try:
        result = run_command(f"sudo grep CORS_ORIGINS {BACKEND_ENV_PATH}", capture_output=True)
        print(result)
    except:
        print("未找到 CORS_ORIGINS 配置")
    
    print("\nNginx Authorization header:")
    try:
        result = run_command(f"sudo grep -A 2 'proxy_set_header Authorization' {NGINX_CONFIG_PATH}", capture_output=True)
        if result:
            print(result)
        else:
            print("未找到（可能使用默认传递）")
    except:
        print("检查失败")

def main():
    """主函数"""
    print("=" * 60)
    print("修复 401 认证问题")
    print("=" * 60)
    
    # 检查权限
    if os.geteuid() != 0:
        print("[警告] 需要 root 权限，部分操作可能需要 sudo")
    
    # 1. 备份配置
    print("\n>>> [1] 备份配置...")
    backup_file(BACKEND_ENV_PATH)
    backup_file(NGINX_CONFIG_PATH)
    
    # 2. 更新 CORS 配置
    if not update_cors_config():
        print("[错误] CORS 配置更新失败")
        return 1
    
    # 3. 更新 Nginx 配置
    if not update_nginx_config():
        print("[错误] Nginx 配置更新失败")
        return 1
    
    # 4. 测试 Nginx 配置
    if not test_nginx():
        print("[错误] Nginx 配置测试失败，请手动检查")
        return 1
    
    # 5. 重新加载 Nginx
    if not reload_nginx():
        print("[错误] Nginx 重新加载失败")
        return 1
    
    # 6. 重启后端服务
    if not restart_backend():
        print("[错误] 后端服务重启失败")
        return 1
    
    # 7. 验证配置
    verify_config()
    
    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)
    print("\n下一步：")
    print("1. 在浏览器中访问 http://aikz.usdt2026.cc/login 重新登录")
    print("2. 登录后访问 http://aikz.usdt2026.cc/group-ai/accounts")
    print("3. 检查浏览器控制台，确认 API 请求是否成功")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

