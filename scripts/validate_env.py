"""
環境變量驗證腳本（啟動時 fail-fast 驗證）

使用方式：
    python scripts/validate_env.py
    python -m scripts.validate_env
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# 環境變量定義（必填項）
REQUIRED_ENV_VARS = {
    "TELEGRAM_API_ID": {
        "type": "int",
        "description": "Telegram 開發者 API ID（整型）",
        "help": "從 https://my.telegram.org 獲取",
    },
    "TELEGRAM_API_HASH": {
        "type": "str",
        "description": "Telegram API Hash",
        "help": "從 https://my.telegram.org 獲取",
    },
    "TELEGRAM_SESSION_NAME": {
        "type": "str",
        "description": "Pyrogram Session 名稱",
        "help": "用於創建 Telegram session 文件",
    },
    "OPENAI_API_KEY": {
        "type": "str",
        "description": "OpenAI API Key",
        "help": "從 https://platform.openai.com/api-keys 獲取",
    },
}

# 可選環境變量（帶默認值）
OPTIONAL_ENV_VARS = {
    "OPENAI_MODEL": {
        "type": "str",
        "default": "gpt-4",
        "description": "默認 OpenAI 模型名稱",
    },
    "OPENAI_VISION_MODEL": {
        "type": "str",
        "default": "gpt-4o-mini",
        "description": "OpenAI Vision 模型名稱",
    },
    "OPENAI_STT_PRIMARY": {
        "type": "str",
        "default": "gpt-4o-mini-transcribe",
        "description": "主要 STT 模型",
    },
    "OPENAI_STT_FALLBACK": {
        "type": "str",
        "default": "whisper-1",
        "description": "備用 STT 模型",
    },
    "TENCENT_SECRET_ID": {
        "type": "str",
        "default": "",
        "description": "騰訊雲 SecretId（可選）",
    },
    "TENCENT_SECRET_KEY": {
        "type": "str",
        "default": "",
        "description": "騰訊雲 SecretKey（可選）",
    },
    "ENABLE_VOICE_RESPONSES": {
        "type": "str",
        "default": "1",
        "description": "是否啟用語音響應（1/0）",
    },
    "MIN_VOICE_DURATION_SEC": {
        "type": "int",
        "default": "1",
        "description": "最小語音時長（秒）",
    },
    "MAX_VOICE_DURATION_SEC": {
        "type": "int",
        "default": "120",
        "description": "最大語音時長（秒）",
    },
    "MAX_VOICE_FILE_MB": {
        "type": "float",
        "default": "8",
        "description": "最大語音文件大小（MB）",
    },
    "PROACTIVE_VOICE_MIN_TURN": {
        "type": "int",
        "default": "4",
        "description": "主動語音最小輪次",
    },
    "PROACTIVE_VOICE_INTERVAL": {
        "type": "int",
        "default": "3",
        "description": "主動語音間隔（輪次）",
    },
    "PROACTIVE_VOICE_TEXT_THRESHOLD": {
        "type": "int",
        "default": "60",
        "description": "主動語音文本閾值（字符數）",
    },
    "ADD_FRIENDS_RATE_PER_MINUTE": {
        "type": "int",
        "default": "15",
        "description": "每分鐘允許的自動加好友上限",
    },
    "GREET_RATE_PER_MINUTE": {
        "type": "int",
        "default": "20",
        "description": "每分鐘歡迎消息最大發送次數",
    },
    "AUTO_REPLY_RATE_PER_MINUTE": {
        "type": "int",
        "default": "30",
        "description": "每分鐘批量自動回覆最大發送次數",
    },
    "TAG_ANALYZE_RATE_PER_MINUTE": {
        "type": "int",
        "default": "25",
        "description": "每分鐘允許執行的標籤分析次數",
    },
    "AUTO_GREET_INTERVAL_SECONDS": {
        "type": "int",
        "default": "300",
        "description": "定時歡迎任務執行間隔秒數",
    },
    "AUTO_REPLY_INTERVAL_SECONDS": {
        "type": "int",
        "default": "180",
        "description": "批量問候/回覆輪詢間隔秒數",
    },
    "AUTO_TAG_ANALYZE_INTERVAL_SECONDS": {
        "type": "int",
        "default": "900",
        "description": "標籤分析輪詢間隔秒數",
    },
    "AUTO_BACKUP_INTERVAL_SECONDS": {
        "type": "int",
        "default": "3600",
        "description": "備份排程執行間隔秒數",
    },
    "GAME_DATABASE_URL": {
        "type": "str",
        "default": "",
        "description": "遊戲系統數據庫連接（可選）",
    },
    "GROUP_AI_GAME_API_BASE_URL": {
        "type": "str",
        "default": "http://localhost:8000",
        "description": "遊戲系統 API 地址（可選）",
    },
    "GROUP_AI_GAME_API_KEY": {
        "type": "str",
        "default": "",
        "description": "遊戲系統 API 密鑰（可選）",
    },
    "GROUP_AI_GAME_API_ENABLED": {
        "type": "str",
        "default": "false",
        "description": "是否啟用遊戲系統 API（可選）",
    },
    "GAME_SYSTEM_PATH": {
        "type": "str",
        "default": "",
        "description": "遊戲系統代碼路徑（可選）",
    },
}


def validate_type(value: str, var_type: str, var_name: str) -> Tuple[bool, Optional[str]]:
    """驗證環境變量類型"""
    try:
        if var_type == "int":
            int(value)
        elif var_type == "float":
            float(value)
        elif var_type == "bool":
            if value.lower() not in ["true", "false", "1", "0", "yes", "no"]:
                return False, f"必須是布爾值（true/false/1/0/yes/no）"
        elif var_type == "str":
            pass  # 字符串無需驗證
        return True, None
    except ValueError:
        return False, f"必須是 {var_type} 類型"


def validate_required_env() -> Tuple[bool, List[str]]:
    """驗證必填環境變量"""
    errors = []
    
    for var_name, var_info in REQUIRED_ENV_VARS.items():
        value = os.getenv(var_name)
        
        if not value or value.strip() == "":
            errors.append(
                f"❌ {var_name}: 未設置（必填）\n"
                f"   說明: {var_info['description']}\n"
                f"   幫助: {var_info.get('help', '請查看文檔')}"
            )
            continue
        
        # 驗證類型
        var_type = var_info["type"]
        is_valid, error_msg = validate_type(value, var_type, var_name)
        if not is_valid:
            errors.append(
                f"❌ {var_name}: 類型錯誤\n"
                f"   當前值: {value}\n"
                f"   錯誤: {error_msg}"
            )
    
    return len(errors) == 0, errors


def validate_optional_env() -> Tuple[bool, List[str]]:
    """驗證可選環境變量（類型檢查）"""
    errors = []
    warnings = []
    
    for var_name, var_info in OPTIONAL_ENV_VARS.items():
        value = os.getenv(var_name)
        
        # 如果未設置，使用默認值（不報錯）
        if not value or value.strip() == "":
            default = var_info.get("default", "")
            if default:
                warnings.append(
                    f"⚠️  {var_name}: 未設置，使用默認值: {default}"
                )
            continue
        
        # 驗證類型
        var_type = var_info["type"]
        is_valid, error_msg = validate_type(value, var_type, var_name)
        if not is_valid:
            errors.append(
                f"❌ {var_name}: 類型錯誤\n"
                f"   當前值: {value}\n"
                f"   錯誤: {error_msg}"
            )
    
    return len(errors) == 0, errors, warnings


def check_env_files() -> List[str]:
    """檢查 .env 文件是否存在"""
    warnings = []
    
    env_paths = [
        Path(project_root) / ".env",
        Path(project_root) / "config.py" / ".env",  # 同級目錄
    ]
    
    found = False
    for env_path in env_paths:
        if env_path.exists():
            found = True
            warnings.append(f"✅ 找到 .env 文件: {env_path}")
            break
    
    if not found:
        warnings.append(
            "⚠️  未找到 .env 文件，建議從 docs/env.example 複製並配置"
        )
    
    return warnings


def main():
    """主函數：驗證環境變量"""
    print("=" * 60)
    print("環境變量驗證")
    print("=" * 60)
    print()
    
    # 加載 .env 文件（如果存在）
    try:
        from dotenv import load_dotenv
        env_path = Path(project_root) / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ 已加載 .env 文件: {env_path}")
        else:
            # 嘗試加載 config.py 同級目錄的 .env
            env_path2 = Path(__file__).parent.parent / ".env"
            if env_path2.exists():
                load_dotenv(env_path2)
                print(f"✅ 已加載 .env 文件: {env_path2}")
            else:
                print("⚠️  未找到 .env 文件，使用系統環境變量")
        print()
    except ImportError:
        print("⚠️  python-dotenv 未安裝，跳過 .env 文件加載")
        print()
    
    # 檢查 .env 文件
    env_file_warnings = check_env_files()
    for warning in env_file_warnings:
        print(warning)
    print()
    
    # 驗證必填環境變量
    print("[1/2] 驗證必填環境變量...")
    required_valid, required_errors = validate_required_env()
    
    if required_valid:
        print("✅ 所有必填環境變量已設置")
    else:
        print("❌ 必填環境變量驗證失敗：")
        for error in required_errors:
            print(f"\n{error}")
    
    print()
    
    # 驗證可選環境變量
    print("[2/2] 驗證可選環境變量...")
    optional_valid, optional_errors, optional_warnings = validate_optional_env()
    
    if optional_warnings:
        for warning in optional_warnings:
            print(warning)
    
    if optional_valid:
        if not optional_warnings:
            print("✅ 所有可選環境變量驗證通過")
    else:
        print("❌ 可選環境變量驗證失敗：")
        for error in optional_errors:
            print(f"\n{error}")
    
    print()
    print("=" * 60)
    
    # 總結
    if required_valid and optional_valid:
        print("✅ 環境變量驗證通過！")
        print("=" * 60)
        return 0
    else:
        print("❌ 環境變量驗證失敗！請修正上述錯誤後重試。")
        print("=" * 60)
        print()
        print("提示：")
        print("1. 從 docs/env.example 複製為 .env 文件")
        print("2. 填入必填環境變量（TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_NAME, OPENAI_API_KEY）")
        print("3. 根據需要調整可選環境變量")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

