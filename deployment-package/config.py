import os
import yaml
from dotenv import load_dotenv


def _load_env_files():
    """
    尝试加载当前目录与项目根目录下的 .env 文件。
    """
    env_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
    ]
    for path in env_paths:
        if os.path.exists(path):
            load_dotenv(path, override=False)


_load_env_files()


def _get_env(key, default=None, required=False):
    value = os.getenv(key, default)
    if required and (value is None or value == ""):
        raise ValueError(f"环境变量 {key} 未设置，且无默认值。")
    return value


def _get_int_env(key, default=None, required=False):
    value = _get_env(key, default, required=required)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"环境变量 {key} 必须是整数，当前值: {value}") from exc


# =========== 路径与常量 ===========
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
BACKUP_DIR = os.path.join(ROOT_DIR, "backup")
STATIC_DIR = os.path.join(ROOT_DIR, "static")
AI_MODELS_DIR = os.path.join(ROOT_DIR, "ai_models")
PHOTOS_DIR = os.path.join(ROOT_DIR, "photos")
VOICES_DIR = os.path.join(ROOT_DIR, "voices")

DB_PATH = os.path.join(DATA_DIR, "chat_history.db")
EXCEL_PATH = os.path.join(DATA_DIR, "friends.xlsx")
EMOJI_ROOT = os.path.join(PHOTOS_DIR, "xiaotong/emoji/")
VOICE_SAVE_DIR = VOICES_DIR

# =========== Telegram API ===========
API_ID = _get_int_env("TELEGRAM_API_ID", default=None, required=True)
API_HASH = _get_env("TELEGRAM_API_HASH", required=True)
SESSION_NAME = _get_env("TELEGRAM_SESSION_NAME", required=True)
SESSION_STRING = _get_env("TELEGRAM_SESSION_STRING", default="")
SESSION_FILE = _get_env("TELEGRAM_SESSION_FILE", default="")

# =========== OpenAI/腾讯等API参数 ===========
OPENAI_API_KEY = _get_env("OPENAI_API_KEY", required=True)
OPENAI_MODEL = _get_env("OPENAI_MODEL", default="gpt-4")
OPENAI_VISION_MODEL = _get_env("OPENAI_VISION_MODEL", default="gpt-4o-mini")

TENCENT_SECRET_ID = _get_env("TENCENT_SECRET_ID", default="")
TENCENT_SECRET_KEY = _get_env("TENCENT_SECRET_KEY", default="")

# =========== AI风格相关 ===========
BATCH_AI_EMOJI_FREQ = (2, 8)  # 批量AI表情触发频率

# =========== 风控/延迟参数 ===========
REPLY_DELAY = (2, 6)
CONTEXT_WINDOW = 8
PER_CHAR_DELAY_DAY = 1.2
PER_CHAR_DELAY_NIGHT = 1.8
PER_CHAR_DELAY_HOLIDAY = 2.2
PER_CHAR_DELAY_SENSITIVE = 2.5
SEND_MSG_MIN_DELAY = 3
SEND_MSG_MAX_DELAY = 15
ADD_FRIENDS_RATE_PER_MINUTE = _get_int_env(
    "ADD_FRIENDS_RATE_PER_MINUTE", default=15)
GREET_RATE_PER_MINUTE = _get_int_env("GREET_RATE_PER_MINUTE", default=20)
AUTO_REPLY_RATE_PER_MINUTE = _get_int_env(
    "AUTO_REPLY_RATE_PER_MINUTE", default=30)
TAG_ANALYZE_RATE_PER_MINUTE = _get_int_env(
    "TAG_ANALYZE_RATE_PER_MINUTE", default=25)
AUTO_GREET_INTERVAL_SECONDS = _get_int_env(
    "AUTO_GREET_INTERVAL_SECONDS", default=300)
AUTO_REPLY_INTERVAL_SECONDS = _get_int_env(
    "AUTO_REPLY_INTERVAL_SECONDS", default=180)
