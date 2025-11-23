"""
Session文件自動上傳和分配服務
實現智能分配算法，每個服務器最多5個賬號
"""
import logging
import json
import paramiko
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ServerNode:
    """服務器節點信息"""
    node_id: str
    host: str
    user: str
    password: str
    deploy_dir: str
    max_accounts: int = 5
    current_accounts: int = 0
    location: str = ""
    status: str = "active"


class SessionUploader:
    """Session文件上傳和分配器"""
    
    def __init__(self, master_config_path: Optional[Path] = None):
        if master_config_path is None:
            # 默認從項目根目錄查找
            project_root = Path(__file__).parent.parent.parent.parent.parent
            master_config_path = project_root / "data" / "master_config.json"
        
        self.master_config_path = master_config_path
        self.servers: Dict[str, ServerNode] = {}
        self._load_servers()
    
    def _load_servers(self):
        """加載服務器配置"""
        if not self.master_config_path.exists():
            logger.warning(f"主配置文件不存在: {self.master_config_path}")
            return
        
        try:
            with open(self.master_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                servers_config = config.get('servers', {})
                
                for node_id, server_config in servers_config.items():
                    if server_config.get('status', 'active') == 'active':
                        self.servers[node_id] = ServerNode(
                            node_id=node_id,
                            host=server_config['host'],
                            user=server_config.get('user', 'ubuntu'),
                            password=server_config.get('password', ''),
                            deploy_dir=server_config.get('deploy_dir', '/opt/group-ai'),
                            max_accounts=server_config.get('max_accounts', 5),
                            current_accounts=0,  # 需要從服務器查詢實際數量
                            location=server_config.get('location', ''),
                            status=server_config.get('status', 'active')
                        )
                        logger.info(f"加載服務器節點: {node_id} ({server_config['host']})")
        except Exception as e:
            logger.error(f"加載服務器配置失敗: {e}")
    
    def _get_server_account_count(self, node: ServerNode) -> int:
        """獲取服務器上的實際賬號數量"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(node.host, username=node.user, password=node.password, timeout=10)
            
            try:
                # 檢查遠程sessions目錄中的文件數量
                remote_sessions_dir = f"{node.deploy_dir}/sessions"
                stdin, stdout, stderr = ssh.exec_command(f'ls -1 {remote_sessions_dir}/*.session 2>/dev/null | wc -l')
                count = int(stdout.read().decode().strip())
                return count
            finally:
                ssh.close()
        except Exception as e:
            logger.warning(f"獲取服務器 {node.node_id} 賬號數量失敗: {e}")
            return 0
    
    def find_best_server(self) -> Optional[ServerNode]:
        """找到最適合的服務器（負載最低且未滿）"""
        best_node = None
        min_load = float('inf')
        
        for node_id, node in self.servers.items():
            if node.status != 'active':
                continue
            
            # 獲取實際賬號數量
            node.current_accounts = self._get_server_account_count(node)
            
            # 檢查是否已滿
            if node.current_accounts >= node.max_accounts:
                continue
            
            # 計算負載率
            load_ratio = node.current_accounts / node.max_accounts if node.max_accounts > 0 else 1.0
            
            # 選擇負載最低的服務器
            if load_ratio < min_load:
                min_load = load_ratio
                best_node = node
        
        return best_node
    
    def upload_session_to_server(
        self, 
        session_file: str, 
        node: ServerNode,
        account_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        上傳session文件到指定服務器
        
        Returns:
            (success, remote_path_or_error_message)
        """
        try:
            session_path = Path(session_file)
            if not session_path.exists():
                return False, f"Session文件不存在: {session_file}"
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(node.host, username=node.user, password=node.password, timeout=30)
            
            try:
                remote_sessions_dir = f"{node.deploy_dir}/sessions"
                
                # 確保遠程目錄存在
                ssh.exec_command(f'mkdir -p {remote_sessions_dir}')
                
                # 使用SFTP上傳文件
                sftp = ssh.open_sftp()
                try:
                    # 使用account_id作為文件名（如果提供），否則使用原文件名
                    if account_id:
                        remote_filename = f"{account_id}.session"
                    else:
                        remote_filename = session_path.name
                    
                    remote_path = f"{remote_sessions_dir}/{remote_filename}"
                    sftp.put(str(session_path), remote_path)
                    
                    # 設置文件權限
                    sftp.chmod(remote_path, 0o600)
                    
                    logger.info(f"Session文件已上傳到服務器 {node.node_id}: {remote_path}")
                    return True, remote_path
                finally:
                    sftp.close()
            finally:
                ssh.close()
        except Exception as e:
            error_msg = f"上傳session文件到服務器 {node.node_id} 失敗: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def auto_upload_and_assign(
        self, 
        session_file: str,
        account_id: Optional[str] = None
    ) -> Tuple[Optional[ServerNode], Optional[str], str]:
        """
        自動上傳session文件並分配到最適合的服務器
        
        Returns:
            (server_node, remote_path, error_message)
        """
        # 找到最適合的服務器
        best_server = self.find_best_server()
        
        if not best_server:
            error_msg = "沒有可用的服務器（所有服務器已滿或不可用）"
            logger.warning(error_msg)
            return None, None, error_msg
        
        # 上傳文件
        success, result = self.upload_session_to_server(session_file, best_server, account_id)
        
        if success:
            logger.info(f"Session文件已自動分配到服務器 {best_server.node_id}")
            return best_server, result, ""
        else:
            return None, None, result

