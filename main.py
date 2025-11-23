import asyncio
import config
import logging
import math
import os
import random
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

from langdetect import DetectorFactory, LangDetectException, detect
from pyrogram import Client, filters, idle
from pyrogram.errors import AuthKeyUnregistered

from utils import auto_backup
from utils.ai_context_manager import add_to_history, get_message_count, get_turn_count, init_history_db
from utils.async_utils import AsyncRateLimiter
from utils.auto_batch_greet_and_reply import auto_batch_greet_and_reply
from utils.business_ai import ai_business_reply, ai_extract_name_from_reply, analyze_image_message
from utils.db_manager import auto_init_db, update_user_profile_async
from utils.excel_manager import auto_init_excel
from utils.friend_greet import batch_auto_greet_new_friends
from utils.logger import setup_logger
from utils.media_utils import cleanup_file, convert_to_voice_ogg, extract_audio_from_media, extract_video_frames
from utils.prompt_manager import (ANGELA_CONFIG, generate_tts_text, get_button_config,
                                  init_prompt_templates, resolve_language_code,
                                  split_reply_sentences)
from utils.speech_to_text import transcribe_audio
from utils.tag_analyzer import batch_analyze_all_users
from utils.tts_voice import generate_voice
from utils.user_utils import get_user_profile

DetectorFactory.seed = 0
language_cache = {}
BUTTON_PRIORITY = ["group", "site", "bot"]
LINK_ACK_MESSAGES = {
    "zh": "我已把需要的連結貼好，有任何問題再跟我說。",
    "en": "I've shared the link above—let me know if you need anything else.",
}
VOICE_LIMIT_PER_HOUR = 10
VOICE_HISTORY = deque()
VOICE_RESPONSES_ENABLED = os.getenv("ENABLE_VOICE_RESPONSES", "1") != "0"
MIN_VOICE_DURATION_SEC = int(os.getenv("MIN_VOICE_DURATION_SEC", "1"))
MAX_VOICE_DURATION_SEC = int(os.getenv("MAX_VOICE_DURATION_SEC", "120"))
MAX_VOICE_FILE_MB = float(os.getenv("MAX_VOICE_FILE_MB", "8"))
PROACTIVE_VOICE_MIN_TURN = int(os.getenv("PROACTIVE_VOICE_MIN_TURN", "4"))
PROACTIVE_VOICE_INTERVAL = int(os.getenv("PROACTIVE_VOICE_INTERVAL", "3"))
PROACTIVE_VOICE_TEXT_THRESHOLD = int(os.getenv("PROACTIVE_VOICE_TEXT_THRESHOLD", "60"))
BUTTON_KEYWORDS = {
    "zh": {
        "group": ["進入紅包遊戲群", "加入紅包群", "進群", "红包群", "紅包群", "群呢", "群在哪", "給群", "群連結", "群链接"],
        "site": ["遊戲", "游戏", "玩遊戲", "平台", "網址", "連結", "鏈接", "官網", "website"],
        "bot": ["紅包", "红包", "搶紅包", "領紅包", "紅包資訊", "紅包助手", "紅包機器人"],
    },
    "en": {
        "group": ["join the group", "group link", "join group", "red packet group", "enter the group", "give me the group", "group invite"],
        "site": ["game", "play", "platform", "website", "site", "official site", "game link"],
        "bot": ["red packet", "red envelope", "bonus", "giveaway", "bot", "helper"],
    },
}
VOICE_REQUEST_KEYWORDS = {
    "zh": ["语音", "語音", "聲音回覆", "發語音", "語音回答", "語音回复", "語音給我"],
    "en": ["voice", "voice note", "voice reply", "audio reply", "send voice"],
}
ROBOT_QUERY_KEYWORDS = {
    "zh": ["你是不是机器人", "你是不是機器人", "你是ai", "你是人工", "假人", "是不是機器"],
    "en": ["are you a robot", "are you ai", "are you an ai", "are you artificial", "are you bot"],
}
ROBOT_DENIAL_RESPONSES = {
    "zh": "别想偷懒呀，我就在这儿陪你聊，真人本尊在线～",
    "en": "Hey, I’m right here in person keeping you company—no bots involved, promise!",
}
VOICE_QUALITY_FEEDBACK = {
    "too_short": {
        "zh": "剛剛的語音有點短，我怕沒聽清楚，可以再錄長一點和我說嗎？",
        "en": "That voice note was a bit too short—I might have missed it. Could you resend a slightly longer one?",
    },
    "too_long": {
        "zh": "語音稍微長了一點，怕系統轉寫不完整，方便分段再說一次嗎？",
        "en": "The voice note was on the long side—can you break it into smaller parts so I catch everything?",
    },
    "too_large": {
        "zh": "語音檔案有點大，轉寫時容易失敗，方便壓縮或重錄一段較短的嗎？",
        "en": "The audio file is quite large and hard to process—could you compress it or send a shorter one?",
    },
}
VIDEO_QUALITY_FEEDBACK = {
    "too_short": {
        "zh": "影片的語音只有一點點，轉寫不到，好嗎？可以錄長一些或改用文字告訴我。",
        "en": "The clip’s audio is very short so I couldn’t catch anything. Could you share a longer one or type it out for me?",
    },
    "too_long": {
        "zh": "影片稍微長了點，擔心轉寫不完整，要不要分段錄或挑重點告訴我？",
        "en": "That clip runs a bit long, so the transcription might miss parts. Maybe break it into smaller segments or highlight the key point for me?",
    },
    "too_large": {
        "zh": "影片檔太大，這邊處理時容易失敗，方便壓縮或錄短一些再傳一次嗎？",
        "en": "The video file is quite large and tricky to process. Could you compress it or send a shorter version?",
    },
    "extract_failed": {
        "zh": "我嘗試從影片抽音訊但沒有成功，可以再錄一段語音或用文字跟我說嗎？",
        "en": "I tried to extract the audio track but couldn’t. Could you send a quick voice note or type it out instead?",
    },
}


