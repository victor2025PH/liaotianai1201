import os
import random
import config

EMOJI_ROOT = config.EMOJI_ROOT


def auto_discover_emoji_groups():
    """
    扫描本地emoji分组目录，自动发现所有分组和图片文件
    返回: (分组名列表, {分组名: [图片路径, ...]})
    """
    groups = []
    group_files = {}
    if not os.path.exists(EMOJI_ROOT):
        os.makedirs(EMOJI_ROOT)
    for d in os.listdir(EMOJI_ROOT):
        group_dir = os.path.join(EMOJI_ROOT, d)
        if os.path.isdir(group_dir):
            files = [os.path.join(group_dir, f) for f in os.listdir(group_dir)
                     if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))]
            if files:
                groups.append(d)
                group_files[d] = files
    return groups, group_files


EMOJI_GROUPS, EMOJI_GROUP_FILES = auto_discover_emoji_groups()


def get_group_emoji(group: str):
    """
    从指定分组随机选一张emoji图片
    """
    files = EMOJI_GROUP_FILES.get(group, [])
    if not files:
        return None
    return random.choice(files)


def get_random_emoji():
    """
    随机从所有分组抽取emoji图片
    """
    group_list = list(EMOJI_GROUPS)
    random.shuffle(group_list)
    for g in group_list:
        e = get_group_emoji(g)
        if e:
            return e
    return None


def match_emoji_group(text, repeat_count=1, user_id=None, persona_tags=None):
    """
    智能分组判定（可AI判断、也可按关键词/标签优先匹配）
    """
    text = (text or "").lower()
    persona_tags = persona_tags or []
    if "开心" in text or "哈哈" in text or "😄" in text or "高兴" in text:
        return "happy" if "happy" in EMOJI_GROUPS else None
    if "兄弟" in text or "合作" in text or "生意" in text:
        return "business" if "business" in EMOJI_GROUPS else None
    if "冷" in text or repeat_count > 3:
        return "cold" if "cold" in EMOJI_GROUPS else None
    # ... 可自定义更多分组规则
    return random.choice(list(EMOJI_GROUPS)) if EMOJI_GROUPS else None


async def send_image_as_reply(message, img_path):
    """
    适配Telegram/微信/企业IM，自动发送表情包图片
    """
    import os
    ext = os.path.splitext(img_path)[-1].lower()
    try:
        if ext in [".jpg", ".jpeg", ".png"]:
            await message.reply_photo(img_path)
        elif ext == ".webp":
            try:
                await message.reply_sticker(img_path)
            except Exception:
                await message.reply_photo(img_path)
        elif ext == ".gif":
            await message.reply_animation(img_path)
        else:
            await message.reply("抱歉，这个表情文件暂不支持~")
    except Exception as e:
        print(f"[emoji_manager] 发送表情图片失败: {img_path}, {e}")


async def send_emoji_by_ai(message, msg_text, emoji_freq_control, count_dict, user_id):
    """
    按频率自动AI分发emoji图片
    emoji_freq_control: (min_freq, max_freq)
    count_dict: {user_id: 当前计数, f'{user_id}_target': 目标频次}
    user_id: str/int
    """
    if user_id not in count_dict:
        count_dict[user_id] = 0
        count_dict[f"{user_id}_target"] = random.randint(*emoji_freq_control)
    count_dict[user_id] += 1
    if count_dict[user_id] >= count_dict[f"{user_id}_target"]:
        group = match_emoji_group(msg_text, 1, user_id=user_id)
        img_path = get_group_emoji(group) if group else get_random_emoji()
        if img_path:
            await send_image_as_reply(message, img_path)
        count_dict[user_id] = 0
        count_dict[f"{user_id}_target"] = random.randint(*emoji_freq_control)

if __name__ == "__main__":
    print("表情分组池扫描完成，已发现分组：", EMOJI_GROUPS)
