"""
Session 文件访问审计日志模块
记录所有 Session 文件的访问、上传、下载、删除等操作
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """审计操作类型"""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    VIEW = "view"
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"
    ACCESS_DENIED = "access_denied"


class SessionAuditLogger:
    """Session 文件审计日志记录器"""
    
    def __init__(self, audit_log_dir: Optional[Path] = None):
        """
        初始化审计日志记录器
        
        Args:
            audit_log_dir: 审计日志目录（可选，默认使用 logs/audit/）
        """
        if audit_log_dir is None:
            from config import LOGS_DIR
            audit_log_dir = Path(LOGS_DIR) / "audit"
        
        self.audit_log_dir = Path(audit_log_dir)
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置审计日志文件路径（按日期）
        self.log_file = self.audit_log_dir / f"session_audit_{datetime.now().strftime('%Y%m%d')}.log"
    
    def log(
        self,
        user_id: int,
        user_email: str,
        action: AuditAction,
        file_path: str,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        记录审计日志
        
        Args:
            user_id: 用户 ID
            user_email: 用户邮箱
            action: 操作类型
            file_path: 文件路径
            success: 是否成功
            error_message: 错误消息（如果失败）
            metadata: 额外元数据
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "user_email": user_email,
                "action": action.value,
                "file_path": file_path,
                "success": success,
                "error_message": error_message,
                "metadata": metadata or {}
            }
            
            # 写入日志文件（JSON 格式，每行一条）
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            # 同时记录到标准日志
            if success:
                logger.info(
                    f"[审计] 用户 {user_email} ({user_id}) {action.value} "
                    f"文件 {file_path}"
                )
            else:
                logger.warning(
                    f"[审计] 用户 {user_email} ({user_id}) {action.value} "
                    f"文件 {file_path} 失败: {error_message}"
                )
                
        except Exception as e:
            logger.error(f"记录审计日志失败: {e}")
    
    def query_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        file_path: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        查询审计日志
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户 ID 过滤
            action: 操作类型过滤
            file_path: 文件路径过滤
            limit: 返回记录数限制
        
        Returns:
            审计日志记录列表
        """
        results = []
        
        try:
            # 确定要查询的日志文件
            if start_date and end_date:
                # 查询日期范围内的所有日志文件
                current_date = start_date
                log_files = []
                while current_date <= end_date:
                    log_file = self.audit_log_dir / f"session_audit_{current_date.strftime('%Y%m%d')}.log"
                    if log_file.exists():
                        log_files.append(log_file)
                    current_date = current_date.replace(day=current_date.day + 1)
            else:
                # 只查询今天的日志文件
                log_files = [self.log_file] if self.log_file.exists() else []
            
            # 读取并过滤日志
            for log_file in log_files:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        
                        try:
                            entry = json.loads(line)
                            entry_time = datetime.fromisoformat(entry['timestamp'])
                            
                            # 应用过滤条件
                            if start_date and entry_time < start_date:
                                continue
                            if end_date and entry_time > end_date:
                                continue
                            if user_id and entry.get('user_id') != user_id:
                                continue
                            if action and entry.get('action') != action.value:
                                continue
                            if file_path and file_path not in entry.get('file_path', ''):
                                continue
                            
                            results.append(entry)
                            
                            if len(results) >= limit:
                                break
                        except json.JSONDecodeError:
                            continue
                
                if len(results) >= limit:
                    break
            
            # 按时间倒序排序
            results.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"查询审计日志失败: {e}")
        
        return results[:limit]


# 全局审计日志记录器实例
_audit_logger: Optional[SessionAuditLogger] = None


def get_audit_logger() -> SessionAuditLogger:
    """获取全局审计日志记录器实例"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = SessionAuditLogger()
    return _audit_logger


def log_session_access(
    user_id: int,
    user_email: str,
    action: str,
    file_path: str,
    success: bool = True,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    记录 Session 文件访问（便捷函数）
    
    Args:
        user_id: 用户 ID
        user_email: 用户邮箱
        action: 操作类型（字符串，会自动转换为 AuditAction）
        file_path: 文件路径
        success: 是否成功
        error_message: 错误消息
        metadata: 额外元数据
    """
    try:
        audit_action = AuditAction(action.lower())
    except ValueError:
        audit_action = AuditAction.VIEW
    
    get_audit_logger().log(
        user_id=user_id,
        user_email=user_email,
        action=audit_action,
        file_path=file_path,
        success=success,
        error_message=error_message,
        metadata=metadata
    )