class BackgroundTaskManager:
    def __init__(self, app: Client, logger: logging.Logger) -> None:
        self.app = app
        self.logger = logger
        self.stop_event = asyncio.Event()
        self.tasks: list[tuple[str, asyncio.Task]] = []
        self.greet_limiter = AsyncRateLimiter(config.GREET_RATE_PER_MINUTE, 60)
        self.reply_limiter = AsyncRateLimiter(config.AUTO_REPLY_RATE_PER_MINUTE, 60)
        self.tag_limiter = AsyncRateLimiter(config.TAG_ANALYZE_RATE_PER_MINUTE, 60)

    async def start(self) -> None:
        if self.tasks:
            return
        if self.stop_event.is_set():
            self.stop_event = asyncio.Event()
        task = asyncio.create_task(
            self._run_periodic(
                "auto_greet",
                self._run_auto_greet,
                max(1, config.AUTO_GREET_INTERVAL_SECONDS),
            ), name="auto_greet_task")
        self.tasks.append(("auto_greet", task))
        task = asyncio.create_task(
            self._run_periodic(
                "batch_greet_reply",
                self._run_auto_batch_greet_and_reply,
                max(1, config.AUTO_REPLY_INTERVAL_SECONDS),
            ), name="auto_batch_greet_reply_task")
        self.tasks.append(("auto_batch_greet_reply", task))
        task = asyncio.create_task(
            self._run_periodic(
                "tag_analyzer",
                self._run_tag_analyzer,
                max(1, config.AUTO_TAG_ANALYZE_INTERVAL_SECONDS),
            ), name="tag_analyzer_task")
        self.tasks.append(("tag_analyzer", task))
        task = asyncio.create_task(
            auto_backup.schedule_auto_backup(
                interval_seconds=max(30, config.AUTO_BACKUP_INTERVAL_SECONDS),
                stop_event=self.stop_event,
                validator=self._log_backup_result,
            ), name="auto_backup_task")
        self.tasks.append(("auto_backup", task))
        self.logger.info("背景任務已啟動：歡迎、批量問候、標籤分析、備份排程。")

    async def stop(self) -> None:
        if not self.tasks:
            return
        self.stop_event.set()
        for _, task in self.tasks:
            task.cancel()
        results = await asyncio.gather(*(task for _, task in self.tasks), return_exceptions=True)
        for (name, _), result in zip(self.tasks, results):
            if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                self.logger.warning(f"[背景任務] {name} 結束時捕捉到異常: {result}")
        self.tasks.clear()
        self.logger.info("背景任務已停止。")

    async def _run_periodic(self, name: str, op: callable, interval: int) -> None:
        while not self.stop_event.is_set():
            try:
                await op()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.logger.exception(f"[背景任務] {name} 執行失敗: {exc}")
            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue

    async def _run_auto_greet(self) -> None:
        await batch_auto_greet_new_friends(
            tg_client=self.app,
            limiter=self.greet_limiter,
        )

    async def _run_auto_batch_greet_and_reply(self) -> None:
        await auto_batch_greet_and_reply(
            client=self.app,
            greet_limiter=self.greet_limiter,
            reply_limiter=self.reply_limiter,
        )

    async def _run_tag_analyzer(self) -> None:
        await batch_analyze_all_users(limiter=self.tag_limiter)

    async def _log_backup_result(self, payload: dict | None) -> None:
        if not payload:
            self.logger.warning("[背景任務] 備份回調未返回結果")
            return
        excel_path = payload.get("excel")
        db_path = payload.get("db")
        log_paths = payload.get("logs") or []
        self.logger.info(
            "[背景任務] 備份完成：excel=%s, db=%s, logs=%s",
            excel_path or "無",
            db_path or "無",
            ", ".join(log_paths) if log_paths else "無",
        )


def detect_user_language(text: str, user_id: int) -> str:
    fallback = language_cache.get(user_id)
    detected = None
    if text:
        try:
            detected = detect(text)
        except LangDetectException:
            detected = None
    resolved = resolve_language_code(detected) if detected else None
    if not resolved:
        resolved = fallback or ANGELA_CONFIG["language_settings"]["default"]
    language_cache[user_id] = resolved
    return resolved


def determine_button_triggers(text: str, language: str) -> list[str]:
    if not text:
        return []
    lang = resolve_language_code(language)
    mapping = BUTTON_KEYWORDS.get(lang, {})
    triggers = []
    plain = text.lower()
    for key in BUTTON_PRIORITY:
        keywords = mapping.get(key, [])
        if lang == "zh":
            hit = any(kw in text for kw in keywords)
        else:
            hit = any(kw in plain for kw in keywords)
        if hit and key not in triggers:
            triggers.append(key)
    return triggers