AUTO_TAG_ANALYZE_INTERVAL_SECONDS = _get_int_env(
    "AUTO_TAG_ANALYZE_INTERVAL_SECONDS", default=900)
AUTO_BACKUP_INTERVAL_SECONDS = _get_int_env(
    "AUTO_BACKUP_INTERVAL_SECONDS", default=3600)
REPLY_KEYWORDS_FILTER = ["色", "菠菜", "黄", "红包", "违法", "色情", "电影", "博彩"]

# =========== 内容池yaml入口 ===========


def load_yaml(path):
    """加载YAML文件，支持相对路径和绝对路径"""
    # 如果是相对路径，基于config.py所在目录解析
    if not os.path.isabs(path):
        # config.py 在项目根目录，所以直接使用
        config_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(config_dir, path)
    
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 使用基于 __file__ 的路径，确保无论从哪里导入都能找到文件
_config_dir = os.path.dirname(os.path.abspath(__file__))
_intro_segments_path = os.path.join(_config_dir, "ai_models", "intro_segments.yaml")

# 如果文件不存在，使用空字典避免导入错误（某些功能可能不需要这个文件）
if os.path.exists(_intro_segments_path):
    BASE_INFO = load_yaml(_intro_segments_path)
else:
    import logging
    logging.warning(f"intro_segments.yaml 文件不存在: {_intro_segments_path}，使用空配置")
    BASE_INFO = {}
STYLE_TAGS = BASE_INFO     # 让其它内容池引用同一个dict即可
GREETINGS = BASE_INFO
MULTI_PERSONA = BASE_INFO


# =========== 自动初始化必要目录/文件 ===========
NEED_DIRS = [DATA_DIR, LOGS_DIR, BACKUP_DIR,
             STATIC_DIR, AI_MODELS_DIR, PHOTOS_DIR, VOICES_DIR]


def auto_init_dirs():
    for d in NEED_DIRS:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)


auto_init_dirs()

# =========== 注释：如需其它项目级参数、统一加在本文件顶部 ===========
OPENAI_STT_PRIMARY = _get_env("OPENAI_STT_PRIMARY", default="gpt-4o-mini-transcribe")
OPENAI_STT_FALLBACK = _get_env("OPENAI_STT_FALLBACK", default="whisper-1")


# =========== 啟動時環境變量驗證 ===========
def validate_required_env_on_startup():
    """
    啟動時驗證必填環境變量（fail-fast 驗證）
    
    如果必填環境變量缺失，會立即拋出異常，避免運行時錯誤。
    """
    required_vars = [
        ("TELEGRAM_API_ID", "必須是整型"),
        ("TELEGRAM_API_HASH", "Telegram API Hash"),
        ("TELEGRAM_SESSION_NAME", "Pyrogram Session 名稱"),
        ("OPENAI_API_KEY", "OpenAI API Key"),
    ]
    
    missing = []
    for var_name, description in required_vars:
        value = os.getenv(var_name)
        if not value or value.strip() == "":
            missing.append(f"  - {var_name}: {description}")
        
        # 額外驗證 TELEGRAM_API_ID 必須是整型
        if var_name == "TELEGRAM_API_ID" and value:
            try:
                int(value)
            except ValueError:
                raise ValueError(
                    f"環境變量 {var_name} 必須是整型，當前值: {value}\n"
                    f"請從 https://my.telegram.org 獲取正確的 API ID。"
                )
    
    if missing:
        error_msg = "啟動失敗：以下必填環境變量未設置：\n" + "\n".join(missing)
        error_msg += "\n\n請從 docs/env.example 複製為 .env 文件並填入必填值。"
        raise ValueError(error_msg)


# 啟動時驗證（導入 config.py 時自動執行）
try:
    validate_required_env_on_startup()
except ValueError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"環境變量驗證失敗: {e}")
    # 注意：這裡不 raise，允許在某些情況下（如測試）跳過驗證
    # 如果需要嚴格驗證，可以在 main.py 中調用 validate_required_env_on_startup()