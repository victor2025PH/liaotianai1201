import paramiko
import os
from pathlib import Path

# 配置信息
HOST = '165.154.233.55'
USER = 'ubuntu'
PASSWORD = 'Along2025!!!'

# 获取本地公钥
ssh_dir = Path.home() / ".ssh"
pub_key_path = ssh_dir / "id_rsa.pub"

# 如果没有公钥，提示用户生成
if not pub_key_path.exists():
    print(f"❌ 未找到公钥: {pub_key_path}")
    print("请先在终端运行: ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa")
    exit(1)

with open(pub_key_path, 'r') as f:
    public_key = f.read().strip()

print(f"正在连接 {HOST} ...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    print("正在配置免密登录...")
    
    # 写入 authorized_keys
    cmd = (
        'mkdir -p ~/.ssh && '
        'chmod 700 ~/.ssh && '
        f'echo "{public_key}" >> ~/.ssh/authorized_keys && '
        'chmod 600 ~/.ssh/authorized_keys'
    )
    
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print("✅ 公钥上传成功！免密登录已配置。")
        print("\n正在验证连接...")
        stdin, stdout, stderr = client.exec_command("echo '🎉 验证成功！主机名：' && hostname")
        print(stdout.read().decode())
    else:
        print("❌ 配置失败:", stderr.read().decode())
        
    client.close()

except Exception as e:
    print(f"❌ 连接失败: {e}")