def can_send_voice_now():
    now = datetime.utcnow()
    threshold = now - timedelta(hours=1)
    while VOICE_HISTORY and VOICE_HISTORY[0] < threshold:
        VOICE_HISTORY.popleft()
    return len(VOICE_HISTORY) < VOICE_LIMIT_PER_HOUR


def register_voice_sent():
    VOICE_HISTORY.append(datetime.utcnow())


def detect_voice_request(text: str, language: str) -> bool:
    if not text:
        return False
    lang = resolve_language_code(language)
    keywords = VOICE_REQUEST_KEYWORDS.get(lang, [])
    lowered = text.lower()
    return any(kw in text or kw.lower() in lowered for kw in keywords)


def detect_robot_query(text: str, language: str) -> bool:
    if not text:
        return False
    lang = resolve_language_code(language)
    keywords = ROBOT_QUERY_KEYWORDS.get(lang, [])
    lowered = text.lower()
    return any(kw in text or kw.lower() in lowered for kw in keywords)


def assess_voice_quality(voice_media, file_path: str | None) -> str | None:
    """
    依據時長與檔案大小初步檢查語音品質。
    回傳 issue 代碼 (too_short/too_long/too_large) 或 None。
    """
    duration = getattr(voice_media, "duration", None)
    if duration is None:
        duration = getattr(voice_media, "length", None)
    if duration is not None:
        if duration < MIN_VOICE_DURATION_SEC:
            return "too_short"
        if duration > MAX_VOICE_DURATION_SEC:
            return "too_long"
    if file_path and os.path.exists(file_path):
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > MAX_VOICE_FILE_MB:
                return "too_large"
        except Exception:
            pass
    return None


def get_voice_quality_feedback(language: str, issue: str) -> str:
    lang = resolve_language_code(language)
    choices = VOICE_QUALITY_FEEDBACK.get(issue, {})
    msg = choices.get(lang) or choices.get("en")
    return msg or "Could you resend that voice note? I want to make sure I caught everything clearly."


def get_video_quality_feedback(language: str, issue: str) -> str:
    lang = resolve_language_code(language)
    choices = VIDEO_QUALITY_FEEDBACK.get(issue, {})
    msg = choices.get(lang) or choices.get("en")
    return msg or "Could you resend that clip or let me know in text? The audio didn’t come through clearly."


def decide_voice_strategy(
    *,
    force_voice: bool,
    stage: str,
    turn_count: int,
    is_voice: bool,
    user_text: str,
    stt_error: str | None,
) -> tuple[bool, str]:
    """
    綜合判斷是否主動回覆語音。
    回傳 (是否使用語音, 原因)。
    """
    if force_voice:
        return True, "user_requested"
    if not VOICE_RESPONSES_ENABLED:
        return False, "global_disabled"
    if stt_error:
        return False, "stt_error"
    if is_voice and turn_count > 1:
        return True, "mirror_user_voice"
    if stage != "warmup" and turn_count >= PROACTIVE_VOICE_MIN_TURN:
        if turn_count % PROACTIVE_VOICE_INTERVAL == 0:
            return True, "rhythm_variation"
        if len(user_text) >= PROACTIVE_VOICE_TEXT_THRESHOLD:
            return True, "long_text_variation"
    return False, "text_default"


