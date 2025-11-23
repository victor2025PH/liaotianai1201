#!/usr/bin/env python3
"""
檢查部署狀態並啟動所有程序
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from master_controller import MasterController


def check_deployment_status(node_id: str, config):
    """檢查單個服務器的部署狀態"""
    print(f"\n檢查 {node_id} ({config.host}) 的部署狀態...")
    
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(config.host, username=config.user, password=config.password, timeout=10)
        
        checks = {}
        
        # 1. 檢查部署目錄
        stdin, stdout, stderr = ssh.exec_command(f'test -d {config.deploy_dir} && echo "exists" || echo "not_found"')
        checks['部署目錄'] = stdout.read().decode('utf-8').strip() == "exists"
        
        # 2. 檢查Python虛擬環境
        stdin, stdout, stderr = ssh.exec_command(f'test -d {config.deploy_dir}/venv && echo "exists" || echo "not_found"')
        checks['Python環境'] = stdout.read().decode('utf-8').strip() == "exists"
        
        # 3. 檢查配置文件
        stdin, stdout, stderr = ssh.exec_command(f'test -f {config.deploy_dir}/.env && echo "exists" || echo "not_found"')
        checks['配置文件'] = stdout.read().decode('utf-8').strip() == "exists"
        
        # 4. 檢查systemd服務
        stdin, stdout, stderr = ssh.exec_command('systemctl list-units --type=service | grep group-ai-worker || echo "not_found"')
        checks['Systemd服務'] = "group-ai-worker" in stdout.read().decode('utf-8')
        
        # 5. 檢查服務狀態
        stdin, stdout, stderr = ssh.exec_command('systemctl is-active group-ai-worker 2>/dev/null || echo "inactive"')
        service_status = stdout.read().decode('utf-8').strip()
        checks['服務狀態'] = service_status
        
        # 6. 檢查端口
        stdin, stdout, stderr = ssh.exec_command('netstat -tlnp 2>/dev/null | grep :8000 || ss -tlnp 2>/dev/null | grep :8000 || echo "not_listening"')
        checks['端口監聽'] = "8000" in stdout.read().decode('utf-8')
        
        ssh.close()
        
        # 顯示檢查結果
        print("  部署狀態檢查:")
        for check_name, result in checks.items():
            if isinstance(result, bool):
                status = "[OK]" if result else "[FAIL]"
            else:
                status = f"[{result}]"
            print(f"    {check_name}: {status}")
        
        # 判斷是否部署完成
        deployment_complete = (
            checks['部署目錄'] and
            checks['Python環境'] and
            checks['配置文件'] and
            checks['Systemd服務']
        )
        
        return deployment_complete, checks
        
    except Exception as e:
        print(f"  [FAIL] 檢查失敗: {e}")
        return False, {}


def start_server(node_id: str, config):
    """啟動服務器"""
    print(f"\n啟動 {node_id} ({config.host})...")
    
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(config.host, username=config.user, password=config.password, timeout=10)
        
        # 啟動服務
        stdin, stdout, stderr = ssh.exec_command('systemctl start group-ai-worker')
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            # 等待服務啟動
            time.sleep(3)
            
            # 檢查狀態
            stdin, stdout, stderr = ssh.exec_command('systemctl is-active group-ai-worker')
            status = stdout.read().decode('utf-8').strip()
            
            if status == "active":
                print(f"  [OK] {node_id} 啟動成功")
                
                # 檢查端口
                stdin, stdout, stderr = ssh.exec_command('netstat -tlnp 2>/dev/null | grep :8000 || ss -tlnp 2>/dev/null | grep :8000')
                port_check = stdout.read().decode('utf-8')
                if "8000" in port_check:
                    print(f"  [OK] 端口8000正在監聽")
                else:
                    print(f"  [WARN] 端口8000未監聽，服務可能還在啟動中")
                
                ssh.close()
                return True
            else:
                print(f"  [WARN] 啟動命令執行，但狀態為: {status}")
                ssh.close()
                return False
        else:
            error = stderr.read().decode('utf-8')
            print(f"  [FAIL] 啟動失敗: {error}")
            ssh.close()
            return False
            
    except Exception as e:
        print(f"  [FAIL] 啟動失敗: {e}")
        return False


def main():
    print("=" * 60)
    print("檢查部署狀態並啟動所有程序")
    print("=" * 60)
    
    controller = MasterController()
    
    if not controller.servers:
        print("沒有已配置的服務器")
        return
    
    results = {}
    
    # 1. 檢查部署狀態
    print("\n" + "=" * 60)
    print("步驟1: 檢查部署狀態")
    print("=" * 60)
    
    for node_id, config in controller.servers.items():
        deployment_complete, checks = check_deployment_status(node_id, config)
        results[node_id] = {
            'deployment_complete': deployment_complete,
            'checks': checks
        }
    
    # 2. 啟動已部署的服務器
    print("\n" + "=" * 60)
    print("步驟2: 啟動已部署的服務器")
    print("=" * 60)
    
    for node_id, config in controller.servers.items():
        if results[node_id]['deployment_complete']:
            start_success = start_server(node_id, config)
            results[node_id]['start_success'] = start_success
        else:
            print(f"\n跳過 {node_id}: 部署未完成")
            results[node_id]['start_success'] = False
    
    # 3. 總結
    print("\n" + "=" * 60)
    print("總結")
    print("=" * 60)
    
    for node_id, result in results.items():
        print(f"\n{node_id}:")
        print(f"  部署狀態: {'完成' if result['deployment_complete'] else '未完成'}")
        if result['deployment_complete']:
            print(f"  啟動狀態: {'成功' if result.get('start_success') else '失敗'}")
            if result.get('start_success'):
                print(f"  服務地址: http://{controller.servers[node_id].host}:8000")
    
    # 4. 生成測試清單
    print("\n" + "=" * 60)
    print("測試清單")
    print("=" * 60)
    
    print("\n需要測試的程序:")
    print("  1. 後端API服務 (admin-backend)")
    print("     - 地址: http://localhost:8000")
    print("     - 測試: GET /health")
    print("     - 測試: GET /api/v1/group-ai/servers/")
    
    print("\n  2. 前端服務 (saas-demo)")
    print("     - 地址: http://localhost:3000")
    print("     - 測試頁面: http://localhost:3000/group-ai/servers")
    print("     - 測試頁面: http://localhost:3000/group-ai/accounts")
    
    for node_id, result in results.items():
        if result.get('start_success'):
            host = controller.servers[node_id].host
            print(f"\n  3. 工作節點 {node_id}")
            print(f"     - 地址: http://{host}:8000")
            print(f"     - 測試: GET http://{host}:8000/health")
            print(f"     - 測試: GET http://{host}:8000/api/v1/group-ai/accounts")
    
    print("\n測試內容:")
    print("  1. 服務器狀態檢查")
    print("     - 訪問 http://localhost:3000/group-ai/servers")
    print("     - 檢查所有服務器是否顯示為'在線'")
    print("     - 檢查帳號數量是否正確")
    
    print("\n  2. 服務器操作測試")
    print("     - 測試啟動/停止/重啟功能")
    print("     - 檢查操作是否成功")
    
    print("\n  3. 日誌查看測試")
    print("     - 點擊'日誌'按鈕")
    print("     - 檢查日誌是否正常顯示")
    print("     - 檢查錯誤日誌是否高亮")
    
    print("\n  4. API接口測試")
    print("     - curl http://localhost:8000/api/v1/group-ai/servers/")
    print("     - curl http://localhost:8000/api/v1/group-ai/accounts")
    
    print("\n  5. 帳號管理測試")
    print("     - 訪問 http://localhost:3000/group-ai/accounts")
    print("     - 測試創建帳號")
    print("     - 測試啟動/停止帳號")
    print("     - 測試上傳Session文件")


if __name__ == '__main__':
    main()

