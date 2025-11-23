"""
Session 文件加密存储模块
提供 Session 文件的加密存储和解密读取功能
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)


class EncryptedSessionStorage:
    """Session 文件加密存储类"""
    
    def __init__(self, encryption_key: Optional[bytes] = None, password: Optional[str] = None):
        """
        初始化加密存储
        
        Args:
            encryption_key: 加密密钥（Fernet key，32 字节 base64 编码）
            password: 密码（用于生成密钥，如果提供 encryption_key 则忽略）
        """
        if encryption_key:
            self.cipher = Fernet(encryption_key)
        elif password:
            self.cipher = Fernet(self._derive_key_from_password(password))
        else:
            # 从环境变量获取密钥
            key = self._get_encryption_key_from_env()
            if key:
                self.cipher = Fernet(key)
            else:
                raise ValueError(
                    "需要提供 encryption_key 或 password，或设置环境变量 SESSION_ENCRYPTION_KEY"
                )
    
    @staticmethod
    def _derive_key_from_password(password: str, salt: Optional[bytes] = None) -> bytes:
        """
        从密码派生加密密钥
        
        Args:
            password: 密码字符串
            salt: 盐值（可选，默认使用固定盐值）
        
        Returns:
            Fernet 密钥（32 字节 base64 编码）
        """
        if salt is None:
            # 使用固定盐值（生产环境建议使用随机盐值）
            salt = b'session_encryption_salt_v1'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @staticmethod
    def _get_encryption_key_from_env() -> Optional[bytes]:
        """从环境变量获取加密密钥"""
        key_str = os.getenv("SESSION_ENCRYPTION_KEY")
        if not key_str:
            return None
        
        try:
            # 如果密钥是 base64 编码的字符串，直接使用
            if len(key_str) == 44:  # Fernet key 的标准长度
                return key_str.encode()
            # 否则尝试从密码派生
            return EncryptedSessionStorage._derive_key_from_password(key_str)
        except Exception as e:
            logger.error(f"从环境变量获取加密密钥失败: {e}")
            return None
    
    @staticmethod
    def generate_key() -> bytes:
        """
        生成新的加密密钥
        
        Returns:
            Fernet 密钥（32 字节 base64 编码）
        """
        return Fernet.generate_key()
    
    def encrypt_session(self, session_data: bytes, output_path: Path) -> Path:
        """
        加密 Session 数据并保存到文件
        
        Args:
            session_data: 原始 Session 数据
            output_path: 输出文件路径（会自动添加 .encrypted 扩展名）
        
        Returns:
            加密文件路径
        """
        try:
            encrypted_data = self.cipher.encrypt(session_data)
            
            # 如果路径没有 .encrypted 扩展名，添加它
            if not output_path.name.endswith('.encrypted'):
                encrypted_path = output_path.with_suffix('.session.encrypted')
            else:
                encrypted_path = output_path
            
            # 确保目录存在
            encrypted_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入加密文件
            encrypted_path.write_bytes(encrypted_data)
            
            logger.info(f"Session 文件已加密保存: {encrypted_path}")
            return encrypted_path
        except Exception as e:
            logger.error(f"加密 Session 文件失败: {e}")
            raise
    
    def decrypt_session(self, encrypted_path: Path) -> bytes:
        """
        解密 Session 文件
        
        Args:
            encrypted_path: 加密文件路径
        
        Returns:
            解密后的 Session 数据
        """
        try:
            if not encrypted_path.exists():
                raise FileNotFoundError(f"加密文件不存在: {encrypted_path}")
            
            encrypted_data = encrypted_path.read_bytes()
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            logger.debug(f"Session 文件已解密: {encrypted_path}")
            return decrypted_data
        except Exception as e:
            logger.error(f"解密 Session 文件失败: {e}")
            raise
    
    def is_encrypted_file(self, file_path: Path) -> bool:
        """
        检查文件是否为加密文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否为加密文件
        """
        return file_path.name.endswith('.encrypted') or file_path.suffix == '.encrypted'
    
    def get_decrypted_path(self, encrypted_path: Path, temp_dir: Optional[Path] = None) -> Path:
        """
        获取解密文件的临时路径（用于 Pyrogram 读取）
        
        Args:
            encrypted_path: 加密文件路径
            temp_dir: 临时目录（可选，默认使用加密文件所在目录）
        
        Returns:
            临时解密文件路径
        """
        if temp_dir is None:
            temp_dir = encrypted_path.parent
        
        # 生成临时文件名（移除 .encrypted 扩展名）
        temp_name = encrypted_path.stem.replace('.session', '') + '.session'
        temp_path = temp_dir / temp_name
        
        return temp_path


class SessionFileManager:
    """Session 文件管理器（支持加密和明文）"""
    
    def __init__(self, sessions_dir: Path, encryption_enabled: bool = False, 
                 encryption_key: Optional[bytes] = None, password: Optional[str] = None):
        """
        初始化 Session 文件管理器
        
        Args:
            sessions_dir: Session 文件目录
            encryption_enabled: 是否启用加密
            encryption_key: 加密密钥
            password: 加密密码
        """
        self.sessions_dir = Path(sessions_dir)
        self.encryption_enabled = encryption_enabled
        self.encryptor: Optional[EncryptedSessionStorage] = None
        
        if encryption_enabled:
            try:
                self.encryptor = EncryptedSessionStorage(encryption_key, password)
                logger.info("Session 文件加密已启用")
            except Exception as e:
                logger.warning(f"Session 加密初始化失败，将使用明文存储: {e}")
                self.encryption_enabled = False
    
    def save_session(self, session_data: bytes, filename: str) -> Path:
        """
        保存 Session 文件（根据配置决定是否加密）
        
        Args:
            session_data: Session 数据
            filename: 文件名
        
        Returns:
            保存的文件路径
        """
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.sessions_dir / filename
        
        if self.encryption_enabled and self.encryptor:
            # 加密保存
            return self.encryptor.encrypt_session(session_data, file_path)
        else:
            # 明文保存
            file_path.write_bytes(session_data)
            logger.info(f"Session 文件已保存（明文）: {file_path}")
            return file_path
    
    def load_session(self, filename: str) -> Tuple[bytes, Path]:
        """
        加载 Session 文件（自动检测加密或明文）
        
        Args:
            filename: 文件名
        
        Returns:
            (Session 数据, 文件路径)
        """
        # 尝试查找加密文件
        encrypted_path = self.sessions_dir / f"{filename}.encrypted"
        if encrypted_path.exists():
            if not self.encryptor:
                raise ValueError(f"发现加密文件但未配置加密密钥: {encrypted_path}")
            decrypted_data = self.encryptor.decrypt_session(encrypted_path)
            return decrypted_data, encrypted_path
        
        # 尝试查找明文文件
        plain_path = self.sessions_dir / filename
        if plain_path.exists():
            return plain_path.read_bytes(), plain_path
        
        raise FileNotFoundError(f"Session 文件不存在: {filename}")
    
    def list_sessions(self) -> list[Path]:
        """
        列出所有 Session 文件（包括加密和明文）
        
        Returns:
            Session 文件路径列表
        """
        sessions = []
        
        # 查找加密文件
        for encrypted_file in self.sessions_dir.glob("*.encrypted"):
            sessions.append(encrypted_file)
        
        # 查找明文文件（排除已加密的同名文件）
        for plain_file in self.sessions_dir.glob("*.session"):
            # 检查是否有对应的加密文件
            encrypted_version = plain_file.with_suffix('.session.encrypted')
            if not encrypted_version.exists():
                sessions.append(plain_file)
        
        return sessions


def get_session_manager() -> SessionFileManager:
    """
    获取全局 Session 文件管理器实例
    
    Returns:
        SessionFileManager 实例
    """
    from group_ai_service.config import get_group_ai_config
    
    config = get_group_ai_config()
    sessions_dir = Path(config.session_files_directory)
    
    # 检查是否启用加密
    encryption_enabled = os.getenv("SESSION_ENCRYPTION_ENABLED", "false").lower() == "true"
    encryption_key = os.getenv("SESSION_ENCRYPTION_KEY")
    password = os.getenv("SESSION_ENCRYPTION_PASSWORD")
    
    key_bytes = None
    if encryption_key:
        try:
            key_bytes = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        except Exception:
            pass
    
    return SessionFileManager(
        sessions_dir=sessions_dir,
        encryption_enabled=encryption_enabled,
        encryption_key=key_bytes,
        password=password
    )

