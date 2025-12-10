"""
服務器管理API
用於查詢和管理遠程服務器狀態
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import subprocess
import json
import os
from pathlib import Path
import logging

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.core.cache import cached, invalidate_cache

logger = logging.getLogger(__name__)

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
@cached(prefix="servers_list", ttl=60)  # 緩存 60 秒（服務器狀態變化較慢）
async def list_servers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _t: Optional[int] = Query(None, description="強制刷新時間戳（繞過緩存）")
):
    """獲取所有服務器列表（並發優化版本，帶緩存）"""
    try:
        # 如果提供了強制刷新時間戳，清除緩存
        if _t is not None:
            invalidate_cache("servers_list:*")
        import asyncio
        servers_config = load_server_configs()
        
        # 使用並發處理所有服務器，大幅提升速度
    async def get_server_status_safe(node_id: str, config: Dict):
        """安全獲取服務器狀態，捕獲所有異常"""
        try:
            return await get_server_status(node_id, config, db)
        except Exception as e:
            # 如果無法連接，返回錯誤狀態，但從數據庫獲取賬號數
            accounts_count = 0
            try:
                from app.models.group_ai import GroupAIAccount
                # 只統計激活的賬號
                accounts_count = db.query(GroupAIAccount).filter(
                    GroupAIAccount.server_id == node_id,
                    GroupAIAccount.active == True
                ).count()
                logger.debug(f"服務器 {node_id} 連接失敗，從數據庫獲取賬號數: {accounts_count}")
            except Exception as db_error:
                logger.warning(f"從數據庫獲取賬號數失敗: {db_error}")
                accounts_count = 0
            
            return ServerStatus(
                node_id=node_id,
                host=config.get('host', ''),
                port=config.get('port', 8000),
                status='error',
                accounts_count=accounts_count,
                max_accounts=config.get('max_accounts', 5),
                service_status=f"連接失敗: {str(e)}"
            )
    
    # 並發獲取所有服務器狀態
    tasks = [
        get_server_status_safe(node_id, config)
        for node_id, config in servers_config.items()
    ]
    
    # 使用 asyncio.gather 並發執行，設置總超時時間為 10 秒
    try:
        servers = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),  # 添加 return_exceptions=True 避免单个任务失败导致整体失败
            timeout=10.0  # 總超時時間 10 秒
        )
        # 过滤掉异常结果
        valid_servers = []
        for result in servers:
            if isinstance(result, Exception):
                logger.warning(f"獲取服務器狀態時發生異常: {result}")
            else:
                valid_servers.append(result)
        servers = valid_servers
    except asyncio.TimeoutError:
        # 如果超時，返回部分結果
        logger.warning("獲取服務器狀態超時，返回部分結果")
        # 嘗試獲取已完成的部分結果
        servers = []
        for task in tasks:
            if task.done():
                try:
                    result = task.result()
                    if not isinstance(result, Exception):
                        servers.append(result)
                except Exception as e:
                    logger.warning(f"獲取服務器狀態時發生異常: {e}")
    except Exception as e:
        logger.exception(f"獲取服務器列表失敗: {e}", exc_info=True)
        # 即使發生異常，也返回空列表而不是拋出 500 錯誤
        servers = []
    
        return servers
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"獲取服務器列表失敗（外層異常處理）: {e}", exc_info=True)
        # 返回空列表而不是拋出 500 錯誤，讓前端可以正常顯示（即使沒有服務器數據）
        return []


@router.get("/{node_id}", response_model=ServerStatus)
async def get_server(node_id: str, db: Session = Depends(get_db)):
    """獲取單個服務器狀態"""
    servers_config = load_server_configs()
    
    if node_id not in servers_config:
        raise HTTPException(status_code=404, detail=f"服務器 {node_id} 不存在")
    
    config = servers_config[node_id]
    return await get_server_status(node_id, config, db)


async def get_server_status(node_id: str, config: Dict, db: Optional[Session] = None) -> ServerStatus:
    """獲取服務器狀態"""
    host = config.get('host', '')
    user = config.get('user', 'ubuntu')
    password = config.get('password', '')
    deploy_dir = config.get('deploy_dir', '/home/ubuntu')
    
    # 檢查服務狀態
    service_status = "unknown"
    accounts_count = 0
    
    # 優先嘗試使用paramiko（Windows友好）
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 減少連接超時時間，快速失敗
        ssh.connect(host, username=user, password=password, timeout=3)
        
        # 優化：合併多個命令為一個，減少 SSH 往返次數
        # 一次性獲取進程狀態、進程數和文件數
        combined_command = f'''
        if pgrep -f "python.*main.py" > /dev/null; then
            echo "active"
        else
            echo "inactive"
        fi
        echo "---SEPARATOR---"
        pgrep -f "python.*main.py" | wc -l
        echo "---SEPARATOR---"
        ls -1 {deploy_dir}/sessions/*.session 2>/dev/null | wc -l
        '''
        
        stdin, stdout, stderr = ssh.exec_command(combined_command, timeout=3)
        output = stdout.read().decode('utf-8').strip()
        parts = output.split('---SEPARATOR---')
        
        if len(parts) >= 3:
            service_status = parts[0].strip()
            process_count = int(parts[1].strip() or 0)
            file_count = int(parts[2].strip() or 0)
        else:
            # 如果命令失敗，使用默認值
            service_status = "unknown"
            process_count = 0
            file_count = 0
        
        # 清理可能的重複輸出
        if '\n' in service_status:
            service_status = service_status.split('\n')[-1].strip()
        
        # 使用進程數和文件數的較大值（因為可能有未運行的 session 文件）
        file_based_count = max(process_count, file_count)
        
        ssh.close()
        
        # 優先從數據庫統計（更準確）
        # 數據庫是唯一真實來源，因為：
        # 1. 文件系統可能包含已刪除但未清理的文件
        # 2. 文件系統可能包含臨時文件或測試文件
        # 3. 數據庫記錄是經過驗證的實際分配的賬號
        accounts_count = 0
        if db:
            try:
                from app.models.group_ai import GroupAIAccount
                db_count = db.query(GroupAIAccount).filter(
                    GroupAIAccount.server_id == node_id,
                    GroupAIAccount.active == True  # 只统计激活的账号
                ).count()
                # 直接使用數據庫統計，這是真實的賬號數量
                accounts_count = db_count
                logger.debug(f"服務器 {node_id} 數據庫統計: {db_count} 個激活賬號，文件系統統計: {file_based_count} 個文件")
            except Exception as e:
                logger.warning(f"從數據庫統計賬號數失敗: {e}，回退到文件統計")
                # 只有在數據庫查詢失敗時才使用文件統計
                accounts_count = file_based_count
        else:
            # 如果沒有數據庫會話，使用文件統計（但這不是理想情況）
            logger.warning(f"沒有數據庫會話，使用文件統計: {file_based_count}")
            accounts_count = file_based_count
    except ImportError:
        # paramiko未安裝，嘗試使用sshpass
        try:
            # 優化：合併多個命令為一個，減少 SSH 往返次數
            combined_command = f'''
            if pgrep -f "python.*main.py" > /dev/null; then
                echo "active"
            else
                echo "inactive"
            fi
            echo "---SEPARATOR---"
            pgrep -f "python.*main.py" | wc -l
            echo "---SEPARATOR---"
            ls -1 {deploy_dir}/sessions/*.session 2>/dev/null | wc -l
            '''
            
            cmd = [
                'sshpass', '-p', password,
                'ssh', '-o', 'StrictHostKeyChecking=accept-new', '-o', 'ConnectTimeout=3',
                f'{user}@{host}',
                combined_command
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout.strip()
                parts = output.split('---SEPARATOR---')
                if len(parts) >= 3:
                    service_status = parts[0].strip()
                    process_count = int(parts[1].strip() or 0)
                    file_count = int(parts[2].strip() or 0)
                else:
                    service_status = "unknown"
                    process_count = 0
                    file_count = 0
            else:
                service_status = "unknown"
                process_count = 0
                file_count = 0
            
            # 使用較大值
            file_based_count = max(process_count, file_count)
            
            # 優先從數據庫統計（如果提供了 db）
            accounts_count = 0
            if db:
                try:
                    from app.models.group_ai import GroupAIAccount
                    db_count = db.query(GroupAIAccount).filter(
                        GroupAIAccount.server_id == node_id,
                        GroupAIAccount.active == True  # 只统计激活的账号
                    ).count()
                    accounts_count = db_count
                    logger.debug(f"服務器 {node_id} 數據庫統計: {db_count} 個激活賬號，文件系統統計: {file_based_count} 個文件")
                except Exception as e:
                    logger.warning(f"從數據庫統計賬號數失敗: {e}，回退到文件統計")
                    accounts_count = file_based_count
            else:
                # 如果沒有數據庫會話，使用文件統計（但這不是理想情況）
                logger.warning(f"沒有數據庫會話，使用文件統計: {file_based_count}")
                accounts_count = file_based_count
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
        
        # 執行操作（直接操作 main.py 進程，而不是 systemd 服務）
        deploy_dir = config.get('deploy_dir', '/home/ubuntu')
        output = ""
        error = ""
        exit_code = 0
        
        if action == "start":
            # 啟動所有該服務器的賬號（從數據庫獲取）
            # 這裡先簡單啟動，實際應該根據數據庫中的 server_id 來啟動對應的賬號
            cmd = f'cd {deploy_dir} && nohup python3 main.py > logs/main.log 2>&1 &'
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
        elif action == "stop":
            # 停止所有 main.py 進程
            stdin, stdout, stderr = ssh.exec_command('pkill -f "python.*main.py"')
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
        elif action == "restart":
            # 先停止，再啟動
            stdin, stdout, stderr = ssh.exec_command('pkill -f "python.*main.py"; sleep 2; cd {deploy_dir} && nohup python3 main.py > logs/main.log 2>&1 &')
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
        elif action == "status":
            # 檢查進程狀態
            stdin, stdout, stderr = ssh.exec_command('pgrep -f "python.*main.py" > /dev/null && echo "active" || echo "inactive"')
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8')
        
        ssh.close()
        
        if exit_code == 0 or action == "status":
            return {"success": True, "message": f"操作 {action} 執行成功", "output": output}
        else:
            error_msg = error if error else output
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

