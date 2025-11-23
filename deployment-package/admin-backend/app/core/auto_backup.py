"""
自动备份和恢复系统
支持数据库、Session文件、配置文件的自动备份和恢复
"""
import logging
import shutil
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json
import gzip

logger = logging.getLogger(__name__)


class BackupManager:
    """备份管理器"""
    
    def __init__(
        self,
        backup_dir: str = "backups",
        retention_days: int = 30,
        auto_backup_enabled: bool = True,
        backup_interval_hours: int = 24
    ):
        """
        初始化备份管理器
        
        Args:
            backup_dir: 备份目录
            retention_days: 保留天数
            auto_backup_enabled: 是否启用自动备份
            backup_interval_hours: 备份间隔（小时）
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self.auto_backup_enabled = auto_backup_enabled
        self.backup_interval_hours = backup_interval_hours
        self._backup_task: Optional[asyncio.Task] = None
    
    async def backup_database(self, database_url: str) -> Optional[Path]:
        """备份数据库"""
        if not database_url:
            logger.warning("数据库 URL 未配置，跳过数据库备份")
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"database_{timestamp}.sql.gz"
            
            # 解析数据库 URL
            if database_url.startswith("postgresql://"):
                # PostgreSQL 备份
                import os
                from urllib.parse import urlparse
                
                parsed = urlparse(database_url)
                db_name = parsed.path.lstrip("/")
                db_user = parsed.username
                db_host = parsed.hostname
                db_port = parsed.port or 5432
                
                # 使用 pg_dump
                env = os.environ.copy()
                if parsed.password:
                    env["PGPASSWORD"] = parsed.password
                
                cmd = [
                    "pg_dump",
                    "-h", db_host,
                    "-p", str(db_port),
                    "-U", db_user,
                    "-d", db_name,
                    "-F", "c",  # 自定义格式
                    "-f", str(backup_file.with_suffix(""))
                ]
                
                result = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    # 压缩备份文件
                    with open(backup_file.with_suffix(""), "rb") as f_in:
                        with gzip.open(backup_file, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    backup_file.with_suffix("").unlink()
                    
                    logger.info(f"数据库备份完成: {backup_file}")
                    return backup_file
                else:
                    logger.error(f"数据库备份失败: {result.stderr}")
                    return None
            else:
                logger.warning(f"不支持的数据库类型: {database_url.split('://')[0]}")
                return None
                
        except Exception as e:
            logger.error(f"数据库备份异常: {e}", exc_info=True)
            return None
    
    async def backup_sessions(self, sessions_dir: str = "sessions") -> Optional[Path]:
        """备份 Session 文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"sessions_{timestamp}.tar.gz"
            
            sessions_path = Path(sessions_dir)
            if not sessions_path.exists():
                logger.warning(f"Session 目录不存在: {sessions_dir}")
                return None
            
            # 创建压缩包
            import tarfile
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(sessions_path, arcname="sessions")
            
            logger.info(f"Session 文件备份完成: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Session 文件备份异常: {e}", exc_info=True)
            return None
    
    async def backup_config(self, config_files: List[str]) -> Optional[Path]:
        """备份配置文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"config_{timestamp}.tar.gz"
            
            import tarfile
            with tarfile.open(backup_file, "w:gz") as tar:
                for config_file in config_files:
                    config_path = Path(config_file)
                    if config_path.exists():
                        tar.add(config_path, arcname=config_path.name)
            
            logger.info(f"配置文件备份完成: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"配置文件备份异常: {e}", exc_info=True)
            return None
    
    async def full_backup(
        self,
        database_url: Optional[str] = None,
        sessions_dir: str = "sessions",
        config_files: Optional[List[str]] = None
    ) -> Dict[str, Optional[Path]]:
        """完整备份"""
        results = {}
        
        if database_url:
            results["database"] = await self.backup_database(database_url)
        
        results["sessions"] = await self.backup_sessions(sessions_dir)
        
        if config_files:
            results["config"] = await self.backup_config(config_files)
        
        # 记录备份元数据
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "backups": {k: str(v) if v else None for k, v in results.items()}
        }
        metadata_file = self.backup_dir / f"backup_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        return results
    
    async def cleanup_old_backups(self):
        """清理旧备份"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0
            
            for backup_file in self.backup_dir.glob("*"):
                if backup_file.is_file():
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        backup_file.unlink()
                        deleted_count += 1
                        logger.debug(f"删除旧备份: {backup_file}")
            
            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 个旧备份文件")
                
        except Exception as e:
            logger.error(f"清理旧备份异常: {e}", exc_info=True)
    
    async def restore_database(self, backup_file: Path, database_url: str) -> bool:
        """恢复数据库"""
        if not backup_file.exists():
            logger.error(f"备份文件不存在: {backup_file}")
            return False
        
        try:
            # 解压备份文件
            if backup_file.suffix == ".gz":
                import gzip
                temp_file = backup_file.with_suffix("")
                with gzip.open(backup_file, "rb") as f_in:
                    with open(temp_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = temp_file
            else:
                restore_file = backup_file
            
            # 恢复数据库
            if database_url.startswith("postgresql://"):
                import os
                from urllib.parse import urlparse
                
                parsed = urlparse(database_url)
                db_name = parsed.path.lstrip("/")
                db_user = parsed.username
                db_host = parsed.hostname
                db_port = parsed.port or 5432
                
                env = os.environ.copy()
                if parsed.password:
                    env["PGPASSWORD"] = parsed.password
                
                cmd = [
                    "pg_restore",
                    "-h", db_host,
                    "-p", str(db_port),
                    "-U", db_user,
                    "-d", db_name,
                    "-c",  # 清理现有数据
                    str(backup_file)
                ]
                
                result = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode == 0:
                    logger.info(f"数据库恢复完成: {backup_file}")
                    if temp_file and temp_file.exists():
                        temp_file.unlink()  # 删除临时文件
                    return True
                else:
                    logger.error(f"数据库恢复失败: {result.stderr}")
                    if temp_file and temp_file.exists():
                        temp_file.unlink()
                    return False
            elif database_url.startswith("sqlite:///"):
                # SQLite 恢复
                import shutil
                db_path = database_url.replace("sqlite:///", "")
                # 备份原数据库
                if Path(db_path).exists():
                    shutil.copy(db_path, f"{db_path}.backup")
                # 恢复
                if restore_file.suffix == ".gz":
                    with gzip.open(restore_file, "rb") as f_in:
                        with open(db_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                else:
                    shutil.copy(restore_file, db_path)
                logger.info(f"SQLite 数据库恢复完成: {db_path}")
                if temp_file and temp_file.exists():
                    temp_file.unlink()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"数据库恢复异常: {e}", exc_info=True)
            return False
    
    async def start_auto_backup(
        self,
        database_url: Optional[str] = None,
        sessions_dir: str = "sessions",
        config_files: Optional[List[str]] = None
    ):
        """启动自动备份任务"""
        if not self.auto_backup_enabled:
            logger.info("自动备份未启用")
            return
        
        # 立即执行一次备份
        try:
            logger.info("执行初始备份...")
            await self.full_backup(database_url, sessions_dir, config_files)
            await self.cleanup_old_backups()
        except Exception as e:
            logger.warning(f"初始备份失败: {e}")
        
        async def backup_loop():
            while True:
                try:
                    await asyncio.sleep(self.backup_interval_hours * 3600)
                    logger.info("开始自动备份...")
                    await self.full_backup(database_url, sessions_dir, config_files)
                    await self.cleanup_old_backups()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"自动备份异常: {e}", exc_info=True)
        
        self._backup_task = asyncio.create_task(backup_loop())
        logger.info(f"自动备份已启动，间隔: {self.backup_interval_hours} 小时")
    
    def stop_auto_backup(self):
        """停止自动备份任务"""
        if self._backup_task:
            self._backup_task.cancel()
            logger.info("自动备份已停止")


# 全局备份管理器实例
_backup_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """获取备份管理器实例"""
    global _backup_manager
    if _backup_manager is None:
        from app.core.config import get_settings
        settings = get_settings()
        backup_dir = getattr(settings, "backup_dir", "backups")
        retention_days = getattr(settings, "backup_retention_days", 30)
        auto_backup = getattr(settings, "auto_backup_enabled", True)
        _backup_manager = BackupManager(
            backup_dir=backup_dir,
            retention_days=retention_days,
            auto_backup_enabled=auto_backup
        )
    return _backup_manager

