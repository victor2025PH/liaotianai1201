"""
服務器管理API
用於查詢和管理遠程服務器狀態
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import subprocess
import json
import os
from pathlib import Path

router = APIRouter(tags=["servers"])


class ServerStatus(BaseModel):
    """服務器狀態"""
    node_id: str
    host: str
    port: int
    status: str  # online, offline, error
    accounts_count: int
    max_accounts: int
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    last_heartbeat: Optional[str] = None
    service_status: Optional[str] = None  # systemd服務狀態


class ServerLogEntry(BaseModel):
    """日誌條目"""
    timestamp: str
    level: str
    message: str


class ServerActionRequest(BaseModel):
    """服務器操作請求"""
    action: str  # start, stop, restart, status
    node_id: str


def get_master_config_path() -> Path:
    """獲取主節點配置文件路徑"""
    project_root = Path(__file__).parent.parent.parent.parent.parent
    return project_root / "data" / "master_config.json"


def load_server_configs() -> Dict:
    """加載服務器配置"""
    config_path = get_master_config_path()
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('servers', {})


@router.get("/", response_model=List[ServerStatus])
async def list_servers():
    """獲取所有服務器列表"""
    servers_config = load_server_configs()
    servers = []
    
    for node_id, config in servers_config.items():
        try:
            status = await get_server_status(node_id, config)
            servers.append(status)
        except Exception as e:
            # 如果無法連接，返回錯誤狀態
            servers.append(ServerStatus(
                node_id=node_id,
                host=config.get('host', ''),
                port=config.get('port', 8000),
                status='error',
                accounts_count=0,
                max_accounts=config.get('max_accounts', 5),
                service_status=f"連接失敗: {str(e)}"
            ))
    
    return servers


@router.get("/{node_id}", response_model=ServerStatus)
async def get_server(node_id: str):
    """獲取單個服務器狀態"""
    servers_config = load_server_configs()
    
    if node_id not in servers_config:
        raise HTTPException(status_code=404, detail=f"服務器 {node_id} 不存在")
    
    config = servers_config[node_id]
    return await get_server_status(node_id, config)


async def get_server_status(node_id: str, config: Dict) -> ServerStatus:
    """獲取服務器狀態"""
    host = config.get('host', '')
    user = config.get('user', 'ubuntu')
    password = config.get('password', '')
    deploy_dir = config.get('deploy_dir', '/opt/group-ai')
    
    # 檢查服務狀態
    service_status = "unknown"
    accounts_count = 0
    
    # 優先嘗試使用paramiko（Windows友好）
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        stdin, stdout, stderr = ssh.exec_command('systemctl is-active group-ai-worker 2>/dev/null || echo "inactive"')
        service_status = stdout.read().decode('utf-8').strip()
        # 清理可能的重複輸出
        if '\n' in service_status:
            service_status = service_status.split('\n')[-1].strip()
        
        # 獲取帳號數量
        stdin, stdout, stderr = ssh.exec_command(f'ls -1 {deploy_dir}/sessions/*.session 2>/dev/null | wc -l')
        accounts_count = int(stdout.read().decode('utf-8').strip() or 0)
        
        ssh.close()
    except ImportError:
        # paramiko未安裝，嘗試使用sshpass
        try:
            cmd = [
                'sshpass', '-p', password,
                'ssh', '-o', 'StrictHostKeyChecking=accept-new', '-o', 'ConnectTimeout=5',
                f'{user}@{host}',
                'systemctl is-active group-ai-worker 2>/dev/null || echo "inactive"'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                service_status = result.stdout.strip()
            
            # 獲取帳號數量
            cmd = [
                'sshpass', '-p', password,
                'ssh', '-o', 'StrictHostKeyChecking=accept-new', '-o', 'ConnectTimeout=5',
                f'{user}@{host}',
                f'ls -1 {deploy_dir}/sessions/*.session 2>/dev/null | wc -l'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                accounts_count = int(result.stdout.strip() or 0)
        except FileNotFoundError:
            service_status = "sshpass未安裝，請安裝paramiko或sshpass"
        except Exception as e:
            service_status = f"sshpass錯誤: {str(e)}"
    except Exception as e:
        service_status = f"連接失敗: {str(e)}"
    
    # 判斷服務器狀態
    if service_status == "active":
        status = "online"
    elif service_status == "inactive" or service_status == "failed":
        status = "offline"
    else:
        status = "error"
    
    return ServerStatus(
        node_id=node_id,
        host=host,
        port=config.get('port', 8000),
        status=status,
        accounts_count=accounts_count,
        max_accounts=config.get('max_accounts', 5),
        service_status=service_status
    )


@router.get("/{node_id}/logs", response_model=List[ServerLogEntry])
async def get_server_logs(node_id: str, lines: int = 100):
    """獲取服務器日誌"""
    servers_config = load_server_configs()
    
    if node_id not in servers_config:
        raise HTTPException(status_code=404, detail=f"服務器 {node_id} 不存在")
    
    config = servers_config[node_id]
    host = config.get('host', '')
    user = config.get('user', 'ubuntu')
    password = config.get('password', '')
    deploy_dir = config.get('deploy_dir', '/opt/group-ai')
    log_file = f"{deploy_dir}/logs/worker.log"
    
    # 優先嘗試使用paramiko（Windows友好）
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        # 使用journalctl获取systemd服务日志（更可靠）
        # 先尝试使用journalctl，如果失败则使用日志文件
        stdin, stdout, stderr = ssh.exec_command(f'sudo journalctl -u group-ai-worker -n {lines} --no-pager 2>&1')
        log_output = stdout.read().decode('utf-8')
        error_output = stderr.read().decode('utf-8')
        
        # 如果journalctl失败，尝试读取日志文件
        if not log_output.strip() or "No entries" in log_output or "No such file" in error_output:
            stdin, stdout, stderr = ssh.exec_command(f'tail -n {lines} {log_file} 2>/dev/null || echo "日誌文件不存在"')
            log_output = stdout.read().decode('utf-8')
        
        ssh.close()
        
        log_lines = log_output.strip().split('\n')
        logs = []
        for line in log_lines:
            if line.strip() and "日誌文件不存在" not in line:
                # 解析journalctl格式: Nov 16 20:39:55 hostname start.sh[52283]: INFO:__main__:ServiceManager初始化完成
                import re
                # 尝试匹配journalctl格式
                journal_match = re.match(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+\S+\s+\S+\[.*?\]:\s*(.+)', line)
                if journal_match:
                    timestamp, message = journal_match.groups()
                    # 从消息中提取level
                    level_match = re.match(r'(\w+):', message)
                    level = level_match.group(1) if level_match else "INFO"
                    # 移除level前缀
                    message_clean = re.sub(r'^\w+:', '', message).strip()
                    logs.append(ServerLogEntry(
                        timestamp=timestamp.strip(),
                        level=level.strip(),
                        message=message_clean
                    ))
                else:
                    # 尝试匹配其他格式
                    match = re.match(r'(\d{4}-\d{2}-\d{2}[\s\d:]+)\s+(\w+)\s+(.+)', line)
                    if match:
                        timestamp, level, message = match.groups()
                        logs.append(ServerLogEntry(
                            timestamp=timestamp.strip(),
                            level=level.strip(),
                            message=message.strip()
                        ))
                    else:
                        logs.append(ServerLogEntry(
                            timestamp="",
                            level="INFO",
                            message=line.strip()
                        ))
        return logs
    except ImportError:
        # paramiko未安裝，嘗試使用sshpass
        try:
            cmd = [
                'sshpass', '-p', password,
                'ssh', '-o', 'StrictHostKeyChecking=accept-new', '-o', 'ConnectTimeout=5',
                f'{user}@{host}',
                f'tail -n {lines} {log_file} 2>/dev/null || echo "日誌文件不存在"'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                log_lines = result.stdout.strip().split('\n')
                logs = []
                for line in log_lines:
                    if line.strip():
                        import re
                        match = re.match(r'(\d{4}-\d{2}-\d{2}[\s\d:]+)\s+(\w+)\s+(.+)', line)
                        if match:
                            timestamp, level, message = match.groups()
                            logs.append(ServerLogEntry(
                                timestamp=timestamp.strip(),
                                level=level.strip(),
                                message=message.strip()
                            ))
                        else:
                            logs.append(ServerLogEntry(
                                timestamp="",
                                level="INFO",
                                message=line.strip()
                            ))
                return logs
            else:
                raise HTTPException(status_code=500, detail="讀取日誌失敗")
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="sshpass未安裝，請安裝paramiko或sshpass")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"讀取日誌失敗: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取日誌失敗: {str(e)}")


@router.post("/{node_id}/action")
async def server_action(node_id: str, request: ServerActionRequest):
    """執行服務器操作"""
    servers_config = load_server_configs()
    
    if node_id not in servers_config:
        raise HTTPException(status_code=404, detail=f"服務器 {node_id} 不存在")
    
    config = servers_config[node_id]
    host = config.get('host', '')
    user = config.get('user', 'ubuntu')
    password = config.get('password', '')
    
    action = request.action
    valid_actions = ['start', 'stop', 'restart', 'status']
    
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"無效的操作: {action}")
    
    # 優先嘗試使用paramiko（Windows友好）
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=5)
        
        # 先檢查服務是否存在
        stdin, stdout, stderr = ssh.exec_command('systemctl list-unit-files | grep -q "group-ai-worker.service" && echo "exists" || echo "not_found"')
        service_exists = stdout.read().decode('utf-8').strip() == "exists"
        
        if not service_exists:
            ssh.close()
            return {
                "success": False, 
                "message": f"服務 group-ai-worker 不存在，請先部署服務",
                "error": "Service not found"
            }
        
        # 執行systemctl命令，嘗試無密碼sudo，如果失敗則通過stdin傳遞密碼
        stdin, stdout, stderr = ssh.exec_command(f'sudo -S systemctl {action} group-ai-worker')
        # 如果sudo需要密碼，通過stdin傳遞
        stdin.write(f'{password}\n')
        stdin.flush()
        
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        ssh.close()
        
        if exit_code == 0:
            return {"success": True, "message": f"操作 {action} 執行成功", "output": output}
        else:
            # 提供更詳細的錯誤信息
            error_msg = error if error else output
            if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                return {
                    "success": False, 
                    "message": f"服務 group-ai-worker 不存在，請先部署服務",
                    "error": error_msg
                }
            return {"success": False, "message": f"操作 {action} 執行失敗: {error_msg}", "error": error_msg}
    except ImportError:
        # paramiko未安裝，嘗試使用sshpass
        try:
            cmd = [
                'sshpass', '-p', password,
                'ssh', '-o', 'StrictHostKeyChecking=accept-new', '-o', 'ConnectTimeout=5',
                f'{user}@{host}',
                f'sudo systemctl {action} group-ai-worker'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {"success": True, "message": f"操作 {action} 執行成功", "output": result.stdout}
            else:
                return {"success": False, "message": f"執行操作失敗: {result.stderr}", "output": result.stdout}
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="sshpass未安裝，請安裝paramiko或sshpass")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"執行操作失敗: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"執行操作失敗: {str(e)}")

