#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查服务器上的session文件
"""
import paramiko
import sys

def check_server_files():
    """检查服务器上的session文件"""
    host = "165.154.254.99"
    user = "ubuntu"
    password = "Along2025!!!"
    deploy_dir = "/home/ubuntu"
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=10)
        
        print(f"\n{'='*60}")
        print(f"检查服务器: {host}")
        print(f"{'='*60}\n")
        
        # 检查sessions目录是否存在
        sessions_dir = f"{deploy_dir}/sessions"
        print(f"1. 检查目录: {sessions_dir}")
        stdin, stdout, stderr = ssh.exec_command(f'test -d "{sessions_dir}" && echo "exists" || echo "not_exists"')
        dir_check = stdout.read().decode().strip()
        print(f"   结果: {dir_check}\n")
        
        if "exists" in dir_check:
            # 列出目录内容
            print(f"2. 列出目录内容:")
            stdin, stdout, stderr = ssh.exec_command(f'ls -la {sessions_dir}/ 2>&1')
            dir_listing = stdout.read().decode()
            if dir_listing:
                print(dir_listing)
            else:
                print("   (空)")
            print()
            
            # 查找session文件
            print(f"3. 查找session文件:")
            stdin, stdout, stderr = ssh.exec_command(f'find {sessions_dir} -name "*.session" -type f 2>&1')
            find_files = stdout.read().decode().strip()
            if find_files:
                files = find_files.split('\n')
                print(f"   找到 {len(files)} 个文件:")
                for f in files:
                    if f.strip():
                        print(f"   - {f}")
            else:
                print("   未找到session文件")
            print()
            
            # 使用ls命令查找
            print(f"4. 使用ls命令查找:")
            stdin, stdout, stderr = ssh.exec_command(f'ls -1 {sessions_dir}/*.session 2>&1')
            ls_files = stdout.read().decode().strip()
            if ls_files and "No such file" not in ls_files:
                files = ls_files.split('\n')
                print(f"   找到 {len(files)} 个文件:")
                for f in files:
                    if f.strip():
                        print(f"   - {f}")
            else:
                print("   未找到session文件")
        else:
            # 尝试查找sessions目录
            print(f"2. 目录不存在，尝试查找sessions目录...")
            stdin, stdout, stderr = ssh.exec_command(f'find {deploy_dir} -type d -name "sessions" 2>&1 | head -5')
            alt_dirs = stdout.read().decode().strip()
            if alt_dirs:
                print(f"   找到可能的sessions目录:")
                for d in alt_dirs.split('\n'):
                    if d.strip():
                        print(f"   - {d}")
            else:
                print("   未找到sessions目录")
            
            # 列出deploy_dir下的所有目录
            print(f"\n3. 列出 {deploy_dir} 下的目录:")
            stdin, stdout, stderr = ssh.exec_command(f'ls -d {deploy_dir}/*/ 2>&1 | head -10')
            all_dirs = stdout.read().decode().strip()
            if all_dirs:
                print(all_dirs)
            else:
                print("   (无)")
        
        # 在整个deploy_dir中查找session文件
        print(f"\n5. 在整个 {deploy_dir} 中查找session文件:")
        stdin, stdout, stderr = ssh.exec_command(f'find {deploy_dir} -name "*.session" -type f 2>&1 | head -20')
        all_files = stdout.read().decode().strip()
        if all_files:
            files = all_files.split('\n')
            print(f"   找到 {len(files)} 个文件:")
            for f in files:
                if f.strip():
                    print(f"   - {f}")
        else:
            print("   未找到session文件")
        
        ssh.close()
        print(f"\n{'='*60}")
        print("检查完成")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    check_server_files()

