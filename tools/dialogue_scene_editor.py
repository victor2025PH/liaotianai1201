import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml

import config
from utils import prompt_manager

DEFAULT_PATH = Path(prompt_manager.SCENE_SCRIPTS_PATH)
BACKUP_SUFFIX = ".bak"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return config.load_yaml(str(path)) or {}


def save_yaml(path: Path, data: dict):
    validated = prompt_manager.validate_scene_scripts(data)
    backup_path = path.with_suffix(path.suffix + BACKUP_SUFFIX)
    if path.exists():
        shutil.copy(path, backup_path)
        print(f"已備份原檔至 {backup_path}")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            validated,
            f,
            allow_unicode=True,
            sort_keys=True,
            default_flow_style=False,
        )
    print(f"已寫入 {path}")


def cmd_list(data: dict, scene: str | None):
    validated = prompt_manager.validate_scene_scripts(data) if data else {}
    if not validated:
        print("目前沒有任何場景話術。")
        return
    if scene:
        scene = scene.strip()
        if scene not in validated:
            print(f"找不到場景 {scene}")
            return
        print(f"場景 {scene}：")
        for lang, lines in validated[scene].items():
            print(f"  語言 {lang}:")
            for idx, line in enumerate(lines, start=1):
                print(f"    {idx}. {line}")
    else:
        print("目前可用場景：")
        for key in sorted(validated.keys()):
            langs = ", ".join(sorted(validated[key].keys()))
            print(f"- {key} ({langs})")


def cmd_add(path: Path, data: dict, scene: str, lang: str, line: str):
    scene = scene.strip()
    lang = lang.strip()
    line = line.strip()
    if not scene or not lang or not line:
        print("場景、語言與話術內容不可為空。", file=sys.stderr)
        sys.exit(2)
    scene_map = data.setdefault(scene, {})
    lang_lines = scene_map.setdefault(lang, [])
    lang_lines.append(line)
    save_yaml(path, data)


def cmd_new_scene(path: Path, data: dict, scene: str, lang: str | None, line: str | None):
    scene = scene.strip()
    if not scene:
        print("場景名稱不可為空。", file=sys.stderr)
        sys.exit(2)
    if scene in data:
        print(f"場景 {scene} 已存在，可使用 add 指令新增話術。", file=sys.stderr)
        sys.exit(2)
    data[scene] = {}
    if lang and line:
        data[scene][lang.strip()] = [line.strip()]
    save_yaml(path, data)


def cmd_remove(path: Path, data: dict, scene: str, lang: str, index: int | None):
    scene = scene.strip()
    lang = lang.strip()
    if scene not in data or lang not in data[scene]:
        print(f"找不到場景/語言: {scene} / {lang}")
        sys.exit(2)
    if index is None:
        del data[scene][lang]
        if not data[scene]:
            del data[scene]
        save_yaml(path, data)
        return
    lines = data[scene][lang]
    if index < 1 or index > len(lines):
        print(f"索引超出範圍 (1~{len(lines)})")
        sys.exit(2)
    removed = lines.pop(index - 1)
    print(f"已移除：{removed}")
    if lines:
        data[scene][lang] = lines
    else:
        del data[scene][lang]
        if not data[scene]:
            del data[scene]
    save_yaml(path, data)


def build_parser():
    parser = argparse.ArgumentParser(description="管理 dialogue_scene_scripts.yaml")
    parser.add_argument(
        "--path",
        default=str(DEFAULT_PATH),
        help="自訂 YAML 路徑 (預設為 ai_models/dialogue_scene_scripts.yaml)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="列出全部或指定場景")
    list_cmd.add_argument("scene", nargs="?", help="指定場景名稱")

    add_cmd = sub.add_parser("add", help="在既有場景新增話術")
    add_cmd.add_argument("scene")
    add_cmd.add_argument("lang")
    add_cmd.add_argument("line")

    new_cmd = sub.add_parser("new", help="建立新場景")
    new_cmd.add_argument("scene")
    new_cmd.add_argument("--lang")
    new_cmd.add_argument("--line")

    remove_cmd = sub.add_parser("remove", help="移除場景或特定話術")
    remove_cmd.add_argument("scene")
    remove_cmd.add_argument("lang")
    remove_cmd.add_argument("index", nargs="?", type=int, help="要刪除的話術索引 (省略則移除整個語言)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    target = Path(args.path)
    data = load_yaml(target)

    if args.command == "list":
        cmd_list(data, args.scene)
    elif args.command == "add":
        cmd_add(target, data, args.scene, args.lang, args.line)
    elif args.command == "new":
        cmd_new_scene(target, data, args.scene, args.lang, args.line)
    elif args.command == "remove":
        cmd_remove(target, data, args.scene, args.lang, args.index)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
