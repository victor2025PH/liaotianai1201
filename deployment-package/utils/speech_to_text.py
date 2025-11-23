import asyncio
import logging
from typing import Optional

from openai import AsyncOpenAI

import config
from utils.media_utils import normalize_audio, cleanup_file

logger = logging.getLogger("speech_to_text")
client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

DEFAULT_STT_MODEL = "gpt-4o-mini-transcribe"
FALLBACK_STT_MODEL = "whisper-1"
PRIMARY_MODEL = config.OPENAI_STT_PRIMARY or DEFAULT_STT_MODEL
FALLBACK_MODEL = config.OPENAI_STT_FALLBACK or FALLBACK_STT_MODEL


def _log_params(file_path: str, language: Optional[str], model: str):
    logger.debug(f"[STT] 調用模型={model}, 語言={language}, 文件={file_path}")


async def _transcribe_file(file_path: str, language: Optional[str], model: str) -> str:
    _log_params(file_path, language, model)
    with open(file_path, "rb") as audio_file:
        result = await client.audio.transcriptions.create(
            file=audio_file,
            model=model,
            temperature=0,
            response_format="text",
            language=language,
        )
    return result.strip() if isinstance(result, str) else getattr(result, "text", "").strip()


async def transcribe_audio(file_path: str, language: str | None = None) -> dict:
    """
    將音訊檔轉寫為文字。
    回傳格式：
    {
        \"text\": str,
        \"model\": str | None,
        \"language\": str | None,
        \"error\": str | None
    }
    """
    result = {
        "text": "",
        "model": None,
        "language": language,
        "error": None,
    }
    if not file_path:
        logger.debug("[STT] 未提供音訊路徑，跳過轉寫。")
        result["error"] = "missing_file"
        return result

    logger.debug("[STT] 開始轉寫: %s", file_path)
    normalized_path = None
    try:
        normalized_path = await asyncio.to_thread(normalize_audio, file_path)
    except Exception as exc:
        logger.warning("[STT] 音訊正規化失敗，將使用原始檔案: %s", exc)

    target_path = normalized_path or file_path
    tried_models = []

    try:
        for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
            if model in tried_models:
                continue
            tried_models.append(model)
            try:
                text = await _transcribe_file(target_path, language, model)
            except Exception as exc:
                logger.error("[STT] 模型 %s 轉寫失敗: %s", model, exc)
                if model == FALLBACK_MODEL and PRIMARY_MODEL == FALLBACK_MODEL:
                    break
                result["error"] = str(exc)
                continue

            if text:
                logger.info("[STT] 轉寫成功 (模型=%s): %s", model, text)
                result["text"] = text
                result["model"] = model
                return result

            logger.warning("[STT] 模型 %s 轉寫為空，嘗試其他模型。", model)

        if result["error"] is None:
            result["error"] = "empty_result"
        return result
    finally:
        if normalized_path:
            cleanup_file(normalized_path)
