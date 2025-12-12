from openai import AsyncOpenAI
import config
import logging
import base64
import mimetypes
import json
import re
from utils.prompt_manager import (
    build_dynamic_prompt,
    optimize_master_reply,
    check_bad_ai_reply,
    get_cold_scene_phrase,
    get_structured_fewshots,
    get_name_extraction_prompt,
    resolve_language_code,
    ANGELA_CONFIG,
)
from utils.ai_context_manager import add_to_history, get_history

logger = logging.getLogger("business_ai")

def get_openai_client():
    """獲取 OpenAI 客戶端，每次都重新讀取 API Key"""
    import os
    from dotenv import load_dotenv
    # 重新加載 .env 文件以獲取最新的 API Key
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY") or config.OPENAI_API_KEY
    return AsyncOpenAI(api_key=api_key)

VISION_FALLBACK_REPLY = {
    "chat_screenshot": {
        "zh": "我有看到你傳來的聊天截圖，如果需要我幫你看哪一段對話或整理重點，再跟我說細節喔。",
        "en": "I noticed you shared a chat screenshot. Let me know which part you’d like me to focus on and I’ll walk you through it.",
    },
    "person_photo": {
        "zh": "謝謝你分享照片！我會記得這份氛圍，有什麼想聊的或要請我幫忙的，也可以直接說。",
        "en": "Thanks for the photo! I’ll keep that vibe in mind—just tell me what you’d like to talk about next.",
    },
    "poster_or_promo": {
        "zh": "這張海報看起來挺有意思，要不要我幫你整理亮點或安排相關活動資訊？",
        "en": "That poster looks interesting! Want me to highlight its key points or get you set up with the related activity info?",
    },
    "other_scene": {
        "zh": "我有收到你分享的照片，如果想聊聊裡面的場景或感受，可以直接告訴我喔！",
        "en": "Got the picture you shared! If there’s anything about the scene you’d like to discuss, just let me know.",
    },
}

VISION_FALLBACK_NOTE = {
    "zh": "這張圖片暫時和我們討論的主題無關，我先幫你記下來，需要再聊的話提醒我。",
    "en": "This image doesn’t seem tied to our current chat, so I’ll keep it noted—just ping me if you want to dive into it later.",
}


# --- v5.0 新增功能：专用于识别名字的AI调用 ---
async def ai_extract_name_from_reply(user_text):
    """
    调用AI判断一段文本是否为名字。
    :param user_text: 用户回复的文本。
    :return: 如果是名字，返回该名字字符串；否则返回 None。
    """
    prompt = get_name_extraction_prompt(user_text)
    try:
        client = get_openai_client()
        resp = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # 使用更快速、便宜的模型进行简单判断
            messages=[{"role": "system", "content": prompt}],
            temperature=0,
            max_tokens=20
        )
        result = resp.choices[0].message.content.strip()
        logger.info(f"名字识别AI结果: '{result}'")
        # 如果AI返回"null"或内容过长，则认为不是名字
        if result.lower() == "null" or len(result) > 10:
            return None
        return result
    except Exception as e:
        logger.error(f"名字识别AI调用失败: {e}")
        return None


async def ai_business_reply(user_id, user_profile, context_info=None, history_summary="", use_name_in_prompt=False):
    """
    生成AI文本（只返回文本），自动日志。业务方向主动输出。
    """
    context_info = context_info or {}
    language = resolve_language_code(context_info.get("language"))

    logger.info(
        f"[AI] 开始AI回复，用户{user_id}, profile={user_profile}, use_name={use_name_in_prompt}, context={context_info}, language={language}")

    history = await get_history(user_id, max_len=config.CONTEXT_WINDOW)

    prompt = build_dynamic_prompt(
        user_profile,
        {**context_info, "language": language},
        history_summary,
        use_name_in_prompt=use_name_in_prompt,
    )

    fewshots = get_structured_fewshots(language)
    messages = [{"role": "system", "content": prompt}]
    messages.extend(fewshots)
    if history:
        for h in history:
            if h["role"] in ("user", "assistant"):
                messages.append({"role": h["role"], "content": h["content"]})

    logger.info(f"[AI] OpenAI messages构建: {messages}")
    client = get_openai_client()
    resp = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        temperature=0.78,
        max_tokens=512,
    )
    ai_reply = resp.choices[0].message.content.strip()
    ai_reply = optimize_master_reply(ai_reply, language=language)
    logger.info(f"[AI] OpenAI原始回复: {ai_reply}")

    if not check_bad_ai_reply(ai_reply, language=language):
        await add_to_history(user_id, "assistant", ai_reply)
        logger.info(f"[AI] 写入历史成功: {ai_reply}")
        return ai_reply

    cold = get_cold_scene_phrase(language)
    await add_to_history(user_id, "assistant", cold)
    logger.warning(f"[AI] AI腔/冷场触发: {cold}")
    return cold


