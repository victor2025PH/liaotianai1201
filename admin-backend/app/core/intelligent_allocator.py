"""
智能分配引擎
实时监控所有服务器状态，计算服务器负载分数，执行智能分配算法
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.server_monitor import ServerMonitor
from app.core.load_balancer import LoadBalancer, AllocationStrategy, ServerMetrics
from app.models.group_ai import GroupAIAccount, AllocationHistory

logger = logging.getLogger(__name__)


@dataclass
class AllocationResult:
    """分配结果"""
    success: bool
    server_id: Optional[str] = None
    remote_path: Optional[str] = None
    load_score: Optional[float] = None
    message: str = ""
    error: Optional[str] = None


@dataclass
class RebalanceResult:
    """重新分配结果"""
    success: bool
    migrated_accounts: List[str] = None
    failed_accounts: List[str] = None
    message: str = ""
    
    def __post_init__(self):
        if self.migrated_accounts is None:
            self.migrated_accounts = []
        if self.failed_accounts is None:
            self.failed_accounts = []


class IntelligentAllocator:
    """智能分配引擎"""
    
    def __init__(
        self,
        master_config_path: Optional[Path] = None,
        check_interval: int = 60
    ):
        """
        初始化智能分配引擎
        
        Args:
            master_config_path: 主配置文件路径
            check_interval: 服务器检查间隔（秒）
        """
        # 如果未提供路径，自动解析
        if master_config_path is None:
            # 从 admin-backend/app/core/intelligent_allocator.py 到项目根目录
            project_root = Path(__file__).parent.parent.parent.parent
            master_config_path = project_root / "data" / "master_config.json"
        
        self.master_config_path = Path(master_config_path) if master_config_path else None
        self.config = self._load_config()
        
        self.server_monitor = ServerMonitor(
            master_config_path=self.master_config_path,
            check_interval=self.config.get("allocation", {}).get("health_check_interval", check_interval)
        )
        self.load_balancer = LoadBalancer()
        self.default_strategy = self._get_default_strategy()
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        import json
        try:
            if self.master_config_path and self.master_config_path.exists():
                with open(self.master_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"配置文件不存在: {self.master_config_path}，使用默认配置")
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
        return {}
    
    def _get_default_strategy(self) -> AllocationStrategy:
        """获取默认分配策略"""
        default_strategy_str = self.config.get("allocation", {}).get("default_strategy", "load_balance")
        strategy_map = {
            "load_balance": AllocationStrategy.LOAD_BALANCE,
            "location": AllocationStrategy.LOCATION,
            "affinity": AllocationStrategy.AFFINITY,
            "isolation": AllocationStrategy.ISOLATION
        }
        return strategy_map.get(default_strategy_str, AllocationStrategy.LOAD_BALANCE)
    
    def get_strategy_for_account_type(self, account_type: Optional[str] = None) -> AllocationStrategy:
        """
        根据账号类型获取分配策略
        
        Args:
            account_type: 账号类型（high_priority, batch, 或其他）
            
        Returns:
            分配策略
        """
        if not account_type:
            return self.default_strategy
        
        account_type_strategies = self.config.get("allocation", {}).get("account_type_strategies", {})
        strategy_str = account_type_strategies.get(account_type, account_type_strategies.get("default", "load_balance"))
        
        strategy_map = {
            "load_balance": AllocationStrategy.LOAD_BALANCE,
            "location": AllocationStrategy.LOCATION,
            "affinity": AllocationStrategy.AFFINITY,
            "isolation": AllocationStrategy.ISOLATION
        }
        
        return strategy_map.get(strategy_str, self.default_strategy)
    
    async def allocate_account(
        self,
        account_id: str,
        session_file: str,
        script_id: Optional[str] = None,
        strategy: Optional[AllocationStrategy] = None,
        account_location: Optional[str] = None,
        account_type: Optional[str] = None,
        db: Optional[Session] = None
    ) -> AllocationResult:
        """
        分配账号到最优服务器
        
        Args:
            account_id: 账号ID
            session_file: Session文件路径
            script_id: 剧本ID（用于亲和性策略）
            strategy: 分配策略（如果为None，则根据account_type或默认策略）
            account_location: 账号地理位置（用于地理位置策略）
            account_type: 账号类型（用于选择策略）
            db: 数据库会话
            
        Returns:
            分配结果
        """
        try:
            # 如果没有指定策略，根据账号类型或使用默认策略
            if strategy is None:
                strategy = self.get_strategy_for_account_type(account_type)
            # 1. 检查账号是否已分配
            if db:
                existing_account = db.query(GroupAIAccount).filter(
                    GroupAIAccount.account_id == account_id
                ).first()
                if existing_account and existing_account.server_id:
                    return AllocationResult(
                        success=False,
                        message=f"账号 {account_id} 已分配到服务器 {existing_account.server_id}",
                        error="账号已分配"
                    )
            
            # 2. 获取所有服务器指标
            server_metrics_dict = await self.server_monitor.check_all_servers()
            
            if not server_metrics_dict:
                return AllocationResult(
                    success=False,
                    message="没有可用的服务器",
                    error="无可用服务器"
                )
            
            # 转换为列表
            server_metrics_list = list(server_metrics_dict.values())
            
            # 3. 如果使用亲和性策略，查询每个服务器上的剧本
            server_scripts = None
            if strategy == AllocationStrategy.AFFINITY and script_id and db:
                server_scripts = self._get_server_scripts(db)
            
            # 4. 使用负载均衡器选择最优服务器
            best_server_metrics = self.load_balancer.select_best_server(
                servers=server_metrics_list,
                strategy=strategy,
                account_location=account_location,
                script_id=script_id,
                server_scripts=server_scripts
            )
            
            if not best_server_metrics:
                return AllocationResult(
                    success=False,
                    message="没有可用的服务器（所有服务器已满或不可用）",
                    error="无可用服务器"
                )
            
            # 5. 获取对应的ServerNode对象
            best_server_node = self._get_server_node(best_server_metrics.node_id)
            if not best_server_node:
                return AllocationResult(
                    success=False,
                    message=f"无法找到服务器节点 {best_server_metrics.node_id}",
                    error="服务器节点不存在"
                )
            
            # 6. 计算负载分数
            load_score = self.load_balancer.calculate_load_score(best_server_metrics)
            
            # 7. 上传Session文件到服务器
            # 延迟导入避免循环依赖
            if not hasattr(self, '_session_uploader'):
                from app.api.group_ai.session_uploader import SessionUploader
                self._session_uploader = SessionUploader(master_config_path=self.master_config_path)
            
            success, remote_path = self._session_uploader.upload_session_to_server(
                session_file=session_file,
                node=best_server_node,
                account_id=account_id
            )
            
            if not success:
                return AllocationResult(
                    success=False,
                    message=f"上传Session文件失败: {remote_path}",
                    error=remote_path
                )
            
            # 8. 更新数据库
            if db:
                # 更新账号的server_id
                account = db.query(GroupAIAccount).filter(
                    GroupAIAccount.account_id == account_id
                ).first()
                if account:
                    account.server_id = best_server_metrics.node_id
                
                # 记录分配历史
                allocation_history = AllocationHistory(
                    account_id=account_id,
                    server_id=best_server_metrics.node_id,
                    allocation_type="initial",
                    load_score=load_score.total_score,
                    strategy=strategy.value,
                    reason="智能分配"
                )
                db.add(allocation_history)
                db.commit()
            
            logger.info(
                f"账号 {account_id} 已成功分配到服务器 {best_server_metrics.node_id}, "
                f"负载分数: {load_score.total_score:.2f}"
            )
            
            return AllocationResult(
                success=True,
                server_id=best_server_metrics.node_id,
                remote_path=remote_path,
                load_score=load_score.total_score,
                message=f"账号已成功分配到服务器 {best_server_metrics.node_id}"
            )
            
        except Exception as e:
            logger.error(f"分配账号 {account_id} 时出错: {e}", exc_info=True)
            return AllocationResult(
                success=False,
                message=f"分配失败: {str(e)}",
                error=str(e)
            )
    
    async def rebalance_accounts(
        self,
        db: Session,
        threshold: float = 30.0,
        max_migrations: int = 10
    ) -> RebalanceResult:
        """
        重新平衡账号分布
        
        Args:
            db: 数据库会话
            threshold: 负载差异阈值（百分比）
            max_migrations: 最大迁移数量
            
        Returns:
            重新分配结果
        """
        try:
            # 1. 获取所有服务器指标
            server_metrics_dict = await self.server_monitor.check_all_servers()
            
            if len(server_metrics_dict) < 2:
                return RebalanceResult(
                    success=False,
                    message="需要至少2个服务器才能进行重新平衡"
                )
            
            # 2. 计算每个服务器的负载分数
            server_scores = {}
            for node_id, metrics in server_metrics_dict.items():
                score = self.load_balancer.calculate_load_score(metrics)
                server_scores[node_id] = {
                    'metrics': metrics,
                    'score': score.total_score
                }
            
            # 3. 找出负载最高和最低的服务器
            sorted_servers = sorted(
                server_scores.items(),
                key=lambda x: x[1]['score']
            )
            
            min_server_id, min_server_data = sorted_servers[0]
            max_server_id, max_server_data = sorted_servers[-1]
            
            # 4. 检查是否需要重新平衡
            score_diff = max_server_data['score'] - min_server_data['score']
            if score_diff < threshold:
                return RebalanceResult(
                    success=True,
                    message=f"服务器负载均衡，无需重新分配（差异: {score_diff:.2f}%）"
                )
            
            # 5. 找出需要迁移的账号
            accounts_to_migrate = db.query(GroupAIAccount).filter(
                and_(
                    GroupAIAccount.server_id == max_server_id,
                    GroupAIAccount.active == True
                )
            ).limit(max_migrations).all()
            
            if not accounts_to_migrate:
                return RebalanceResult(
                    success=True,
                    message="没有可迁移的账号"
                )
            
            # 6. 执行迁移
            migrated_accounts = []
            failed_accounts = []
            
            for account in accounts_to_migrate:
                try:
                    # 获取Session文件路径
                    session_file = account.session_file
                    
                    # 获取目标服务器节点
                    target_server_node = self._get_server_node(min_server_id)
                    if not target_server_node:
                        failed_accounts.append(account.account_id)
                        continue
                    
                    # 上传Session文件到新服务器
                    # 延迟导入避免循环依赖
                    if not hasattr(self, '_session_uploader'):
                        from app.api.group_ai.session_uploader import SessionUploader
                        self._session_uploader = SessionUploader(master_config_path=self.master_config_path)
                    
                    success, remote_path = self._session_uploader.upload_session_to_server(
                        session_file=session_file,
                        node=target_server_node,
                        account_id=account.account_id
                    )
                    
                    if success:
                        # 更新数据库
                        account.server_id = min_server_id
                        
                        # 记录分配历史
                        allocation_history = AllocationHistory(
                            account_id=account.account_id,
                            server_id=min_server_id,
                            allocation_type="rebalance",
                            load_score=min_server_data['score'],
                            strategy="load_balance",
                            reason=f"从 {max_server_id} 迁移到 {min_server_id}"
                        )
                        db.add(allocation_history)
                        
                        migrated_accounts.append(account.account_id)
                        logger.info(
                            f"账号 {account.account_id} 已从 {max_server_id} 迁移到 {min_server_id}"
                        )
                    else:
                        failed_accounts.append(account.account_id)
                        logger.error(f"迁移账号 {account.account_id} 失败: {remote_path}")
                        
                except Exception as e:
                    logger.error(f"迁移账号 {account.account_id} 时出错: {e}", exc_info=True)
                    failed_accounts.append(account.account_id)
            
            # 提交数据库更改
            db.commit()
            
            return RebalanceResult(
                success=len(migrated_accounts) > 0,
                migrated_accounts=migrated_accounts,
                failed_accounts=failed_accounts,
                message=f"成功迁移 {len(migrated_accounts)} 个账号，失败 {len(failed_accounts)} 个"
            )
            
        except Exception as e:
            logger.error(f"重新平衡账号时出错: {e}", exc_info=True)
            db.rollback()
            return RebalanceResult(
                success=False,
                message=f"重新平衡失败: {str(e)}"
            )
    
    def _get_server_node(self, node_id: str):
        """获取ServerNode对象（延迟导入避免循环依赖）"""
        # 延迟导入避免循环依赖
        from app.api.group_ai.session_uploader import SessionUploader, ServerNode
        if not hasattr(self, '_session_uploader'):
            self._session_uploader = SessionUploader(master_config_path=self.master_config_path)
        return self._session_uploader.servers.get(node_id)
    
    def _get_server_scripts(self, db: Session) -> Dict[str, List[str]]:
        """
        获取每个服务器上的剧本列表
        
        Args:
            db: 数据库会话
            
        Returns:
            {server_id: [script_id1, script_id2, ...]}
        """
        server_scripts: Dict[str, List[str]] = {}
        
        try:
            # 查询所有已分配的账号及其剧本
            accounts = db.query(GroupAIAccount).filter(
                GroupAIAccount.server_id.isnot(None),
                GroupAIAccount.script_id.isnot(None)
            ).all()
            
            # 按服务器分组
            for account in accounts:
                server_id = account.server_id
                script_id = account.script_id
                
                if server_id not in server_scripts:
                    server_scripts[server_id] = []
                
                # 去重
                if script_id not in server_scripts[server_id]:
                    server_scripts[server_id].append(script_id)
            
            logger.debug(f"服务器剧本分布: {server_scripts}")
            return server_scripts
            
        except Exception as e:
            logger.error(f"查询服务器剧本失败: {e}", exc_info=True)
            return {}
    
    async def get_server_rankings(self) -> List[Tuple[str, float]]:
        """
        获取服务器排名（按负载分数排序）
        
        Returns:
            [(server_id, score), ...] 按分数升序排列
        """
        server_metrics_dict = await self.server_monitor.check_all_servers()
        rankings = self.load_balancer.get_server_rankings(
            list(server_metrics_dict.values())
        )
        return [(server.node_id, score) for server, score in rankings]

