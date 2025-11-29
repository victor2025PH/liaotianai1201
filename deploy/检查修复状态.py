# -*- coding: utf-8 -*-
import paramiko
import sys

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    
    # 执行修复
    print("执行修复...")
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
    f=open('/etc/nginx/sites-available/aikz.usdt2026.cc','w',encoding='utf-8')
    f.writelines(lines)
    f.close()
    print('OK:已删除',len(idx)-1,'个重复块')
else:
    print('OK:无需修复')
'''
    
    sftp = ssh.open_sftp()
    f = sftp.file('/tmp/fix.py', 'w')
    f.write(fix_code)
    f.close()
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("sudo python3 /tmp/fix.py 2>&1")
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    # 验证
    stdin, stdout, stderr = ssh.exec_command("sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"Location数量: {count}")
    
    if count == "1":
        stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
        test = stdout.read().decode('utf-8', errors='ignore')
        print(test)
        if "syntax is ok" in test:
            ssh.exec_command("sudo systemctl reload nginx 2>&1")
            print("修复完成！Nginx已重载")
    
    ssh.exec_command("rm /tmp/fix.py 2>&1")
    ssh.close()
    
except Exception as e:
    print(f"错误: {e}")

