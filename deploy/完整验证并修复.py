# -*- coding: utf-8 -*-
"""完整验证并修复 WebSocket 配置"""
import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER = "165.154.233.55"
USERNAME = "ubuntu"
PASSWORD = "Along2025!!!"

def exec_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

print("=" * 60)
print("完整验证并修复 WebSocket 配置")
print("=" * 60)
print()

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] 已连接服务器\n")
    
    # 1. 检查 location 数量
    print(">>> [1/7] 检查 location 块数量...")
    output, _ = exec_cmd(ssh, "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    count = int(output.strip() or "0")
    print(f"Location 块数量: {count}\n")
    
    # 2. 如果有多个，执行修复
    if count > 1:
        print(f">>> [2/7] 发现 {count} 个 location 块，执行修复...")
        output, _ = exec_cmd(ssh, "sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.final")
        
        fix_code = '''import re
f=open('/etc/nginx/sites-available/aikz.usdt2026.cc','r',encoding='utf-8')
lines=f.readlines()
f.close()
idx=[i for i,l in enumerate(lines) if 'location /api/v1/notifications/ws' in l]
print(f'找到{len(idx)}个location')
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
    print(f'已删除{len(idx)-1}个重复块')
else:
    print('无需修复')
'''
        
        sftp = ssh.open_sftp()
        f = sftp.file('/tmp/fix_final.py', 'w')
        f.write(fix_code)
        f.close()
        sftp.close()
        
        output, error = exec_cmd(ssh, "sudo python3 /tmp/fix_final.py")
        print(output)
        ssh.exec_command("rm /tmp/fix_final.py")
        
        # 再次检查
        output, _ = exec_cmd(ssh, "sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
        count = int(output.strip() or "0")
        print(f"修复后 location 数量: {count}\n")
    
    # 3. 验证只有一个
    if count != 1:
        print(f"[错误] 仍有 {count} 个 location 块，需要手动检查")
        ssh.close()
        sys.exit(1)
    
    print("[OK] 只有一个 location 块\n")
    
    # 4. 测试配置
    print(">>> [3/7] 测试 Nginx 配置...")
    output, error = exec_cmd(ssh, "sudo nginx -t")
    print(output)
    if "syntax is ok" not in output:
        print("[错误] 配置测试失败")
        ssh.close()
        sys.exit(1)
    print("[OK] 配置语法正确\n")
    
    # 5. 重载 Nginx
    print(">>> [4/7] 重载 Nginx...")
    output, error = exec_cmd(ssh, "sudo systemctl reload nginx")
    print("[OK] Nginx 已重载\n")
    
    # 6. 检查服务状态
    print(">>> [5/7] 检查服务状态...")
    output, _ = exec_cmd(ssh, "sudo systemctl is-active nginx")
    print(f"Nginx 状态: {output.strip()}")
    output, _ = exec_cmd(ssh, "sudo systemctl is-active liaotian-backend")
    print(f"后端服务状态: {output.strip()}\n")
    
    # 7. 显示最终配置
    print(">>> [6/7] 最终 WebSocket 配置：")
    output, _ = exec_cmd(ssh, "sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc")
    print(output)
    
    # 8. 检查端口监听
    print(">>> [7/7] 检查端口监听...")
    output, _ = exec_cmd(ssh, "sudo ss -tlnp | grep -E ':80|:8000' | head -5")
    print(output if output.strip() else "未检测到端口监听")
    
    print("\n" + "=" * 60)
    print("[成功] 修复完成！")
    print("=" * 60)
    print("\n下一步操作：")
    print("1. 在前端浏览器中强制刷新页面（Ctrl+F5 或 Cmd+Shift+R）")
    print("2. 打开开发者工具（F12）→ Network 标签")
    print("3. 筛选 WS (WebSocket) 连接")
    print("4. 检查连接状态，应该看到状态码 101")
    print("\n如果仍有错误，请检查：")
    print("- 浏览器控制台的详细错误信息")
    print("- 后端服务日志：sudo journalctl -u liaotian-backend -n 50")
    print("- Nginx 错误日志：sudo tail -f /var/log/nginx/error.log")
    
    ssh.close()
    
except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n完成！")

