"""
Session 文件访问权限控制模块
提供文件系统权限控制和基于角色的访问控制
"""
import os
import stat
import logging
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class FilePermission(Enum):
    """文件权限枚举"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"


class SessionFilePermissionManager:
    """Session 文件权限管理器"""
    
    def __init__(self, sessions_dir: Path, default_mode: Optional[int] = None):
        """
        初始化权限管理器
        
        Args:
            sessions_dir: Session 文件目录
            default_mode: 默认文件权限（八进制，如 0o600）
        """
        self.sessions_dir = Path(sessions_dir)
        # 默认权限：仅所有者可读写（600）
        self.default_mode = default_mode or 0o600
        # 目录权限：所有者可读写执行（700）
        self.dir_mode = 0o700
    
    def set_file_permissions(self, file_path: Path, mode: Optional[int] = None) -> bool:
        """
        设置文件权限
        
        Args:
            file_path: 文件路径
            mode: 权限模式（八进制），如果为 None 则使用默认模式
        
        Returns:
            是否成功
        """
        try:
            permission_mode = mode or self.default_mode
            os.chmod(file_path, permission_mode)
            logger.debug(f"已设置文件权限: {file_path} -> {oct(permission_mode)}")
            return True
        except Exception as e:
            logger.error(f"设置文件权限失败: {file_path}, 错误: {e}")
            return False
    
    def set_directory_permissions(self, dir_path: Path, mode: Optional[int] = None) -> bool:
        """
        设置目录权限
        
        Args:
            dir_path: 目录路径
            mode: 权限模式（八进制），如果为 None 则使用默认目录权限
        
        Returns:
            是否成功
        """
        try:
            permission_mode = mode or self.dir_mode
            os.chmod(dir_path, permission_mode)
            logger.debug(f"已设置目录权限: {dir_path} -> {oct(permission_mode)}")
            return True
        except Exception as e:
            logger.error(f"设置目录权限失败: {dir_path}, 错误: {e}")
            return False
    
    def ensure_directory_permissions(self) -> bool:
        """
        确保 sessions 目录权限正确
        
        Returns:
            是否成功
        """
        if not self.sessions_dir.exists():
            try:
                self.sessions_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"创建 sessions 目录失败: {e}")
                return False
        
        return self.set_directory_permissions(self.sessions_dir)
    
    def check_file_permission(self, file_path: Path, permission: FilePermission, 
                             user_id: Optional[int] = None) -> bool:
        """
        检查文件权限
        
        Args:
            file_path: 文件路径
            permission: 需要的权限
            user_id: 用户 ID（用于检查是否为文件所有者）
        
        Returns:
            是否有权限
        """
        if not file_path.exists():
            return False
        
        try:
            file_stat = file_path.stat()
            file_mode = stat.filemode(file_stat.st_mode)
            
            # 在 Windows 上，权限检查可能不准确
            if os.name == 'nt':
                # Windows: 检查文件是否可读
                if permission == FilePermission.READ:
                    return os.access(file_path, os.R_OK)
                elif permission == FilePermission.WRITE:
                    return os.access(file_path, os.W_OK)
                return True
            
            # Linux/Unix: 检查文件权限位
            mode_bits = file_stat.st_mode
            
            # 检查是否为文件所有者
            is_owner = False
            if user_id is not None:
                try:
                    is_owner = (file_stat.st_uid == user_id)
                except AttributeError:
                    # 某些系统可能不支持 st_uid
                    is_owner = True
            
            if permission == FilePermission.READ:
                # 所有者读权限 (0400) 或 其他用户读权限 (0044)
                if is_owner:
                    return bool(mode_bits & stat.S_IRUSR)
                else:
                    return bool(mode_bits & stat.S_IROTH)
            
            elif permission == FilePermission.WRITE:
                # 所有者写权限 (0200) 或 其他用户写权限 (0022)
                if is_owner:
                    return bool(mode_bits & stat.S_IWUSR)
                else:
                    return bool(mode_bits & stat.S_IWOTH)
            
            elif permission == FilePermission.DELETE:
                # 需要目录写权限才能删除文件
                parent_dir = file_path.parent
                if parent_dir.exists():
                    parent_stat = parent_dir.stat()
                    if is_owner:
                        return bool(parent_stat.st_mode & stat.S_IWUSR)
                    else:
                        return bool(parent_stat.st_mode & stat.S_IWOTH)
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"检查文件权限失败: {file_path}, 错误: {e}")
            return False
    
    def secure_new_file(self, file_path: Path) -> bool:
        """
        创建新文件并设置安全权限
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否成功
        """
        try:
            # 确保目录存在且权限正确
            file_path.parent.mkdir(parents=True, exist_ok=True)
            self.set_directory_permissions(file_path.parent)
            
            # 如果文件已存在，先设置权限
            if file_path.exists():
                self.set_file_permissions(file_path)
            else:
                # 创建空文件并设置权限
                file_path.touch()
                self.set_file_permissions(file_path)
            
            return True
        except Exception as e:
            logger.error(f"创建安全文件失败: {file_path}, 错误: {e}")
            return False
    
    def get_file_permissions(self, file_path: Path) -> Optional[str]:
        """
        获取文件权限字符串（如 'rw-------'）
        
        Args:
            file_path: 文件路径
        
        Returns:
            权限字符串或 None
        """
        try:
            if not file_path.exists():
                return None
            
            file_stat = file_path.stat()
            return stat.filemode(file_stat.st_mode)
        except Exception as e:
            logger.error(f"获取文件权限失败: {file_path}, 错误: {e}")
            return None


def get_session_permission_manager(sessions_dir: Optional[Path] = None) -> SessionFilePermissionManager:
    """
    获取全局 Session 文件权限管理器实例
    
    Args:
        sessions_dir: Session 文件目录（可选，默认从配置获取）
    
    Returns:
        SessionFilePermissionManager 实例
    """
    if sessions_dir is None:
        from group_ai_service.config import get_group_ai_config
        config = get_group_ai_config()
        sessions_dir = Path(config.session_files_directory)
    
    manager = SessionFilePermissionManager(sessions_dir)
    # 确保目录权限正确
    manager.ensure_directory_permissions()
    
    return manager