async def analyze_image_message(user_id, image_path, user_profile, context_info=None, language=None):
    """
    使用 OpenAI Vision 模型分析圖片，若與對話無關則回傳 NO_REPLY。
    """
    context_info = context_info or {}
    language = resolve_language_code(language or context_info.get("language"))
    pack = ANGELA_CONFIG["language_settings"]["packs"][language]

    history = await get_history(user_id, max_len=config.CONTEXT_WINDOW)
    history_text = "\n".join(
        [f"{item['role']}: {item['content']}" for item in history]
    ) or "無歷史對話"

    instruction = pack["image_instruction"]

    media_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    try:
        stage = context_info.get("conversation_stage")
        triggered_intent = context_info.get("triggered_intent")
        prompt = (
            f"{instruction}\n"
            f"{pack['history_label']}:\n{history_text}\n"
            f"{pack['stage_label']}: {stage}, intent: {triggered_intent}"
        )
        data_uri = f"data:{media_type};base64,{image_data}"
        attempted_models = []

        json_instruction = (
            "You are an assistant that must output STRICT JSON.\n"
            "Analyze the incoming image with respect to the chat context.\n"
            "Return an object with the following fields:\n"
            "{\n"
            '  \"category\": one of [\"chat_screenshot\",\"person_photo\",\"poster_or_promo\",\"other_scene\"],\n'
            '  \"analysis_available\": boolean,\n'
            '  \"failure_reason\": string,\n'
            '  \"is_relevant\": boolean,\n'
            '  \"key_points\": [string,...],\n'
            '  \"summary\": string,\n'
            '  \"contextual_reply\": string,\n'
            '  \"availability_note\": string\n'
            "}\n"
            "If analysis is not possible set analysis_available=false and explain failure_reason.\n"
            "Ensure contextual_reply is concise, tailored to the conversation, and avoids verbatim transcription.\n"
            "If image content is unrelated to the current topic set is_relevant=false.\n"
        )

        def parse_json_output(raw: str) -> dict | None:
            if not raw:
                return None
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```json", "", cleaned, flags=re.IGNORECASE).strip()
                cleaned = re.sub(r"^```", "", cleaned).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                logger.error(f"[Vision] JSON parse 失敗: {cleaned}")
                return None

        async def call_model(model_name: str):
            client = get_openai_client()
            resp = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": json_instruction},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "text", "text": "Please respond with JSON only."},
                            {
                                "type": "image_url",
                                "image_url": {"url": data_uri},
                            },
                        ],
                    },
                ],
                max_tokens=200,
            )
            # OpenAI Chat Completions API 響應格式
            if resp.choices and len(resp.choices) > 0:
                message = resp.choices[0].message
                if hasattr(message, 'content') and message.content:
                    return message.content.strip()
            return ""

        model_candidates = [config.OPENAI_VISION_MODEL, "gpt-4o-mini"]

        for model_name in model_candidates:
            if model_name in attempted_models:
                continue
            attempted_models.append(model_name)
            try:
                raw_reply = await call_model(model_name)
                parsed = parse_json_output(raw_reply)
                if parsed:
                    parsed["model_used"] = model_name
                    category = parsed.get("category") or "other_scene"
                    lang = resolve_language_code(language)

                    contextual_reply = parsed.get("contextual_reply")
                    if not contextual_reply:
                        fallback = VISION_FALLBACK_REPLY.get(category, VISION_FALLBACK_REPLY["other_scene"])
                        parsed["contextual_reply"] = fallback.get(lang, fallback["zh"])

                    if not parsed.get("availability_note") and parsed.get("is_relevant") is False:
                        parsed["availability_note"] = VISION_FALLBACK_NOTE.get(lang, VISION_FALLBACK_NOTE["zh"])

                    key_points = parsed.get("key_points")
                    if key_points and isinstance(key_points, list):
                        parsed["key_points"] = [str(item) for item in key_points if isinstance(item, str)]

                    logger.info(f"[Vision] 圖片分析結構化結果 ({model_name}): {parsed}")
                    return parsed
                logger.warning(f"[Vision] 模型 {model_name} 回傳不可解析內容，嘗試下一個候選。")
            except Exception as resp_err:
                status = getattr(resp_err, "status", None)
                logger.error(f"[Vision] 模型 {model_name} 解析失敗: {resp_err}")
                if status in (401, 403):
                    raise
                if "model_not_found" in str(resp_err):
                    continue
                raise

        logger.warning("[Vision] 所有候選模型皆無法產出內容，返回 NO_REPLY。")
        return "NO_REPLY"
    except Exception as e:
        status = getattr(e, "status", None)
        logger.error(f"[Vision] 圖片分析失敗 (model={config.OPENAI_VISION_MODEL}, status={status}): {e}")
        if status in (401, 403):
            return "NO_REPLY"
        return ""
