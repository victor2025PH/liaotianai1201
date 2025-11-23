"""
自动故障恢复
定期检查服务器健康状态，自动迁移故障服务器上的账号
"""
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.intelligent_allocator import IntelligentAllocator
from app.core.server_monitor import ServerMonitor
from app.models.group_ai import GroupAIAccount, AllocationHistory

logger = logging.getLogger(__name__)


class FaultRecoveryService:
    """故障恢复服务"""
    
    def __init__(
        self,
        allocator: IntelligentAllocator,
        check_interval: int = 300,  # 5分钟检查一次
        failure_threshold: int = 3,  # 连续失败3次才认为故障
        recovery_enabled: bool = True
    ):
        """
        初始化故障恢复服务
        
        Args:
            allocator: 智能分配引擎
            check_interval: 检查间隔（秒）
            failure_threshold: 故障阈值（连续失败次数）
            recovery_enabled: 是否启用自动恢复
        """
        self.allocator = allocator
        self.server_monitor = allocator.server_monitor
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.recovery_enabled = recovery_enabled
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动故障恢复服务"""
        if self.is_running:
            logger.warning("故障恢复服务已在运行")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._recovery_loop())
        logger.info("故障恢复服务已启动")
    
    async def stop(self):
        """停止故障恢复服务"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("故障恢复服务已停止")
    
    async def _recovery_loop(self):
        """故障恢复循环"""
        while self.is_running:
            try:
                await self.check_and_recover()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"故障恢复循环出错: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    async def check_and_recover(self, db: Optional[Session] = None) -> Dict[str, any]:
        """
        检查并恢复故障服务器
        
        Args:
            db: 数据库会话（如果提供，则执行恢复操作）
            
        Returns:
            恢复结果
        """
        if not self.recovery_enabled:
            return {"enabled": False, "message": "故障恢复未启用"}
        
        try:
            # 1. 检查所有服务器健康状态
            server_metrics = await self.server_monitor.check_all_servers()
            
            # 2. 找出故障服务器
            failed_servers = []
            for node_id, metrics in server_metrics.items():
                health_status = self.server_monitor.get_server_health_status(node_id)
                if health_status and not health_status.is_healthy:
                    if health_status.consecutive_failures >= self.failure_threshold:
                        failed_servers.append(node_id)
                        logger.warning(
                            f"检测到故障服务器 {node_id}: "
                            f"连续失败 {health_status.consecutive_failures} 次"
                        )
            
            if not failed_servers:
                return {
                    "success": True,
                    "message": "所有服务器正常",
                    "failed_servers": [],
                    "migrated_accounts": []
                }
            
            # 3. 如果没有提供数据库会话，只返回检测结果
            if not db:
                return {
                    "success": True,
                    "message": f"检测到 {len(failed_servers)} 个故障服务器",
                    "failed_servers": failed_servers,
                    "migrated_accounts": []
                }
            
            # 4. 迁移故障服务器上的账号
            migrated_accounts = []
            failed_migrations = []
            
            for server_id in failed_servers:
                # 查询该服务器上的所有账号
                accounts = db.query(GroupAIAccount).filter(
                    and_(
                        GroupAIAccount.server_id == server_id,
                        GroupAIAccount.active == True
                    )
                ).all()
                
                logger.info(f"服务器 {server_id} 上有 {len(accounts)} 个账号需要迁移")
                
                for account in accounts:
                    try:
                        # 使用智能分配引擎重新分配账号
                        from app.core.load_balancer import AllocationStrategy
                        result = await self.allocator.allocate_account(
                            account_id=account.account_id,
                            session_file=account.session_file,
                            script_id=account.script_id,
                            strategy=AllocationStrategy.LOAD_BALANCE,  # 故障恢复时使用负载均衡策略
                            db=db
                        )
                        
                        if result.success:
                            # 记录迁移历史
                            migration_history = AllocationHistory(
                                account_id=account.account_id,
                                server_id=result.server_id,
                                allocation_type="rebalance",
                                load_score=result.load_score,
                                strategy="fault_recovery",
                                reason=f"服务器 {server_id} 故障，自动迁移"
                            )
                            db.add(migration_history)
                            migrated_accounts.append(account.account_id)
                            logger.info(
                                f"账号 {account.account_id} 已从故障服务器 {server_id} "
                                f"迁移到 {result.server_id}"
                            )
                        else:
                            failed_migrations.append({
                                "account_id": account.account_id,
                                "error": result.message
                            })
                            logger.error(
                                f"迁移账号 {account.account_id} 失败: {result.message}"
                            )
                            
                    except Exception as e:
                        logger.error(
                            f"迁移账号 {account.account_id} 时出错: {e}",
                            exc_info=True
                        )
                        failed_migrations.append({
                            "account_id": account.account_id,
                            "error": str(e)
                        })
            
            # 提交数据库更改
            db.commit()
            
            return {
                "success": True,
                "message": f"成功迁移 {len(migrated_accounts)} 个账号",
                "failed_servers": failed_servers,
                "migrated_accounts": migrated_accounts,
                "failed_migrations": failed_migrations
            }
            
        except Exception as e:
            logger.error(f"故障恢复检查出错: {e}", exc_info=True)
            if db:
                db.rollback()
            return {
                "success": False,
                "message": f"故障恢复检查失败: {str(e)}",
                "failed_servers": [],
                "migrated_accounts": []
            }