async def main_async():
    setup_logger()
    logger = logging.getLogger("main")
    
    # 啟動時驗證環境變量（fail-fast）
    try:
        config.validate_required_env_on_startup()
        logger.info("環境變量驗證通過")
    except ValueError as e:
        logger.error(f"環境變量驗證失敗: {e}")
        raise
    
    config.auto_init_dirs()
    auto_init_db()
    auto_init_excel()
    init_history_db()
    init_prompt_templates()

    # 自動從 sessions 文件夾讀取 session 文件
    def find_session_file():
        """從 sessions 文件夾自動查找可用的 session 文件（支持加密文件）"""
        import tempfile
        from utils.session_encryption import get_session_manager
        
        # 優先使用環境變量中指定的 session
        if config.SESSION_FILE:
            session_path = Path(config.SESSION_FILE)
            if session_path.is_absolute() and session_path.exists():
                logger.info(f"使用環境變量指定的 session 文件: {session_path}")
                # 檢查是否為加密文件
                session_manager = get_session_manager()
                if session_manager.encryptor and session_manager.encryptor.is_encrypted_file(session_path):
                    # 解密到臨時文件
                    temp_dir = Path(tempfile.gettempdir()) / "telegram_sessions"
                    temp_dir.mkdir(exist_ok=True)
                    decrypted_data = session_manager.encryptor.decrypt_session(session_path)
                    temp_path = session_manager.encryptor.get_decrypted_path(session_path, temp_dir)
                    temp_path.write_bytes(decrypted_data)
                    logger.info(f"已解密 Session 文件到臨時位置: {temp_path}")
                    return temp_path.stem, temp_dir
                return session_path.stem, session_path.parent
            elif (Path("sessions") / session_path.name).exists():
                session_path = Path("sessions") / session_path.name
                logger.info(f"在 sessions 文件夾找到指定的 session 文件: {session_path}")
                return session_path.stem, Path("sessions")
        
        # 如果未指定或找不到，從 sessions 文件夾自動選擇
        sessions_dir = Path("sessions")
        if sessions_dir.exists():
            session_manager = get_session_manager()
            all_sessions = session_manager.list_sessions()
            
            # 過濾有效文件（排除 journal 文件）
            valid_sessions = [
                f for f in all_sessions
                if not f.name.endswith("-journal") and f.stat().st_size > 0
            ]
            
            if valid_sessions:
                # 按修改時間排序，使用最新的
                valid_sessions.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                selected = valid_sessions[0]
                
                # 如果是加密文件，需要解密到臨時位置
                if session_manager.encryptor and session_manager.encryptor.is_encrypted_file(selected):
                    import tempfile
                    temp_dir = Path(tempfile.gettempdir()) / "telegram_sessions"
                    temp_dir.mkdir(exist_ok=True)
                    decrypted_data = session_manager.encryptor.decrypt_session(selected)
                    temp_path = session_manager.encryptor.get_decrypted_path(selected, temp_dir)
                    temp_path.write_bytes(decrypted_data)
                    logger.info(f"已解密 Session 文件到臨時位置: {temp_path}")
                    return temp_path.stem, temp_dir
                
                logger.info(f"從 sessions 文件夾自動選擇 session 文件: {selected.name}")
                return selected.stem, sessions_dir
            else:
                logger.warning(f"sessions 文件夾中沒有找到有效的 session 文件")
        
        # 如果都找不到，使用默認的 session_name
        logger.info(f"使用默認 session 名稱: {config.SESSION_NAME}")
        return config.SESSION_NAME, Path(".")
    
    session_name, workdir = find_session_file()
    
    session_kwargs = {}
    if config.SESSION_STRING:
        session_kwargs["session_string"] = config.SESSION_STRING
        logger.info("使用 session_string 認證")
    
    # 創建 Client，使用 sessions 文件夾中的文件
    app = Client(
        session_name,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        workdir=str(workdir.resolve()),
        **session_kwargs,
    )
    
    logger.info(f"Pyrogram Client 初始化完成 - Session: {session_name}, Workdir: {workdir}")
    
    # 驗證 session 是否有效（後台運行，不顯示交互提示，支持重試）
    async def verify_session():
        """驗證 session 是否有效（在啟動前驗證，支持自動重試）"""
        from utils.retry_handler import retry_async, SESSION_RETRY_CONFIG, SessionError, NetworkError
        from pyrogram.errors import AuthKeyUnregistered, SessionPasswordNeeded
        
        retry_config = SESSION_RETRY_CONFIG
        retry_config.max_attempts = 3
        retry_config.initial_delay = 2.0
        
        async def attempt_verify():
            """嘗試驗證 session"""
            try:
                await app.connect()
                try:
                    # 使用 get_me() 来检查是否已授权
                    # 如果未授权，会抛出 AuthKeyUnregistered 异常
                    me = await app.get_me()
                    logger.info(f"Session 驗證成功 - 用戶: {me.first_name} (@{me.username or 'N/A'})")
                    return True
                except AuthKeyUnregistered:
                    await app.disconnect()
                    raise SessionError(f"Session {session_name} 已失效或未註冊，需要重新登錄")
                finally:
                    if app.is_connected:
                        await app.disconnect()
            except (AuthKeyUnregistered, SessionPasswordNeeded) as e:
                # Session 失效，不可重试
                raise ValueError(f"Session 失效: {e}")
            except Exception as e:
                # 检查是否为网络错误
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ["connection", "network", "timeout", "unreachable"]):
                    raise NetworkError(f"網絡錯誤: {e}") from e
                else:
                    raise SessionError(f"驗證錯誤: {e}") from e
        
        try:
            await retry_async(attempt_verify, retry_config)
        except ValueError:
            # Session 失效，直接抛出
            raise
        except Exception as e:
            logger.warning(f"Session 驗證時出現問題: {e}，將繼續運行（可能 session 已授權）")
    
    # 在啟動 handlers 之前驗證 session
    try:
        await verify_session()
    except ValueError as e:
        logger.error(f"Session 驗證失敗: {e}")
        raise

    @app.on_message(filters.private & filters.incoming)
    async def handle_private_message(client, message):
        user_id = message.from_user.id
        username = getattr(message.from_user, "username", "")
        raw_first_name = getattr(message.from_user, "first_name", "")
        text = message.text or ""
        caption = message.caption or ""
        is_photo = bool(message.photo)
        is_image_doc = bool(
            message.document and getattr(message.document, "mime_type", "").startswith("image/"))
        voice_media = message.voice or getattr(message, "audio", None) or getattr(message, "video_note", None)
        video_media = getattr(message, "video", None) or getattr(message, "animation", None)
        is_voice = bool(voice_media)
        is_video = bool(video_media)
        is_image = is_photo or is_image_doc
        voice_transcript = ""
        video_transcript = ""
        downloaded_voice = None
        downloaded_video = None
        stt_result = None
        video_stt_result = None
        voice_quality_issue = None
        video_quality_issue = None
        video_stt_error = None
        video_stt_model = None
        video_detected_language = None

        if is_voice:
            try:
                downloaded_voice = await message.download()
                voice_quality_issue = assess_voice_quality(voice_media, downloaded_voice)
                if voice_quality_issue:
                    stt_result = {
                        "text": "",
                        "error": f"quality:{voice_quality_issue}",
                        "model": None,
                        "language": None,
                    }
                else:
                    stt_result = await transcribe_audio(downloaded_voice)
            except Exception as voice_err:
                logger.warning(f"語音下載失敗: {voice_err}")
                stt_result = {"text": "", "error": str(voice_err), "model": None, "language": None}
            else:
                if voice_quality_issue:
                    logger.warning(f"語音品質異常: {voice_quality_issue}")
                elif stt_result and stt_result.get("error"):
                    logger.warning(f"語音轉寫錯誤: {stt_result['error']}")
            finally:
                if downloaded_voice and os.path.exists(downloaded_voice):
                    try:
                        os.remove(downloaded_voice)
                    except Exception:
                        pass

        extracted_audio = None
        extracted_frames: list[str] = []
        if is_video:
            try:
                downloaded_video = await message.download()
                video_quality_issue = assess_voice_quality(video_media, downloaded_video)
                if video_quality_issue:
                    video_stt_result = {
                        "text": "",
                        "error": f"quality:{video_quality_issue}",
                        "model": None,
                        "language": None,
                    }
                else:
                    extracted_audio = extract_audio_from_media(downloaded_video)
                    if extracted_audio:
                        video_stt_result = await transcribe_audio(extracted_audio)
                    else:
                        video_stt_result = {
                            "text": "",
                            "error": "extract_failed",
                            "model": None,
                            "language": None,
                        }
            except Exception as video_err:
                logger.warning(f"影片下載/轉寫失敗: {video_err}")
                video_stt_result = {"text": "", "error": str(video_err), "model": None, "language": None}
            else:
                if video_quality_issue:
                    logger.warning(f"影片音訊品質異常: {video_quality_issue}")
                elif video_stt_result and video_stt_result.get("error"):
                    logger.warning(f"影片音訊轉寫錯誤: {video_stt_result['error']}")
            finally:
                if extracted_audio:
                    cleanup_file(extracted_audio)
                for frame_path in extracted_frames:
                    cleanup_file(frame_path)

        stt_error = None
        stt_model = None
        stt_detected_language = None

        if stt_result:
            voice_transcript = stt_result.get("text", "") or ""
            stt_error = stt_result.get("error")
            stt_model = stt_result.get("model")
            stt_detected_language = stt_result.get("language")
            if stt_error and isinstance(stt_error, str) and stt_error.startswith("quality:"):
                issue = stt_error.split(":", 1)[1] if ":" in stt_error else ""
                if issue:
                    voice_quality_issue = voice_quality_issue or issue

        if video_stt_result:
            video_transcript = video_stt_result.get("text", "") or ""
            video_stt_error = video_stt_result.get("error")
            video_stt_model = video_stt_result.get("model")
            video_detected_language = video_stt_result.get("language")
            if video_stt_error and isinstance(video_stt_error, str) and video_stt_error.startswith("quality:"):
                issue = video_stt_error.split(":", 1)[1] if ":" in video_stt_error else ""
                if issue:
                    video_quality_issue = video_quality_issue or issue
            if not video_transcript and not video_quality_issue and not video_stt_error:
                video_transcript = "[音訊為音樂或環境聲]"

        user_text = voice_transcript or video_transcript or text or caption or ""

        logger.info(
            f"[收] From {user_id} (@{username} {raw_first_name}): {user_text or '[非文字內容]'}")
        if stt_model:
            logger.info(f"[STT] 使用模型={stt_model}, 語言={stt_detected_language}, 文字長度={len(voice_transcript)}")
        elif stt_error:
            logger.info(f"[STT] 轉寫失敗: {stt_error}")
            if voice_quality_issue:
                logger.info(f"[STT] 語音品質問題: {voice_quality_issue}")
        if video_stt_model:
            logger.info(f"[Video-STT] 使用模型={video_stt_model}, 語言={video_detected_language}, 文字長度={len(video_transcript)}")
        elif video_stt_error:
            logger.info(f"[Video-STT] 轉寫失敗: {video_stt_error}")
            if video_quality_issue:
                logger.info(f"[Video-STT] 音訊品質問題: {video_quality_issue}")

        try:
            user_profile = await get_user_profile(user_id)
        except Exception as e:
            logger.error(f"从数据库获取 user_profile 失败: {e}, 将使用空 profile 继续。")
            user_profile = {}

        # --- v5.0 核心升级：对话状态机 ---
        current_state = user_profile.get("conversation_state", "normal")

        # 状态一：如果正在等待用户输入名字
        if current_state == 'waiting_for_name':
            logger.info(f"用户 {user_id} 处于 'waiting_for_name' 状态，开始名字识别...")
            await add_to_history(user_id, "user", text)  # 同样记录用户的回复
            extracted_name = await ai_extract_name_from_reply(text)

            if extracted_name:
                await message.reply(f"好的，{extracted_name}，以后我就这么称呼你啦！")
                await update_user_profile_async(
                    user_id, {'first_name': extracted_name, 'conversation_state': 'normal'})
                logger.info(
                    f"成功为用户 {user_id} 设置新昵称: {extracted_name}, 状态已重置为 'normal'")
            else:
                await message.reply("好的，那我就先称呼您为“朋友”吧，以后可以随时告诉我怎么称呼您哦。")
                await update_user_profile_async(
                    user_id, {'first_name': '朋友', 'conversation_state': 'normal'})
                logger.info(f"用户 {user_id} 未提供有效昵称, 状态已重置为 'normal'")
            return

        # 状态二：正常对话流程
        language = detect_user_language(user_text, user_id)

        user_profile['user_id'] = user_id
        user_profile['username'] = username
        user_profile['first_name'] = user_profile.get(
            'first_name') or raw_first_name or "朋友"

        if is_image:
            image_path = await message.download()
            storage_text = "[圖片]" + (f" {user_text}" if user_text else "")
            await add_to_history(user_id, "user", storage_text.strip())
        elif is_voice:
            if voice_transcript:
                storage_text = "[語音轉文字] " + voice_transcript.strip()
            elif voice_quality_issue:
                storage_text = f"[語音品質異常:{voice_quality_issue}]"
            elif stt_error:
                storage_text = "[語音轉寫失敗]"
            else:
                storage_text = "[語音]"
            await add_to_history(user_id, "user", storage_text.strip())
        elif is_video:
            if video_transcript:
                storage_text = "[影片轉文字] " + video_transcript.strip()
            elif video_quality_issue:
                storage_text = f"[影片音訊品質異常:{video_quality_issue}]"
            elif video_stt_error:
                storage_text = "[影片音訊轉寫失敗]"
            else:
                storage_text = "[影片]"
            await add_to_history(user_id, "user", storage_text.strip())
        else:
            await add_to_history(user_id, "user", text)
        msg_count = await get_message_count(user_id)
        turn_count = await get_turn_count(user_id)

        if voice_quality_issue and not voice_transcript:
            feedback_text = get_voice_quality_feedback(language, voice_quality_issue)
            await message.reply(feedback_text)
            await add_to_history(user_id, "assistant", feedback_text)
            return

        if video_quality_issue and not video_transcript:
            feedback_text = get_video_quality_feedback(language, video_quality_issue)
            await message.reply(feedback_text)
            await add_to_history(user_id, "assistant", feedback_text)
            return

        # 检查是否需要主动询问姓名
        name_is_unknown = user_profile.get('first_name') == "朋友"
        if msg_count == 1 and name_is_unknown:
            logger.info(f"新用户 {user_id} 且昵称未知，主动询问。")
            ask_text = "你好呀，初次见面，我该怎么称呼您呢？"
            await message.reply(ask_text)
            await add_to_history(user_id, "assistant", ask_text)  # 把询问也计入历史
            await update_user_profile_async(
                user_id, {'conversation_state': 'waiting_for_name'})
            return

        # 正常智能问候逻辑
        use_name_in_prompt = False
        if msg_count == 1 and not name_is_unknown:
            use_name_in_prompt = True
        elif random.randint(1, 8) == 1:
            use_name_in_prompt = True

        stage = "warmup" if turn_count <= 5 else "normal"
        intent = None
        lowered = user_text.lower()
        if any(k in lowered for k in ["work", "job", "game", "红包", "遊戲", "开发", "遊戲", "游戏"]):
            intent = "work"

        button_triggers = determine_button_triggers(user_text, language)
        force_voice = detect_voice_request(user_text, language)
        robot_query = detect_robot_query(user_text, language)
        proactive_voice_allowed, voice_plan_reason = decide_voice_strategy(
            force_voice=force_voice,
            stage=stage,
            turn_count=turn_count,
            is_voice=is_voice,
            user_text=user_text,
            stt_error=stt_error,
        )
        context_info = {
            "conversation_stage": stage,
            "triggered_intent": intent,
            "language": language,
        }
        if voice_transcript:
            context_info["voice_transcript"] = voice_transcript
        if stt_model:
            context_info["stt_model"] = stt_model
        if stt_error:
            context_info["stt_error"] = stt_error
        if stt_detected_language:
            context_info["stt_detected_language"] = stt_detected_language
        if voice_quality_issue:
            context_info["voice_quality_issue"] = voice_quality_issue
        if video_transcript:
            context_info["video_transcript"] = video_transcript
        if video_stt_model:
            context_info["video_stt_model"] = video_stt_model
        if video_stt_error:
            context_info["video_stt_error"] = video_stt_error
        if video_detected_language:
            context_info["video_stt_detected_language"] = video_detected_language
        if video_quality_issue:
            context_info["video_quality_issue"] = video_quality_issue
        context_info["voice_strategy_allowed"] = proactive_voice_allowed
        context_info["voice_strategy_reason"] = voice_plan_reason

        async def send_reply_text(ai_text, language_code, triggers, force_voice=False):
            lang_code = resolve_language_code(language_code)
            direct_lines = []
            if force_voice:
                request_voice = True
                selected_voice_reason = "user_requested"
            else:
                request_voice = VOICE_RESPONSES_ENABLED and proactive_voice_allowed
                selected_voice_reason = voice_plan_reason
            tts_payload = None
            tone_context = {
                "stage": stage,
                "intent": intent,
                "voice_transcript": voice_transcript,
                "video_transcript": video_transcript,
                "voice_quality_issue": voice_quality_issue,
                "video_quality_issue": video_quality_issue,
                "stt_error": stt_error,
                "video_stt_error": video_stt_error,
                "voice_strategy_reason": selected_voice_reason,
            }

            if triggers:
                config_map = get_button_config(lang_code)
                for key in BUTTON_PRIORITY:
                    if key in triggers and key in config_map:
                        fallback = config_map[key].get("fallback_text")
                        if fallback:
                            direct_lines.append(fallback)

            if direct_lines:
                for line in direct_lines:
                    await message.reply(line)
                ack = LINK_ACK_MESSAGES.get(lang_code, LINK_ACK_MESSAGES["en"])
                await message.reply(ack)
                if request_voice:
                    tts_payload = generate_tts_text(
                        ack,
                        intent=intent,
                        max_len=2,
                        warmup=(stage == "warmup"),
                        language=lang_code,
                        tone_context=tone_context,
                    )
            else:
                short_sentences = split_reply_sentences(ai_text, max_len=3)

                def chunk_text(data, min_len=10, max_len=15):
                    cleaned = data.strip()
                    if not cleaned:
                        return []
                    if " " in cleaned:
                        words = cleaned.split()
                        chunks = []
                        current = []
                        current_len = 0
                        for word in words:
                            add_len = len(word) if not current else len(word) + 1
                            if current and current_len + add_len > max_len:
                                chunks.append(" ".join(current))
                                current = [word]
                                current_len = len(word)
                            else:
                                current.append(word)
                                current_len += add_len
                        if current:
                            chunks.append(" ".join(current))
                        if len(chunks) > 1 and len(chunks[-1]) < min_len:
                            chunks[-2] = f"{chunks[-2]} {chunks[-1]}".strip()
                            chunks.pop()
                        return chunks
                    chunks = []
                    start = 0
                    while start < len(cleaned):
                        end = min(start + max_len, len(cleaned))
                        if end - start < min_len and chunks:
                            chunks[-1] += cleaned[start:end]
                            break
                        chunks.append(cleaned[start:end])
                        start = end
                    return [c.strip() for c in chunks if c.strip()]

                all_chunks = []
                for short_reply in short_sentences:
                    all_chunks.extend(chunk_text(short_reply))

                max_messages = min(2, len(all_chunks)) or 1
                per_message = math.ceil(len(all_chunks) / max_messages) if all_chunks else 1

                sent = 0
                for idx in range(max_messages):
                    chunk_slice = all_chunks[sent:sent + per_message]
                    sent += per_message
                    if not chunk_slice:
                        continue
                    msg_text = " ".join(chunk_slice).strip()
                    if not msg_text:
                        continue
                    await message.reply(msg_text)
                    if idx < max_messages - 1:
                        await asyncio.sleep(random.uniform(2, 4))

                if request_voice:
                    tts_payload = generate_tts_text(
                        ai_text,
                        intent=intent,
                        max_len=3,
                        warmup=(stage == "warmup"),
                        language=lang_code,
                        tone_context=tone_context,
                    )

            if triggers and not direct_lines:
                config_map = get_button_config(lang_code)
                fallback_lines = []
                for key in BUTTON_PRIORITY:
                    if key in triggers and key in config_map:
                        fallback = config_map[key].get("fallback_text")
                        if fallback:
                            fallback_lines.append(fallback)
                if fallback_lines:
                    header = "👇 相關連結" if lang_code == "zh" else "👇 Related links"
                    await message.reply("\n".join([header, *fallback_lines]))

            if not request_voice or not tts_payload or not tts_payload.get("text"):
                return
            if not force_voice and not can_send_voice_now():
                logger.info(f"語音發送達到上限（策略: {selected_voice_reason}），改用純文字。")
                return

            tts_voice_choice = tts_payload.get("voice") or "shimmer"
            tts_style_hint = tts_payload.get("hint")
            tts_path = await generate_voice(tts_payload["text"], voice=tts_voice_choice, style_hint=tts_style_hint)
            if not tts_path or not os.path.exists(tts_path):
                return
            voice_ogg_path = convert_to_voice_ogg(tts_path)
            send_voice_path = voice_ogg_path or tts_path
            try:
                await client.read_chat_history(user_id)
            except Exception as read_err:
                logger.warning(f"標記已讀失敗: {read_err}")
            try:
                logger.info(f"語音策略啟用: {selected_voice_reason}")
                if voice_ogg_path and os.path.exists(voice_ogg_path):
                    await message.reply_voice(send_voice_path)
                else:
                    await message.reply_audio(send_voice_path, title="Angela reply", performer="Angela")
                register_voice_sent()
            except Exception as audio_err:
                logger.error(f"傳送音訊失敗: {audio_err}")
            finally:
                if voice_ogg_path and os.path.exists(voice_ogg_path):
                    cleanup_file(voice_ogg_path)

        if robot_query:
            denial = ROBOT_DENIAL_RESPONSES.get(language, ROBOT_DENIAL_RESPONSES["en"])
            await add_to_history(user_id, "assistant", denial)
            await send_reply_text(denial, language, button_triggers, force_voice=force_voice)
            return
        if is_image:
            context_for_image = {**context_info, "language": language}
            ai_image_result = await analyze_image_message(user_id, image_path, user_profile, context_for_image, language)
            try:
                os.remove(image_path)
            except Exception:
                pass

            if isinstance(ai_image_result, dict):
                category = ai_image_result.get("category")
                analysis_available = ai_image_result.get("analysis_available", True)
                failure_reason = ai_image_result.get("failure_reason", "")
                is_relevant = ai_image_result.get("is_relevant", True)
                contextual_reply = (ai_image_result.get("contextual_reply") or "").strip()
                availability_note = (ai_image_result.get("availability_note") or "").strip()
                key_points = ai_image_result.get("key_points") or []

                if category in {"chat_screenshot", "person_photo"}:
                    logger.info(f"[Vision] 類別={category}, key_points={key_points}, failure={failure_reason}")

                if not analysis_available:
                    if availability_note:
                        await send_reply_text(availability_note, language, button_triggers, force_voice=force_voice)
                    return

                if not is_relevant:
                    logger.info("[Vision] 圖片被判定為與當前話題無關，略過回覆。")
                    return

                if contextual_reply:
                    await send_reply_text(contextual_reply, language, button_triggers, force_voice=force_voice)
                elif availability_note:
                    await send_reply_text(availability_note, language, button_triggers, force_voice=force_voice)
                return

            if isinstance(ai_image_result, str):
                normalized = ai_image_result.strip()
                if not normalized or normalized.upper() == "NO_REPLY":
                    logger.info("[Vision] 模型返回 NO_REPLY 或空內容。")
                    return
                await send_reply_text(normalized, language, button_triggers, force_voice=force_voice)
                return

            return

        if is_video:
            context_for_video = {**context_info, "language": language, "video_transcript": video_transcript}
            frame_infos: list[dict] = []
            extracted_frames = extract_video_frames(downloaded_video) if downloaded_video and os.path.exists(downloaded_video) else []
            for frame_path in extracted_frames[:3]:
                ai_video_image = await analyze_image_message(
                    user_id, frame_path, user_profile, {**context_for_video, "from_video": True}, language
                )
                cleanup_file(frame_path)
                if isinstance(ai_video_image, dict):
                    frame_infos.append(ai_video_image)
                elif isinstance(ai_video_image, str):
                    normalized = ai_video_image.strip()
                    if normalized and normalized.upper() != "NO_REPLY":
                        frame_infos.append({"contextual_reply": normalized})

            final_reply = ""
            relevant_infos = [info for info in frame_infos if info.get("is_relevant", True)]
            fallback_infos = frame_infos if frame_infos else []

            def unique_join(items: list[str], sep: str) -> str:
                return sep.join(dict.fromkeys([s for s in items if s]))

            if relevant_infos:
                contextual_parts = []
                summary_parts = []
                key_points = []
                for info in relevant_infos:
                    contextual = (info.get("contextual_reply") or "").strip()
                    summary = (info.get("summary") or "").strip()
                    keys = info.get("key_points") or []
                    if contextual:
                        contextual_parts.append(contextual)
                    elif summary:
                        summary_parts.append(summary)
                    key_points.extend([k for k in keys if isinstance(k, str)])
                if contextual_parts:
                    final_reply = unique_join(contextual_parts, " / ")
                elif summary_parts:
                    final_reply = unique_join(summary_parts, " / ")
                elif key_points:
                    final_reply = unique_join(key_points, "，")

            if not final_reply and fallback_infos:
                summaries = [info.get("summary") for info in fallback_infos if info.get("summary")]
                notes = [info.get("availability_note") for info in fallback_infos if info.get("availability_note")]
                plain_texts = [info.get("contextual_reply") for info in fallback_infos if info.get("contextual_reply")]
                for source in (plain_texts, summaries, notes):
                    cleaned = [s.strip() for s in source if isinstance(s, str) and s.strip()]
                    if cleaned:
                        final_reply = unique_join(cleaned, " / ")
                        break

            if not final_reply:
                final_reply = "我看完你傳的影片了，目前沒有看到很明確的重點，如果有特別想聊的部分可以跟我說。"

            if video_transcript and video_transcript != "[音訊為音樂或環境聲]":
                final_reply = f"{final_reply} 裡面提到：「{video_transcript}」。"
            elif video_transcript == "[音訊為音樂或環境聲]":
                final_reply = f"{final_reply} 這段影片的音訊主要是背景音樂，沒有額外的語音資訊喔。"

            if downloaded_video and os.path.exists(downloaded_video):
                try:
                    os.remove(downloaded_video)
                except Exception:
                    pass

            await send_reply_text(final_reply, language, button_triggers, force_voice=force_voice)
            return

        ai_reply = await ai_business_reply(
            user_id,
            user_profile,
            context_info=context_info,
            history_summary="",
            use_name_in_prompt=use_name_in_prompt,
        )

        await send_reply_text(ai_reply, language, button_triggers, force_voice=force_voice)

        logger.info("="*48)
        print("="*48)

    manager = BackgroundTaskManager(app, logger)
    try:
        async with app:
            try:
                await manager.start()
                print("【阿龙分身批量机器人已启动】分句/表情/拟人TTS一体 ...")
                logger.info("【系统启动】TG机器人运营主控已启动。")
                await idle()
            finally:
                await manager.stop()
    except KeyboardInterrupt:
        logger.info("收到终止信号，准备关闭服务。")
    except Exception:
        logger.exception("主流程发生未预期错误，系统准备退出。")
        raise


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
