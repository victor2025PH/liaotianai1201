import argparse
import pathlib
import shutil
import sys
from typing import Iterable

from tools.session_manager.crypto_utils import decrypt_bytes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量匯入 Telegram session 檔案。")
    parser.add_argument("sources", nargs="+", help="待匯入的 session 檔案或目錄")
    parser.add_argument("--target-dir", default="sessions", help="匯入後的儲存目錄")
    parser.add_argument("--decrypt", action="store_true", help="若檔案已加密，啟用解密並輸入密碼")
    parser.add_argument("--password", help="直接指定解密密碼（會覆蓋互動輸入）")
    return parser.parse_args()


def iter_source_files(paths: Iterable[str]) -> Iterable[pathlib.Path]:
    for raw_path in paths:
        path = pathlib.Path(raw_path)
        if not path.exists():
            print(f"警告：來源不存在 {path}", file=sys.stderr)
            continue
        if path.is_dir():
            for file in path.glob("**/*"):
                if file.is_file():
                    yield file
        else:
            yield path


def copy_file(src: pathlib.Path, target_dir: pathlib.Path, decrypt: bool, password: str | None) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = src.suffix.lower()
    target_path = target_dir / src.name
    if decrypt and suffix.endswith(".enc"):
        data = src.read_bytes()
        pwd = password or input(f"檔案 {src.name} 的解密密碼：")
        plain = decrypt_bytes(data, pwd)
        target_plain = target_path.with_suffix("")
        target_plain.write_bytes(plain)
        print(f"已匯入並解密：{target_plain}")
    else:
        shutil.copy2(src, target_path)
        print(f"已匯入：{target_path}")


def main() -> None:
    args = parse_args()
    password = args.password
    for file_path in iter_source_files(args.sources):
        try:
            copy_file(file_path, pathlib.Path(args.target_dir), args.decrypt, password)
        except Exception as exc:
            print(f"匯入 {file_path} 時失敗：{exc}", file=sys.stderr)


if __name__ == "__main__":
    main()

