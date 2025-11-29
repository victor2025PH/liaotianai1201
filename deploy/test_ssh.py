# -*- coding: utf-8 -*-
import paramiko

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("测试 SSH 连接...")
try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("SSH 连接成功!")
    
    stdin, stdout, stderr = ssh.exec_command("echo 'Hello from server'")
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"服务器响应: {output}")
    
    ssh.close()
    print("连接测试完成")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

