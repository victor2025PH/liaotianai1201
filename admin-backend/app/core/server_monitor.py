"""
服务器监控器
定期检查服务器健康状态，收集服务器资源使用情况
"""
import logging
import asyncio
import paramiko
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import time

from app.core.load_balancer import ServerMetrics

logger = logging.getLogger(__name__)


@dataclass
class ServerHealthStatus:
    """服务器健康状态"""
    node_id: str
    is_healthy: bool
    last_check: datetime
    consecutive_failures: int = 0
    error_message: Optional[str] = None


class ServerMonitor:
    """服务器监控器"""
    
    def __init__(
        self,
        master_config_path: Optional[Path] = None,
        check_interval: int = 60,
        health_check_timeout: int = 10,
        failure_threshold: int = 3
    ):
        """
        初始化服务器监控器
        
        Args:
            master_config_path: 主配置文件路径
            check_interval: 检查间隔（秒）
            health_check_timeout: 健康检查超时时间（秒）
            failure_threshold: 故障阈值（连续失败次数）
        """
        if master_config_path is None:
            # 从 admin-backend/app/core/server_monitor.py 到项目根目录
            # __file__ = admin-backend/app/core/server_monitor.py
            # .parent = admin-backend/app/core
            # .parent.parent = admin-backend/app
            # .parent.parent.parent = admin-backend
            # .parent.parent.parent.parent = 项目根目录
            project_root = Path(__file__).parent.parent.parent.parent
            master_config_path = project_root / "data" / "master_config.json"
        
        self.master_config_path = Path(master_config_path) if master_config_path else None
        self.check_interval = check_interval
        self.health_check_timeout = health_check_timeout
        self.failure_threshold = failure_threshold
        
        self.server_configs: Dict = {}
        self.server_metrics_cache: Dict[str, ServerMetrics] = {}
        self.server_health_status: Dict[str, ServerHealthStatus] = {}
        self.last_check_time: Dict[str, datetime] = {}
        self.network_latency_cache: Dict[str, Tuple[float, datetime]] = {}  # {node_id: (latency, timestamp)}
        self.latency_cache_ttl = 300  # 延迟缓存TTL（秒）
        
        self._load_server_configs()
    
    def _load_server_configs(self):
        """加载服务器配置"""
        if not self.master_config_path.exists():
            logger.warning(f"主配置文件不存在: {self.master_config_path}")
            return
        
        try:
            with open(self.master_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.server_configs = config.get('servers', {})
                logger.info(f"加载了 {len(self.server_configs)} 个服务器配置")
        except Exception as e:
            logger.error(f"加载服务器配置失败: {e}")
    
    async def check_server_health(self, node_id: str) -> bool:
        """
        检查服务器健康状态
        
        Args:
            node_id: 服务器节点ID
            
        Returns:
            是否健康
        """
        if node_id not in self.server_configs:
            logger.warning(f"服务器 {node_id} 不在配置中")
            return False
        
        config = self.server_configs[node_id]
        host = config.get('host', '')
        user = config.get('user', 'ubuntu')
        password = config.get('password', '')
        
        try:
            # 尝试SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                host, 
                username=user, 
                password=password, 
                timeout=self.health_check_timeout
            )
            ssh.close()
            
            # 更新健康状态
            if node_id not in self.server_health_status:
                self.server_health_status[node_id] = ServerHealthStatus(
                    node_id=node_id,
                    is_healthy=True,
                    last_check=datetime.now()
                )
            else:
                status = self.server_health_status[node_id]
                if status.is_healthy:
                    status.consecutive_failures = 0
                else:
                    status.is_healthy = True
                    status.consecutive_failures = 0
                status.last_check = datetime.now()
                status.error_message = None
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"服务器 {node_id} 健康检查失败: {error_msg}")
            
            # 更新健康状态
            if node_id not in self.server_health_status:
                self.server_health_status[node_id] = ServerHealthStatus(
                    node_id=node_id,
                    is_healthy=False,
                    last_check=datetime.now(),
                    consecutive_failures=1,
                    error_message=error_msg
                )
            else:
                status = self.server_health_status[node_id]
                status.is_healthy = False
                status.consecutive_failures += 1
                status.last_check = datetime.now()
                status.error_message = error_msg
            
            return False
    
    async def collect_server_metrics(self, node_id: str) -> Optional[ServerMetrics]:
        """
        收集服务器指标
        
        Args:
            node_id: 服务器节点ID
            
        Returns:
            服务器指标，如果失败则返回None
        """
        if node_id not in self.server_configs:
            return None
        
        config = self.server_configs[node_id]
        host = config.get('host', '')
        user = config.get('user', 'ubuntu')
        password = config.get('password', '')
        deploy_dir = config.get('deploy_dir', '/home/ubuntu')
        max_accounts = config.get('max_accounts', 5)
        location = config.get('location', '')
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=self.health_check_timeout)
            
            try:
                # 获取CPU使用率
                stdin, stdout, stderr = ssh.exec_command(
                    "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\([0-9.]*\)%* id.*/\\1/' | awk '{print 100 - $1}'"
                )
                cpu_output = stdout.read().decode().strip()
                cpu_usage = float(cpu_output) if cpu_output else 0.0
                
                # 获取内存使用率
                stdin, stdout, stderr = ssh.exec_command(
                    "free | grep Mem | awk '{printf \"%.2f\", $3/$2 * 100.0}'"
                )
                memory_output = stdout.read().decode().strip()
                memory_usage = float(memory_output) if memory_output else 0.0
                
                # 获取磁盘使用率
                stdin, stdout, stderr = ssh.exec_command(
                    f"df -h {deploy_dir} | tail -1 | awk '{{print $5}}' | sed 's/%//'"
                )
                disk_output = stdout.read().decode().strip()
                disk_usage = float(disk_output) if disk_output else 0.0
                
                # 获取账号数量
                remote_sessions_dir = f"{deploy_dir}/sessions"
                stdin, stdout, stderr = ssh.exec_command(
                    f"ls -1 {remote_sessions_dir}/*.session 2>/dev/null | wc -l"
                )
                account_count = int(stdout.read().decode().strip() or 0)
                
                # 获取网络延迟（使用ping命令测量真实延迟）
                network_latency = self._measure_network_latency(node_id, host)
                
                # 获取健康状态
                health_status = self.server_health_status.get(node_id)
                failure_count = health_status.consecutive_failures if health_status else 0
                
                metrics = ServerMetrics(
                    node_id=node_id,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    disk_usage=disk_usage,
                    current_accounts=account_count,
                    max_accounts=max_accounts,
                    network_latency=network_latency,
                    response_time=network_latency,  # 使用网络延迟作为响应时间
                    failure_count=failure_count,
                    last_heartbeat=datetime.now().isoformat(),
                    location=location,
                    status="active" if (health_status and health_status.is_healthy) else "error"
                )
                
                # 更新缓存
                self.server_metrics_cache[node_id] = metrics
                self.last_check_time[node_id] = datetime.now()
                
                return metrics
                
            finally:
                ssh.close()
                
        except Exception as e:
            logger.error(f"收集服务器 {node_id} 指标失败: {e}")
            return None
    
    async def check_all_servers(self) -> Dict[str, ServerMetrics]:
        """
        检查所有服务器并收集指标
        
        Returns:
            服务器指标字典
        """
        all_metrics = {}
        
        # 并发检查所有服务器
        tasks = []
        for node_id in self.server_configs.keys():
            tasks.append(self.collect_server_metrics(node_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, (node_id, result) in enumerate(zip(self.server_configs.keys(), results)):
            if isinstance(result, Exception):
                logger.error(f"检查服务器 {node_id} 时出错: {result}")
                # 使用缓存的指标或创建错误指标
                if node_id in self.server_metrics_cache:
                    all_metrics[node_id] = self.server_metrics_cache[node_id]
                else:
                    all_metrics[node_id] = ServerMetrics(
                        node_id=node_id,
                        status="error"
                    )
            elif result:
                all_metrics[node_id] = result
        
        return all_metrics
    
    def get_cached_metrics(self, node_id: str) -> Optional[ServerMetrics]:
        """获取缓存的服务器指标"""
        return self.server_metrics_cache.get(node_id)
    
    def get_all_cached_metrics(self) -> Dict[str, ServerMetrics]:
        """获取所有缓存的服务器指标"""
        return self.server_metrics_cache.copy()
    
    def is_cache_valid(self, node_id: str, max_age_seconds: int = 300) -> bool:
        """
        检查缓存是否有效
        
        Args:
            node_id: 服务器节点ID
            max_age_seconds: 最大缓存年龄（秒）
            
        Returns:
            缓存是否有效
        """
        if node_id not in self.last_check_time:
            return False
        
        age = (datetime.now() - self.last_check_time[node_id]).total_seconds()
        return age < max_age_seconds
    
    def get_server_health_status(self, node_id: str) -> Optional[ServerHealthStatus]:
        """获取服务器健康状态"""
        return self.server_health_status.get(node_id)
    
    def is_server_healthy(self, node_id: str) -> bool:
        """检查服务器是否健康"""
        status = self.server_health_status.get(node_id)
        if not status:
            return False
        return status.is_healthy and status.consecutive_failures < self.failure_threshold
    
    def _measure_network_latency(self, node_id: str, host: str) -> float:
        """
        测量网络延迟（使用ping命令，带缓存）
        
        Args:
            node_id: 服务器节点ID
            host: 服务器地址
            
        Returns:
            网络延迟（毫秒）
        """
        # 检查缓存
        if node_id in self.network_latency_cache:
            latency, timestamp = self.network_latency_cache[node_id]
            age = (datetime.now() - timestamp).total_seconds()
            if age < self.latency_cache_ttl:
                return latency
        
        # 使用ping命令测量延迟
        try:
            import subprocess
            import platform
            
            # 根据操作系统选择ping命令
            if platform.system().lower() == 'windows':
                # Windows: ping -n 1 -w 1000 host
                result = subprocess.run(
                    ['ping', '-n', '1', '-w', '1000', host],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
            else:
                # Linux/Mac: ping -c 1 -W 1 host
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '1', host],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
            
            if result.returncode == 0:
                # 解析ping输出获取延迟
                output = result.stdout
                # 尝试提取时间（格式：time=10.5ms 或 time<1ms）
                import re
                time_match = re.search(r'time[<=]?(\d+\.?\d*)', output)
                if time_match:
                    latency = float(time_match.group(1))
                    # 更新缓存
                    self.network_latency_cache[node_id] = (latency, datetime.now())
                    return latency
                else:
                    # 如果无法解析，使用默认值
                    latency = 50.0  # 默认50ms
                    self.network_latency_cache[node_id] = (latency, datetime.now())
                    return latency
            else:
                # ping失败，使用较大的延迟值
                latency = 1000.0  # 1秒
                self.network_latency_cache[node_id] = (latency, datetime.now())
                return latency
                
        except subprocess.TimeoutExpired:
            # 超时，使用较大的延迟值
            latency = 2000.0  # 2秒
            self.network_latency_cache[node_id] = (latency, datetime.now())
            return latency
        except Exception as e:
            logger.warning(f"测量服务器 {node_id} 网络延迟失败: {e}")
            # 使用默认值
            latency = 100.0  # 默认100ms
            self.network_latency_cache[node_id] = (latency, datetime.now())
            return latency

