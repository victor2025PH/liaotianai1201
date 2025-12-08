"""
📝 日誌持久化模組
支持：
- 文件輸出
- 日誌輪轉（按大小/時間）
- 多級別日誌
- 結構化日誌
- 異步寫入
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from queue import Queue
from threading import Thread
import traceback


# ==================== 配置 ====================

@dataclass
class LogConfig:
    """日誌配置"""
    # 基本設置
    log_dir: str = "./logs"
    log_level: str = "INFO"
    
    # 文件設置
    log_file: str = "app.log"
    error_file: str = "error.log"
    
    # 輪轉設置（按大小）
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # 輪轉設置（按時間）
    when: str = "midnight"  # 每天午夜
    interval: int = 1
    
    # 格式設置
    console_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    file_format: str = "%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # JSON 日誌
    json_log_enabled: bool = True
    json_log_file: str = "app.json.log"
    
    # 性能設置
    async_write: bool = True
    buffer_size: int = 100
    
    @classmethod
    def from_env(cls) -> "LogConfig":
        """從環境變量加載"""
        return cls(
            log_dir=os.getenv("LOG_DIR", "./logs"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_bytes=int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024))),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
        )


# ==================== 自定義 Formatter ====================

class ColoredFormatter(logging.Formatter):
    """彩色日誌格式化器（控制台）"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 綠色
        'WARNING': '\033[33m',   # 黃色
        'ERROR': '\033[31m',     # 紅色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # 添加顏色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加額外字段
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        
        # 添加異常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False)


# ==================== 異步日誌處理器 ====================

