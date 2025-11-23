import base64
import os
from dataclasses import dataclass
from getpass import getpass
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken

DEFAULT_ITERATIONS = 390000
SALT_SIZE = 16


@dataclass
class EncryptionConfig:
    iterations: int = DEFAULT_ITERATIONS
    salt_size: int = SALT_SIZE


def _derive_key(password: str, salt: bytes, iterations: int) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def prompt_passphrase(confirm: bool = False) -> Optional[str]:
    """
    提示使用者輸入加密密碼，支援二次確認（避免輸入錯誤）。
    回傳 None 代表使用者選擇不加密。
    """
    pwd = getpass("設定加密密碼（空白代表不加密）：").strip()
    if not pwd:
        return None
    if confirm:
        pwd_confirm = getpass("再次輸入以確認：").strip()
        if pwd != pwd_confirm:
            raise ValueError("密碼不一致，請重新執行。")
    return pwd


def encrypt_bytes(data: bytes, password: str, cfg: EncryptionConfig | None = None) -> bytes:
    cfg = cfg or EncryptionConfig()
    salt = os.urandom(cfg.salt_size)
    key = _derive_key(password, salt, cfg.iterations)
    token = Fernet(key).encrypt(data)
    packed = b"|".join([salt, str(cfg.iterations).encode("utf-8"), token])
    return packed


def decrypt_bytes(packed: bytes, password: str) -> bytes:
    try:
        salt, iter_bytes, token = packed.split(b"|", 2)
    except ValueError as exc:
        raise ValueError("加密資料格式錯誤，無法解讀。") from exc
    iterations = int(iter_bytes.decode("utf-8"))
    key = _derive_key(password, salt, iterations)
    try:
        return Fernet(key).decrypt(token)
    except InvalidToken as exc:
        raise ValueError("解密失敗，密碼可能不正確。") from exc

