# -*- coding: utf-8 -*-
"""立即修复 WebSocket 重复配置"""
import paramiko
import sys
import io

# 强制 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

print("=" * 60)
print("正在修复 WebSocket 配置...")
print("=" * 60)
print()

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] 已连接服务器\n")
    
    # 检查
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
    )
    count = int(stdout.read().decode('utf-8', errors='ignore').strip() or "0")
    print(f"当前 location 块数量: {count}")
    
    if count <= 1:
        print("[OK] 配置正常，无需修复")
        ssh.close()
        sys.exit(0)
    
    # 备份
    print("\n[1/5] 备份配置...")
    ssh.exec_command("sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.now 2>&1")
    print("[OK] 已备份")
    
    # 修复脚本
    print("\n[2/5] 执行修复...")
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
    print('已删除',len(idx)-1,'个重复块')
else:
    print('无需修复')
'''
    
    sftp = ssh.open_sftp()
    f = sftp.file('/tmp/fix_ws.py', 'w')
    f.write(fix_code)
    f.close()
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("sudo python3 /tmp/fix_ws.py 2>&1")
    result = stdout.read().decode('utf-8', errors='ignore')
    print(result)
    ssh.exec_command("rm /tmp/fix_ws.py 2>&1")
    
    # 验证
    print("\n[3/5] 验证修复...")
    stdin, stdout, stderr = ssh.exec_command(
        "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc 2>&1"
    )
    new_count = int(stdout.read().decode('utf-8', errors='ignore').strip() or "0")
    print(f"剩余 location 数量: {new_count}")
    
    if new_count != 1:
        print(f"[错误] 仍有 {new_count} 个 location 块")
        ssh.close()
        sys.exit(1)
    
    # 测试
    print("\n[4/5] 测试配置...")
    stdin, stdout, stderr = ssh.exec_command("sudo nginx -t 2>&1")
    test_out = stdout.read().decode('utf-8', errors='ignore')
    print(test_out)
    
    if "syntax is ok" not in test_out:
        print("[错误] 配置测试失败")
        ssh.close()
        sys.exit(1)
    
    # 重载
    print("\n[5/5] 重载 Nginx...")
    ssh.exec_command("sudo systemctl reload nginx 2>&1")
    print("[OK] Nginx 已重载")
    
    print("\n" + "=" * 60)
    print("[成功] 修复完成！")
    print("=" * 60)
    print("\n请在前端浏览器中：")
    print("1. 刷新页面")
    print("2. 打开开发者工具（F12）→ Network 标签")
    print("3. 筛选 WS (WebSocket)")
    print("4. 检查连接状态，应该看到状态码 101")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

