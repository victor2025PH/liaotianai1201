#!/usr/bin/env python3
"""
直接在服务器上修复代码，添加 UPSERT 功能
"""
import paramiko
import io

SERVER_IP = "165.154.233.55"
USERNAME = "ubuntu"
REMOTE_FILE = "~/liaotian/admin-backend/app/api/group_ai/accounts.py"

# 读取本地修改后的文件
LOCAL_FILE = "admin-backend/app/api/group_ai/accounts.py"

def read_local_file():
    """读取本地文件"""
    with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def upload_to_server(content):
    """通过 SSH 上传文件到服务器"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 连接到服务器（使用密钥认证）
        ssh.connect(SERVER_IP, username=USERNAME, timeout=10)
        
        # 备份原文件
        sftp = ssh.open_sftp()
        remote_path = REMOTE_FILE.replace("~", "/home/ubuntu")
        
        # 读取原文件并备份
        try:
            with sftp.open(remote_path, 'r') as f:
                backup_content = f.read().decode('utf-8')
            
            backup_path = f"{remote_path}.bak"
            with sftp.open(backup_path, 'w') as f:
                f.write(backup_content.encode('utf-8'))
            print(f"✓ 已备份文件到: {backup_path}")
        except Exception as e:
            print(f"⚠ 备份失败（可能文件不存在）: {e}")
        
        # 写入新文件
        with sftp.open(remote_path, 'w') as f:
            f.write(content.encode('utf-8'))
        
        print(f"✓ 文件已上传: {remote_path}")
        print(f"✓ 文件大小: {len(content)} 字节")
        print(f"✓ 包含 UPSERT: {'UPSERT 模式' in content}")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    print("读取本地文件...")
    content = read_local_file()
    print(f"本地文件大小: {len(content)} 字节")
    
    print("\n上传到服务器...")
    if upload_to_server(content):
        print("\n✓ 上传成功！")
        print("请重启后端服务以使更改生效。")
    else:
        print("\n✗ 上传失败！")
        exit(1)