class AsyncFileHandler(logging.Handler):
    """異步文件處理器"""
    
    def __init__(
        self,
        filename: str,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        buffer_size: int = 100
    ):
        super().__init__()
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.buffer_size = buffer_size
        
        self._queue: Queue = Queue(maxsize=buffer_size * 10)
        self._handler = RotatingFileHandler(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # 啟動後台寫入線程
        self._running = True
        self._thread = Thread(target=self._write_loop, daemon=True)
        self._thread.start()
    
    def emit(self, record):
        try:
            self._queue.put_nowait(record)
        except:
            pass  # 隊列滿時丟棄
    
    def _write_loop(self):
        """後台寫入循環"""
        while self._running:
            try:
                record = self._queue.get(timeout=1)
                self._handler.emit(record)
            except:
                continue
    
    def close(self):
        self._running = False
        self._thread.join(timeout=5)
        self._handler.close()
        super().close()


# ==================== 日誌管理器 ====================

class LogManager:
    """日誌管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: LogConfig = None):
        if self._initialized:
            return
        
        self.config = config or LogConfig.from_env()
        self._handlers: List[logging.Handler] = []
        self._loggers: Dict[str, logging.Logger] = {}
        
        # 創建日誌目錄
        Path(self.config.log_dir).mkdir(parents=True, exist_ok=True)
        
        # 設置根日誌器
        self._setup_root_logger()
        
        self._initialized = True
    
    def _setup_root_logger(self):
        """設置根日誌器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # 清除現有處理器
        root_logger.handlers.clear()
        
        # 1. 控制台處理器（彩色）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter(
            self.config.console_format,
            datefmt=self.config.date_format
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        self._handlers.append(console_handler)
        
        # 2. 文件處理器（按大小輪轉）
        file_path = Path(self.config.log_dir) / self.config.log_file
        if self.config.async_write:
            file_handler = AsyncFileHandler(
                str(file_path),
                max_bytes=self.config.max_bytes,
                backup_count=self.config.backup_count,
                buffer_size=self.config.buffer_size
            )
        else:
            file_handler = RotatingFileHandler(
                str(file_path),
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            self.config.file_format,
            datefmt=self.config.date_format
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        self._handlers.append(file_handler)
        
        # 3. 錯誤日誌處理器
        error_path = Path(self.config.log_dir) / self.config.error_file
        error_handler = RotatingFileHandler(
            str(error_path),
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
        self._handlers.append(error_handler)
        
        # 4. JSON 日誌處理器
        if self.config.json_log_enabled:
            json_path = Path(self.config.log_dir) / self.config.json_log_file
            json_handler = RotatingFileHandler(
                str(json_path),
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            json_handler.setLevel(logging.INFO)
            json_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(json_handler)
            self._handlers.append(json_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """獲取日誌器"""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]
    
    def set_level(self, level: str):
        """設置日誌級別"""
        log_level = getattr(logging, level.upper())
        logging.getLogger().setLevel(log_level)
    
    def close(self):
        """關閉所有處理器"""
        for handler in self._handlers:
            handler.close()
        self._handlers.clear()


# ==================== 結構化日誌助手 ====================

class StructuredLogger:
    """結構化日誌助手"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.default_context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs):
        """設置默認上下文"""
        self.default_context.update(kwargs)
    
    def _log(
        self,
        level: int,
        message: str,
        **extra_data
    ):
        """記錄結構化日誌"""
        data = {**self.default_context, **extra_data}
        
        # 創建帶額外數據的記錄
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(unknown file)",
            0,
            message,
            args=(),
            exc_info=None
        )
        record.extra_data = data
        self.logger.handle(record)
    
    def debug(self, message: str, **extra_data):
        self._log(logging.DEBUG, message, **extra_data)
    
    def info(self, message: str, **extra_data):
        self._log(logging.INFO, message, **extra_data)
    
    def warning(self, message: str, **extra_data):
        self._log(logging.WARNING, message, **extra_data)
    
    def error(self, message: str, **extra_data):
        self._log(logging.ERROR, message, **extra_data)
    
    def critical(self, message: str, **extra_data):
        self._log(logging.CRITICAL, message, **extra_data)
    
    # 業務日誌快捷方法
    def user_action(self, user_id: int, action: str, **details):
        """記錄用戶操作"""
        self.info(
            f"用戶操作: {action}",
            user_id=user_id,
            action=action,
            **details
        )
    
    def api_call(self, endpoint: str, status: str, duration_ms: float, **details):
        """記錄 API 調用"""
        self.info(
            f"API 調用: {endpoint} - {status}",
            endpoint=endpoint,
            status=status,
            duration_ms=duration_ms,
            **details
        )
    
    def redpacket_event(self, event_type: str, user_id: int, amount: float, **details):
        """記錄紅包事件"""
        self.info(
            f"紅包事件: {event_type}",
            event_type=event_type,
            user_id=user_id,
            amount=amount,
            **details
        )
    
    def group_event(self, event_type: str, group_id: int, **details):
        """記錄群組事件"""
        self.info(
            f"群組事件: {event_type}",
            event_type=event_type,
            group_id=group_id,
            **details
        )


# ==================== 日誌統計 ====================

class LogStats:
    """日誌統計"""
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
    
    def get_log_files(self) -> List[dict]:
        """獲取日誌文件列表"""
        files = []
        
        if not self.log_dir.exists():
            return files
        
        for f in self.log_dir.glob("*.log*"):
            stat = f.stat()
            files.append({
                "name": f.name,
                "size": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(f)
            })
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)
    
    def get_total_size(self) -> int:
        """獲取總大小"""
        if not self.log_dir.exists():
            return 0
        return sum(f.stat().st_size for f in self.log_dir.glob("*.log*"))
    
    def _format_size(self, size: int) -> str:
        """格式化大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def get_error_count(self, hours: int = 24) -> int:
        """獲取最近 N 小時的錯誤數"""
        error_file = self.log_dir / "error.log"
        if not error_file.exists():
            return 0
        
        count = 0
        cutoff = datetime.now().timestamp() - hours * 3600
        
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # 簡單解析時間戳
                    try:
                        timestamp_str = line[:19]
                        log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if log_time.timestamp() > cutoff:
                            count += 1
                    except:
                        continue
        except:
            pass
        
        return count
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """清理舊日誌"""
        if not self.log_dir.exists():
            return 0
        
        cutoff = datetime.now().timestamp() - days * 86400
        deleted = 0
        
        for f in self.log_dir.glob("*.log*"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                deleted += 1
        
        return deleted


# ==================== 初始化函數 ====================

def setup_logging(config: LogConfig = None) -> LogManager:
    """
    初始化日誌系統
    
    Usage:
        from worker_logging import setup_logging
        
        log_manager = setup_logging()
        logger = log_manager.get_logger("my_module")
        logger.info("Hello World")
    """
    return LogManager(config)


def get_structured_logger(name: str) -> StructuredLogger:
    """
    獲取結構化日誌器
    
    Usage:
        from worker_logging import get_structured_logger
        
        logger = get_structured_logger("redpacket")
        logger.redpacket_event("claimed", user_id=123, amount=1.5)
    """
    return StructuredLogger(name)


# 導出
__all__ = [
    "LogConfig",
    "LogManager",
    "StructuredLogger",
    "LogStats",
    "setup_logging",
    "get_structured_logger",
    "ColoredFormatter",
    "JSONFormatter",
    "AsyncFileHandler"
]
