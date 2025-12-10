#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接修复 Nginx 配置
"""

import json
import paramiko
import sys
from pathlib import Path

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_config():
    """加载服务器配置"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    config_path = project_root / "data" / "master_config.json"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    manila_config = config.get('servers', {}).get('manila', {})
    
    return {
        'host': '165.154.233.55',
        'user': manila_config.get('user', 'ubuntu'),
        'password': manila_config.get('password', 'Along2025!!!'),
    }

def main():
    """主函数"""
    print("="*70)
    print("🔧 直接修复 Nginx 配置")
    print("="*70)
    print()
    
    config = load_config()
    client = None
    sftp = None
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(config['host'], username=config['user'], password=config['password'], timeout=30)
        print("✅ SSH 连接成功!")
        
        sftp = client.open_sftp()
        
        # 1. 查找配置文件
        print("\n" + "="*70)
        print("第一步：查找 Nginx 配置文件")
        print("="*70)
        
        stdin, stdout, stderr = client.exec_command("sudo nginx -T 2>/dev/null | grep -B 10 'server_name.*aikz.usdt2026.cc' | grep '# configuration file' | tail -1 | sed 's/# configuration file //'", get_pty=True)
        config_file = stdout.read().decode().strip()
        
        if not config_file:
            # 尝试查找启用的配置
            stdin, stdout, stderr = client.exec_command("ls -la /etc/nginx/sites-enabled/ | grep aikz | awk '{print $NF}'", get_pty=True)
            symlink = stdout.read().decode().strip()
            if symlink:
                stdin, stdout, stderr = client.exec_command(f"readlink -f /etc/nginx/sites-enabled/{symlink}", get_pty=True)
                config_file = stdout.read().decode().strip()
        
        if not config_file:
            config_file = "/etc/nginx/sites-available/aikz.conf"
        
        print(f"✅ 配置文件: {config_file}")
        
        # 2. 读取当前配置
        print("\n" + "="*70)
        print("第二步：读取当前配置")
        print("="*70)
        
        stdin, stdout, stderr = client.exec_command(f"sudo cat {config_file}", get_pty=True)
        current_config = stdout.read().decode()
        print(current_config)
        
        # 3. 备份配置
        print("\n" + "="*70)
        print("第三步：备份配置")
        print("="*70)
        
        stdin, stdout, stderr = client.exec_command(f"sudo cp {config_file} {config_file}.backup.$(date +%Y%m%d_%H%M%S)", get_pty=True)
        stdout.channel.recv_exit_status()
        print("✅ 配置已备份")
        
        # 4. 写入新配置
        print("\n" + "="*70)
        print("第四步：写入新的简化配置")
        print("="*70)
        
        simple_config = '''server {
    listen 80;
    server_name aikz.usdt2026.cc;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
    }
}
'''
        
        temp_file = '/tmp/aikz_nginx_simple.conf'
        with sftp.open(temp_file, 'w') as f:
            f.write(simple_config)
        
        stdin, stdout, stderr = client.exec_command(f"sudo mv {temp_file} {config_file} && sudo chmod 644 {config_file}", get_pty=True)
        stdout.channel.recv_exit_status()
        print("✅ 新配置已写入")
        
        # 5. 禁用冲突配置
        print("\n" + "="*70)
        print("第五步：禁用冲突配置")
        print("="*70)
        
        stdin, stdout, stderr = client.exec_command("ls -la /etc/nginx/sites-enabled/ | grep -v 'aikz.conf' | grep -E 'aikz|liaotian' | awk '{print $NF}'", get_pty=True)
        conflicts = [line.strip() for line in stdout.read().decode().split('\n') if line.strip()]
        
        if conflicts:
            for conflict in conflicts:
                stdin, stdout, stderr = client.exec_command(f"sudo rm -f /etc/nginx/sites-enabled/{conflict}", get_pty=True)
                print(f"✅ 已禁用: {conflict}")
        else:
            print("✅ 无冲突配置")
        
        # 6. 测试配置
        print("\n" + "="*70)
        print("第六步：测试 Nginx 配置")
        print("="*70)
        
        stdin, stdout, stderr = client.exec_command("sudo nginx -t", get_pty=True)
        test_output = stdout.read().decode()
        error_output = stderr.read().decode()
        print(test_output)
        if error_output:
            print(f"错误: {error_output}")
        
        if "syntax is ok" not in test_output:
            print("❌ Nginx 配置测试失败")
            return 1
        
        # 7. 重载 Nginx
        print("\n" + "="*70)
        print("第七步：重载 Nginx")
        print("="*70)
        
        stdin, stdout, stderr = client.exec_command("sudo systemctl reload nginx", get_pty=True)
        stdout.channel.recv_exit_status()
        print("✅ Nginx 已重载")
        
        # 8. 显示最终配置
        print("\n" + "="*70)
        print("最终 Nginx 配置")
        print("="*70)
        
        stdin, stdout, stderr = client.exec_command(f"sudo cat {config_file}", get_pty=True)
        final_config = stdout.read().decode()
        print(final_config)
        
        # 9. 验证
        print("\n" + "="*70)
        print("验证结果")
        print("="*70)
        
        import time
        time.sleep(2)
        
        stdin, stdout, stderr = client.exec_command("curl -s -o /dev/null -w '%{http_code}' http://aikz.usdt2026.cc/ 2>&1", get_pty=True)
        root_status = stdout.read().decode().strip()
        print(f"根路径 HTTP 状态: {root_status}")
        
        stdin, stdout, stderr = client.exec_command("curl -s -o /dev/null -w '%{http_code}' http://aikz.usdt2026.cc/_next/static/chunks/00d08e8cd5345827.js 2>&1", get_pty=True)
        chunk_status = stdout.read().decode().strip()
        print(f"Chunks 文件 HTTP 状态: {chunk_status}")
        
        print("\n" + "="*70)
        print("✅ 修复完成！")
        print("="*70)
        print("\n📝 下一步:")
        print("   1. 清除浏览器缓存 (Ctrl+Shift+Delete)")
        print("   2. 刷新页面: http://aikz.usdt2026.cc")
        print("   3. 如果 chunks 文件仍然 404，需要检查 Next.js 服务")
        print()
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if sftp:
            sftp.close()
        if client:
            client.close()
            print("🔌 SSH 连接已关闭")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

