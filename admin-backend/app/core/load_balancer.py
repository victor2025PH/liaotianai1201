"""
负载均衡器
计算服务器负载分数，实现多种负载均衡策略
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AllocationStrategy(str, Enum):
    """分配策略类型"""
    LOAD_BALANCE = "load_balance"  # 负载均衡策略（默认）
    LOCATION = "location"  # 地理位置策略
    AFFINITY = "affinity"  # 剧本亲和性策略
    ISOLATION = "isolation"  # 故障隔离策略


@dataclass
class ServerMetrics:
    """服务器指标"""
    node_id: str
    cpu_usage: float = 0.0  # CPU使用率 (0-100)
    memory_usage: float = 0.0  # 内存使用率 (0-100)
    disk_usage: float = 0.0  # 磁盘使用率 (0-100)
    current_accounts: int = 0  # 当前账号数
    max_accounts: int = 5  # 最大账号数
    network_latency: float = 0.0  # 网络延迟 (ms)
    response_time: float = 0.0  # 响应时间 (ms)
    failure_count: int = 0  # 故障次数
    last_heartbeat: Optional[str] = None  # 最后心跳时间
    location: str = ""  # 地理位置
    status: str = "active"  # 状态: active, inactive, error


@dataclass
class LoadScore:
    """负载分数"""
    total_score: float  # 总分数 (0-100, 越低越好)
    cpu_score: float
    memory_score: float
    account_score: float
    disk_score: float
    network_score: float
    stability_score: float


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(
        self,
        cpu_weight: float = 0.3,
        memory_weight: float = 0.3,
        account_weight: float = 0.3,
        disk_weight: float = 0.1,
        network_weight: float = 0.0,  # 可选
        stability_weight: float = 0.0  # 可选
    ):
        """
        初始化负载均衡器
        
        Args:
            cpu_weight: CPU权重
            memory_weight: 内存权重
            account_weight: 账号权重
            disk_weight: 磁盘权重
            network_weight: 网络权重
            stability_weight: 稳定性权重
        """
        self.cpu_weight = cpu_weight
        self.memory_weight = memory_weight
        self.account_weight = account_weight
        self.disk_weight = disk_weight
        self.network_weight = network_weight
        self.stability_weight = stability_weight
        
        # 验证权重总和为1.0
        total_weight = (
            cpu_weight + memory_weight + account_weight + 
            disk_weight + network_weight + stability_weight
        )
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"权重总和不为1.0: {total_weight}, 将自动归一化")
            # 自动归一化
            self.cpu_weight /= total_weight
            self.memory_weight /= total_weight
            self.account_weight /= total_weight
            self.disk_weight /= total_weight
            if network_weight > 0:
                self.network_weight /= total_weight
            if stability_weight > 0:
                self.stability_weight /= total_weight
    
    def calculate_load_score(self, metrics: ServerMetrics) -> LoadScore:
        """
        计算服务器负载分数
        
        Args:
            metrics: 服务器指标
            
        Returns:
            负载分数对象
        """
        # CPU分数 (0-100)
        cpu_score = metrics.cpu_usage
        
        # 内存分数 (0-100)
        memory_score = metrics.memory_usage
        
        # 账号分数 (0-100)
        if metrics.max_accounts > 0:
            account_score = (metrics.current_accounts / metrics.max_accounts) * 100
        else:
            account_score = 100.0  # 如果没有最大限制，认为已满
        
        # 磁盘分数 (0-100)
        disk_score = metrics.disk_usage
        
        # 网络分数 (0-100, 延迟越高分数越高)
        # 假设延迟超过1000ms为100分，0ms为0分
        if metrics.network_latency > 0:
            network_score = min(metrics.network_latency / 10.0, 100.0)
        else:
            network_score = 0.0
        
        # 稳定性分数 (0-100, 故障次数越多分数越高)
        # 假设故障次数超过10次为100分
        stability_score = min(metrics.failure_count * 10.0, 100.0)
        
        # 计算总分数
        total_score = (
            cpu_score * self.cpu_weight +
            memory_score * self.memory_weight +
            account_score * self.account_weight +
            disk_score * self.disk_weight
        )
        
        # 如果启用了网络权重，加入网络分数
        if self.network_weight > 0:
            total_score += network_score * self.network_weight
        
        # 如果启用了稳定性权重，加入稳定性分数
        if self.stability_weight > 0:
            total_score += stability_score * self.stability_weight
        
        return LoadScore(
            total_score=total_score,
            cpu_score=cpu_score,
            memory_score=memory_score,
            account_score=account_score,
            disk_score=disk_score,
            network_score=network_score,
            stability_score=stability_score
        )
    
    def select_best_server(
        self,
        servers: List[ServerMetrics],
        strategy: AllocationStrategy = AllocationStrategy.LOAD_BALANCE,
        account_location: Optional[str] = None,
        script_id: Optional[str] = None,
        exclude_servers: Optional[List[str]] = None,
        server_scripts: Optional[Dict[str, List[str]]] = None
    ) -> Optional[ServerMetrics]:
        """
        选择最优服务器
        
        Args:
            servers: 服务器列表
            strategy: 分配策略
            account_location: 账号地理位置（用于地理位置策略）
            script_id: 剧本ID（用于亲和性策略）
            exclude_servers: 排除的服务器ID列表
            
        Returns:
            最优服务器指标，如果没有可用服务器则返回None
        """
        if exclude_servers is None:
            exclude_servers = []
        
        # 过滤不可用服务器
        # 1. 只选择状态为 active 的服务器（停用了的服务器会被跳过）
        # 2. 只选择未满的服务器（current_accounts < max_accounts，满了的服务器会被跳过）
        # 3. 排除指定的服务器列表
        available_servers = [
            s for s in servers
            if s.status == "active" 
            and s.current_accounts < s.max_accounts
            and s.node_id not in exclude_servers
        ]
        
        if not available_servers:
            # 记录详细信息，便于调试
            total_servers = len(servers)
            inactive_servers = [s.node_id for s in servers if s.status != "active"]
            full_servers = [s.node_id for s in servers if s.status == "active" and s.current_accounts >= s.max_accounts]
            logger.warning(
                f"没有可用的服务器。总服务器数: {total_servers}, "
                f"停用服务器: {inactive_servers}, 已满服务器: {full_servers}"
            )
            return None
        
        logger.debug(
            f"找到 {len(available_servers)} 个可用服务器: "
            f"{[s.node_id for s in available_servers]}"
        )
        
        # 根据策略选择服务器
        if strategy == AllocationStrategy.LOAD_BALANCE:
            return self._select_by_load_balance(available_servers)
        elif strategy == AllocationStrategy.LOCATION:
            return self._select_by_location(available_servers, account_location)
        elif strategy == AllocationStrategy.AFFINITY:
            return self._select_by_affinity(available_servers, script_id, server_scripts)
        elif strategy == AllocationStrategy.ISOLATION:
            return self._select_by_isolation(available_servers)
        else:
            # 默认使用负载均衡
            return self._select_by_load_balance(available_servers)
    
    def _select_by_load_balance(self, servers: List[ServerMetrics]) -> Optional[ServerMetrics]:
        """负载均衡策略：选择负载最轻的服务器"""
        best_server = None
        min_score = float('inf')
        
        for server in servers:
            score = self.calculate_load_score(server)
            if score.total_score < min_score:
                min_score = score.total_score
                best_server = server
        
        if best_server:
            logger.info(f"选择服务器 {best_server.node_id}, 负载分数: {min_score:.2f}")
        
        return best_server
    
    def _select_by_location(self, servers: List[ServerMetrics], account_location: Optional[str]) -> Optional[ServerMetrics]:
        """地理位置策略：选择最近的服务器"""
        if not account_location:
            # 如果没有提供账号位置，回退到负载均衡
            return self._select_by_load_balance(servers)
        
        # 优先选择相同位置的服务器
        same_location_servers = [s for s in servers if s.location == account_location]
        if same_location_servers:
            return self._select_by_load_balance(same_location_servers)
        
        # 如果没有相同位置的，使用负载均衡
        return self._select_by_load_balance(servers)
    
    def _select_by_affinity(
        self, 
        servers: List[ServerMetrics], 
        script_id: Optional[str],
        server_scripts: Optional[Dict[str, List[str]]] = None
    ) -> Optional[ServerMetrics]:
        """
        剧本亲和性策略：优先选择已有相同剧本的服务器
        
        Args:
            servers: 服务器列表
            script_id: 剧本ID
            server_scripts: 每个服务器上的剧本列表 {server_id: [script_id1, script_id2, ...]}
        """
        if not script_id:
            # 如果没有提供剧本ID，回退到负载均衡
            return self._select_by_load_balance(servers)
        
        if not server_scripts:
            # 如果没有提供服务器剧本信息，使用负载均衡
            logger.warning("剧本亲和性策略需要服务器剧本信息，使用负载均衡策略")
            return self._select_by_load_balance(servers)
        
        # 优先选择已有相同剧本的服务器
        same_script_servers = []
        for server in servers:
            server_script_list = server_scripts.get(server.node_id, [])
            if script_id in server_script_list:
                same_script_servers.append(server)
        
        if same_script_servers:
            # 在已有相同剧本的服务器中选择负载最轻的
            logger.info(
                f"剧本亲和性策略：找到 {len(same_script_servers)} 个已有剧本 {script_id} 的服务器: "
                f"{[s.node_id for s in same_script_servers]}"
            )
            best_server = self._select_by_load_balance(same_script_servers)
            if best_server:
                logger.info(
                    f"剧本亲和性策略：选择服务器 {best_server.node_id} "
                    f"(已有剧本 {script_id}, 账号数: {best_server.current_accounts}/{best_server.max_accounts})"
                )
            return best_server
        else:
            # 如果都没有相同剧本，使用负载均衡（自动分配到下一个服务器）
            logger.info(
                f"剧本亲和性策略：没有服务器已有剧本 {script_id}，"
                f"使用负载均衡策略从 {len(servers)} 个可用服务器中选择"
            )
            best_server = self._select_by_load_balance(servers)
            if best_server:
                logger.info(
                    f"负载均衡策略：选择服务器 {best_server.node_id} "
                    f"(账号数: {best_server.current_accounts}/{best_server.max_accounts})"
                )
            return best_server
    
    def _select_by_isolation(self, servers: List[ServerMetrics]) -> Optional[ServerMetrics]:
        """故障隔离策略：避免选择最近故障的服务器"""
        # 过滤掉最近故障的服务器（故障次数 > 0）
        healthy_servers = [s for s in servers if s.failure_count == 0]
        
        if healthy_servers:
            return self._select_by_load_balance(healthy_servers)
        
        # 如果所有服务器都有故障记录，选择故障次数最少的
        min_failures = min(s.failure_count for s in servers)
        least_failure_servers = [s for s in servers if s.failure_count == min_failures]
        return self._select_by_load_balance(least_failure_servers)
    
    def get_server_rankings(self, servers: List[ServerMetrics]) -> List[tuple]:
        """
        获取服务器排名（按负载分数排序）
        
        Args:
            servers: 服务器列表
            
        Returns:
            [(server, score), ...] 按分数升序排列
        """
        rankings = []
        for server in servers:
            if server.status == "active" and server.current_accounts < server.max_accounts:
                score = self.calculate_load_score(server)
                rankings.append((server, score.total_score))
        
        # 按分数升序排序
        rankings.sort(key=lambda x: x[1])
        return rankings

