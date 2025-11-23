#!/usr/bin/env python3
"""
測試SSH連接
"""
import sys
import json
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_ssh_connection():
    """測試SSH連接"""
    # 讀取配置
    config_path = project_root / "data" / "master_config.json"
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    servers = config.get('servers', {})
    if not servers:
        print("❌ 沒有配置服務器")
        return False
    
    # 測試每個服務器
    for node_id, server_config in servers.items():
        print(f"\n{'='*60}")
        print(f"測試服務器: {node_id}")
        print(f"{'='*60}")
        print(f"主機: {server_config.get('host')}")
        print(f"用戶: {server_config.get('user')}")
        print(f"密碼: {'*' * len(server_config.get('password', ''))}")
        
        host = server_config.get('host')
        user = server_config.get('user', 'root')
        password = server_config.get('password', '')
        
        # 測試paramiko連接
        try:
            import paramiko
            print("\n[1] 測試 paramiko 連接...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                ssh.connect(host, username=user, password=password, timeout=10)
                print("✅ paramiko 連接成功!")
                
                # 測試執行命令
                stdin, stdout, stderr = ssh.exec_command('echo "SSH連接測試成功" && hostname && whoami')
                output = stdout.read().decode('utf-8')
                error = stderr.read().decode('utf-8')
                
                if output:
                    print(f"命令輸出:\n{output}")
                if error:
                    print(f"錯誤輸出:\n{error}")
                
                # 檢查systemd服務
                stdin, stdout, stderr = ssh.exec_command('systemctl is-active group-ai-worker 2>/dev/null || echo "inactive"')
                service_status = stdout.read().decode('utf-8').strip()
                print(f"服務狀態: {service_status}")
                
                ssh.close()
                print("✅ SSH連接測試完成")
                return True
                
            except paramiko.AuthenticationException as e:
                print(f"[FAIL] 認證失敗: {e}")
                print("可能的原因:")
                print("  1. 密碼不正確")
                print("  2. 用戶名不正確")
                print("  3. 服務器不允許密碼登錄")
                print(f"\n當前配置:")
                print(f"  主機: {host}")
                print(f"  用戶: {user}")
                print(f"  密碼長度: {len(password)} 字符")
                print(f"  密碼前3字符: {password[:3] if len(password) >= 3 else 'N/A'}")
                return False
            except paramiko.SSHException as e:
                print(f"❌ SSH錯誤: {e}")
                return False
            except Exception as e:
                print(f"❌ 連接失敗: {e}")
                return False
                
        except ImportError:
            print("❌ paramiko 未安裝")
            print("請運行: pip install paramiko")
            return False

if __name__ == "__main__":
    success = test_ssh_connection()
    sys.exit(0 if success else 1)

