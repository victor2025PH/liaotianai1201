# -*- coding: utf-8 -*-
"""最终修复 WebSocket - 确保配置正确处理路径参数"""
import paramiko
import sys
import io
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

def exec_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output.strip(), error.strip()

print("=" * 60)
print("最终修复 WebSocket 配置")
print("=" * 60)
print()

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] 已连接\n")
    
    # 1. 检查并修复重复配置
    print(">>> [1] 检查配置...")
    output, _ = exec_cmd(ssh, "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    count = int(output or "0")
    print(f"Location 块数量: {count}")
    
    if count > 1:
        print("修复重复配置...")
        exec_cmd(ssh, "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.final")
        
        fix_code = '''import re
f=open('/etc/nginx/sites-available/aikz.usdt2026.cc','r',encoding='utf-8')
lines=f.readlines()
f.close()
idx=[i for i,l in enumerate(lines) if 'location /api/v1/notifications/ws' in l]
if len(idx)>1:
    for i in reversed(idx[1:]):
        s=i
        for j in range(max(0,i-3),i):
            if '# WebSocket' in lines[j] or ('#' in lines[j] and 'WebSocket' in lines[j]):
                s=j
                break
        b=0
        e=i
        f=False
        for j in range(i,len(lines)):
            if '{' in lines[j]:
                b+=lines[j].count('{')
                f=True
            if '}' in lines[j]:
                b-=lines[j].count('}')
                if f and b==0:
                    e=j
                    break
        lines=lines[:s]+lines[e+1:]
    with open('/etc/nginx/sites-available/aikz.usdt2026.cc','w',encoding='utf-8') as f:
        f.writelines(lines)
    print('已删除',len(idx)-1,'个重复块')
else:
    print('无需修复')
'''
        
        sftp = ssh.open_sftp()
        f = sftp.file('/tmp/fix_final.py', 'w')
        f.write(fix_code)
        f.close()
        sftp.close()
        
        output, _ = exec_cmd(ssh, "sudo python3 /tmp/fix_final.py")
        print(output)
        exec_cmd(ssh, "rm /tmp/fix_final.py")
    
    # 2. 检查 WebSocket 配置是否正确（需要支持路径参数）
    print("\n>>> [2] 检查 WebSocket 配置...")
    output, _ = exec_cmd(ssh, "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    print(output)
    
    # 检查 proxy_pass 是否正确（应该包含路径，以便传递路径参数）
    if "proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;" in output:
        print("\n[警告] proxy_pass 配置可能有问题，需要包含路径参数")
        print("当前配置可能无法正确传递 user_email 参数")
        print("建议修改为：proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws/;")
        print("（注意末尾的斜杠）")
    
    # 3. 测试配置
    print("\n>>> [3] 测试配置...")
    output, _ = exec_cmd(ssh, "sudo nginx -t")
    print(output)
    if "syntax is ok" not in output:
        print("[错误] 配置语法错误")
        ssh.close()
        sys.exit(1)
    
    # 4. 重启服务
    print("\n>>> [4] 重启服务...")
    exec_cmd(ssh, "sudo systemctl restart nginx")
    time.sleep(2)
    exec_cmd(ssh, "sudo systemctl restart liaotian-backend")
    time.sleep(3)
    
    output, _ = exec_cmd(ssh, "sudo systemctl is-active nginx")
    print(f"Nginx: {output}")
    output, _ = exec_cmd(ssh, "sudo systemctl is-active liaotian-backend")
    print(f"后端: {output}")
    
    # 5. 检查后端 WebSocket 路由
    print("\n>>> [5] 检查后端 WebSocket 路由...")
    output, _ = exec_cmd(ssh, "curl -s http://localhost:8000/docs 2>&1 | grep -i 'notifications.*ws' | head -3 || echo '无法检查'")
    print(output if output else "无法检查 API 文档")
    
    # 6. 测试 WebSocket 端点（使用 wscat 或 curl）
    print("\n>>> [6] 测试 WebSocket 端点...")
    output, _ = exec_cmd(ssh, "curl -i -N -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: test' http://localhost:8000/api/v1/notifications/ws/test@example.com 2>&1 | head -10")
    print(output if output else "无法测试")
    
    print("\n" + "=" * 60)
    print("修复完成")
    print("=" * 60)
    print("\n重要提示：")
    print("如果 WebSocket 仍然失败，请检查：")
    print("1. Nginx 配置中的 proxy_pass 是否正确传递路径参数")
    print("2. 后端服务日志：sudo journalctl -u liaotian-backend -n 100")
    print("3. Nginx 错误日志：sudo tail -f /var/log/nginx/error.log")
    print("\nWebSocket 连接 URL 应该是：")
    print("ws://aikz.usdt2026.cc/api/v1/notifications/ws/{user_email}")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

print("\n完成！")

