import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils import prompt_manager


def main():
    parser = argparse.ArgumentParser(
        description="Validate dialogue_scene_scripts.yaml structure",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=prompt_manager.SCENE_SCRIPTS_PATH,
        help="Path to dialogue_scene_scripts.yaml (default: project ai_models/dialogue_scene_scripts.yaml)",
    )
    args = parser.parse_args()
    target = Path(args.path)
    if not target.exists():
        print(f"❌ 找不到檔案: {target}")
        sys.exit(1)
    try:
        prompt_manager.validate_scene_scripts_file(str(target))
    except Exception as exc:
        print(f"❌ 驗證失敗: {exc}")
        sys.exit(2)
    print(f"✅ 驗證通過: {target}")


if __name__ == "__main__":
    main()
