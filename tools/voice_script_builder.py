import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.prompt_manager import resolve_language_code

PAUSE_PATTERN = re.compile(r"\[pause\s+([\d\.]+)\]", re.IGNORECASE)
TONE_PATTERN = re.compile(r"\[(smile|warm|calm|serious|slow|fast)\]", re.IGNORECASE)

TONE_HINTS = {
    "zh": {
        "smile": "（微笑著說）",
        "warm": "（語氣溫暖）",
        "calm": "（語調放慢柔和）",
        "serious": "（語氣稍微收斂）",
        "slow": "（語速放慢一點）",
        "fast": "（語速稍微加快）",
    },
    "en": {
        "smile": "(speaking with a smile)",
        "warm": "(warm tone)",
        "calm": "(calm, slower pace)",
        "serious": "(steady, grounded tone)",
        "slow": "(slow down slightly)",
        "fast": "(pick up the pace a bit)",
    },
}


def load_text(source: str | None) -> str:
    if not source:
        return ""
    path = Path(source)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return source


def convert_markups(text: str, language: str) -> str:
    lang = resolve_language_code(language)

    def replace_pause(match: re.Match):
        seconds = match.group(1)
        if lang == "zh":
            return f"（停頓{seconds}秒）"
        return f"(pause {seconds} seconds)"

    def replace_tone(match: re.Match):
        key = match.group(1).lower()
        hints = TONE_HINTS.get(lang, TONE_HINTS["en"])
        return hints.get(key, "")

    text = PAUSE_PATTERN.sub(replace_pause, text)
    text = TONE_PATTERN.sub(replace_tone, text)

    paragraphs = [seg.strip() for seg in text.split("\n") if seg.strip()]
    formatted = []
    for para in paragraphs:
        if lang == "zh":
            formatted.append(para.replace("。", "。 ").replace("，", "， "))
        else:
            formatted.append(para)
    return "\n".join(formatted).strip()


def main():
    parser = argparse.ArgumentParser(description="語音稿節奏標記轉換工具")
    parser.add_argument("text", nargs="?", default="", help="原始文本或檔案路徑")
    parser.add_argument("--language", "-l", default="zh", help="語言（預設 zh）")
    parser.add_argument("--output", "-o", help="輸出檔案路徑")
    args = parser.parse_args()

    raw = load_text(args.text)
    if not raw:
        print("未提供文本或檔案，指令結束。")
        return

    converted = convert_markups(raw, args.language)
    if args.output:
        Path(args.output).write_text(converted, encoding="utf-8")
        print(f"已寫入 {args.output}")
    else:
        print("------ 轉換結果 ------")
        print(converted)


if __name__ == "__main__":
    main()

