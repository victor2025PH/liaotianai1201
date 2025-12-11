"""
API 限流配置
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

# 禁用 slowapi 的 .env 文件读取，仅使用环境变量（避免编码问题）
# 使用不存在的文件名避免 slowapi 尝试读取 .env 文件
# 注意：不删除 .env 文件，因为其他代码（如 config.py）需要读取它
limiter = Limiter(key_func=get_remote_address, config_filename="__nonexistent__.env")

# 限流配置
RATE_LIMITS = {
    "default": "100/minute",      # 默認：每分鐘100次
    "auth": "10/minute",          # 認證相關：每分鐘10次
    "heavy": "20/minute",         # 重操作：每分鐘20次
    "light": "200/minute",        # 輕操作：每分鐘200次
    "upload": "10/minute",        # 上傳：每分鐘10次
    "list": "60/minute",          # 列表查詢：每分鐘60次
    "detail": "100/minute",       # 詳情查詢：每分鐘100次
}

