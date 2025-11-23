#!/usr/bin/env python3
"""
測試通過SSH執行sudo命令
"""
import paramiko
import time

def test_sudo_command():
    """測試sudo命令執行"""
    host = '165.154.254.99'
    user = 'ubuntu'
    password = 'Along2025!!!'
    
    print(f"連接 {user}@{host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=5)
    
    # 測試1: 檢查服務是否存在
    print("\n[1] 檢查服務是否存在...")
    stdin, stdout, stderr = ssh.exec_command('systemctl list-units --all --type=service | grep -E "(group-ai|telegram)"')
    services = stdout.read().decode('utf-8')
    errors = stderr.read().decode('utf-8')
    print(f"服務列表:\n{services}")
    if errors:
        print(f"錯誤: {errors}")
    
    # 測試2: 測試sudo是否需要密碼
    print("\n[2] 測試sudo無密碼執行...")
    stdin, stdout, stderr = ssh.exec_command('sudo -n echo "sudo works" 2>&1')
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    print(f"退出碼: {exit_code}")
    print(f"輸出: {output}")
    if error:
        print(f"錯誤: {error}")
    
    # 測試3: 使用echo密碼到sudo
    print("\n[3] 測試通過echo密碼執行sudo...")
    cmd = f'echo "{password}" | sudo -S systemctl list-units --type=service | head -5'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    print(f"退出碼: {exit_code}")
    print(f"輸出:\n{output}")
    if error:
        print(f"錯誤: {error}")
    
    # 測試4: 使用stdin傳遞密碼
    print("\n[4] 測試通過stdin傳遞密碼...")
    stdin, stdout, stderr = ssh.exec_command('sudo -S systemctl list-units --type=service | head -5')
    stdin.write(f'{password}\n')
    stdin.flush()
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    print(f"退出碼: {exit_code}")
    print(f"輸出:\n{output}")
    if error:
        print(f"錯誤: {error}")
    
    ssh.close()
    print("\n測試完成")

if __name__ == "__main__":
    test_sudo_command()

