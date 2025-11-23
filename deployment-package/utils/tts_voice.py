"""
TTS语音合成模块
- 自动生成真人风格语音
- 所有操作日志，便于追踪异常和性能评估
"""
import os
import time
import random
import logging
import config

logger = logging.getLogger("tts_voice")

try:
    from pydub import AudioSegment
    from pydub.generators import WhiteNoise
except ImportError:  # pragma: no cover - optional dependency
    AudioSegment = None
    WhiteNoise = None


def get_tts_client():
    try:
        import openai
        openai.api_key = config.OPENAI_API_KEY
        return openai
    except Exception as e:
        logger.error(f"[TTS] OpenAI SDK未安装: {e}")
        raise ImportError(f"openai TTS SDK未安装: {e}")


def _get_unique_voice_path():
    VOICE_SAVE_DIR = config.VOICE_SAVE_DIR
    if not os.path.exists(VOICE_SAVE_DIR):
        os.makedirs(VOICE_SAVE_DIR)
    filename = time.strftime("%Y%m%d-%H%M%S") + \
        f"-{random.randint(10000,99999)}.mp3"
    return os.path.join(VOICE_SAVE_DIR, filename)


def _apply_post_processing(path: str, style_hint: str | None = None):
    if AudioSegment is None or WhiteNoise is None:
        logger.debug("[TTS] 未安装 pydub，跳过後製處理。")
        return
    try:
        audio = AudioSegment.from_file(path)
    except Exception as exc:
        logger.warning(f"[TTS] 語音後製載入失敗: {exc}")
        return

    audio = audio.set_frame_rate(44100).set_channels(1)
    target_dbfs = -18.0
    if audio.dBFS > target_dbfs:
        audio = audio.apply_gain(target_dbfs - audio.dBFS)

    fade_in_ms = 120
    fade_out_ms = 160
    audio = audio.fade_in(fade_in_ms).fade_out(fade_out_ms)

    noise_level = -48
    try:
        noise = WhiteNoise().to_audio_segment(duration=len(audio), volume=noise_level)
        audio = audio.overlay(noise)
    except Exception as exc:
        logger.debug(f"[TTS] 添加底噪失敗: {exc}")

    base_speed = 1.08
    if style_hint and "slow" in style_hint:
        speed = 0.95
    else:
        speed = base_speed
    try:
        audio = audio.speedup(playback_speed=speed, crossfade=60)
    except Exception as exc:
        logger.debug(f"[TTS] 調整語速失敗: {exc}")

    try:
        raise_factor = 1.12 if "slow" not in (style_hint or "") else 1.05
        pitch_up = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * raise_factor)})
        audio = pitch_up.set_frame_rate(audio.frame_rate)
    except Exception as exc:
        logger.debug(f"[TTS] 調整音調失敗: {exc}")

    if style_hint and ("smile" in style_hint or "笑" in style_hint):
        audio = audio.apply_gain(+1.2)

    try:
        audio.export(path, format="mp3")
    except Exception as exc:
        logger.warning(f"[TTS] 後製輸出失敗: {exc}")


async def generate_voice(text, voice="shimmer", style_hint: str | None = None):
    """
    生成TTS語音，並套用自然化後製。
    """
    file_path = _get_unique_voice_path()
    openai = get_tts_client()
    import asyncio
    loop = asyncio.get_event_loop()

    def tts_task():
        try:
            prompt_text = f"{style_hint} {text}".strip() if style_hint else text
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=prompt_text,
                response_format="mp3"
            )
            with open(file_path, "wb") as f:
                f.write(response.content if hasattr(
                    response, "content") else response["audio"])
            logger.info(f"[TTS] 语音生成成功: {file_path} ({text[:20]}...) | voice={voice}")
            _apply_post_processing(file_path, style_hint=style_hint)
            return file_path
        except Exception as e:
            logger.error(f"[TTS] 生成语音失败: {e}")
            return None
    return await loop.run_in_executor(None, tts_task)
