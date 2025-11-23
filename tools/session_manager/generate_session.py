import argparse
import os
import pathlib
import sys
from getpass import getpass
from typing import Optional

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded

from tools.session_manager.crypto_utils import encrypt_bytes, prompt_passphrase


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="生成 Telegram Session（支援加密存檔與匯入資料庫）。",
    )
    parser.add_argument("--api-id", type=int, help="Telegram API ID")
    parser.add_argument("--api-hash", help="Telegram API Hash")
    parser.add_argument("--phone", help="登入使用的手機號碼（含國碼）")
    parser.add_argument("--session-name", default="generated_session", help="Pyrogram session 名稱")
    parser.add_argument("--output-dir", default="sessions", help="儲存 session 的目錄")
    parser.add_argument("--encrypt", action="store_true", help="啟用加密輸出（建議）")
    parser.add_argument("--export-string", action="store_true", help="同時輸出 session string 檔案")
    return parser.parse_args()


def ensure_output_dir(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def prompt_if_missing(value: Optional[str], prompt_text: str) -> str:
    if value:
        return value
    entered = input(prompt_text).strip()
    if not entered:
        raise ValueError(f"{prompt_text} 不能為空。")
    return entered


def login_and_export(api_id: int, api_hash: str, phone: str, session_name: str) -> tuple[str, str]:
    """
    回傳 (session_file_path, session_string)
    """
    client = Client(
        session_name,
        api_id=api_id,
        api_hash=api_hash,
        workdir=".",
    )
    client.connect()
    try:
        if not client.is_authorized():
            sent = client.send_code(phone)
            code = input("輸入 Telegram 驗證碼（SMS 或 Telegram App）：").strip()
            try:
                client.sign_in(phone, code, phone_code_hash=sent.phone_code_hash)
            except SessionPasswordNeeded:
                password = getpass("輸入兩步驗證密碼：")
                client.check_password(password)
        client.storage.save()
        session_path = pathlib.Path(client.storage.file.name).resolve()
        session_string = client.export_session_string()
    finally:
        client.disconnect()
    return str(session_path), session_string


def write_session_file(session_path: str, target_dir: pathlib.Path, password: Optional[str]) -> str:
    source = pathlib.Path(session_path)
    if not source.exists():
        raise FileNotFoundError(f"找不到 session 檔案：{source}")
    target = target_dir / source.name
    data = source.read_bytes()
    if password:
        data = encrypt_bytes(data, password)
        target = target.with_suffix(target.suffix + ".enc")
    target.write_bytes(data)
    return str(target)


def write_session_string(
    session_string: str,
    target_dir: pathlib.Path,
    session_name: str,
    password: Optional[str],
) -> str:
    file_path = target_dir / f"{session_name}.session_string"
    data = session_string.encode("utf-8")
    if password:
        data = encrypt_bytes(data, password)
        file_path = file_path.with_suffix(file_path.suffix + ".enc")
    file_path.write_bytes(data)
    return str(file_path)


def main() -> None:
    args = parse_args()
    api_id = int(prompt_if_missing(args.api_id, "輸入 Telegram API ID："))
    api_hash = prompt_if_missing(args.api_hash, "輸入 Telegram API Hash：")
    phone = prompt_if_missing(args.phone, "輸入手機號碼（含國碼）：")

    ensure_output_dir(pathlib.Path(args.output_dir))

    encryption_password: Optional[str] = None
    if args.encrypt:
        try:
            encryption_password = prompt_passphrase(confirm=True)
        except ValueError as exc:
            print(f"密碼設置失敗：{exc}", file=sys.stderr)
            sys.exit(1)
        if not encryption_password:
            print("未輸入密碼，將以純文字儲存。")

    try:
        session_file_path, session_string = login_and_export(
            api_id=api_id,
            api_hash=api_hash,
            phone=phone,
            session_name=args.session_name,
        )
    except Exception as exc:
        print(f"登入或匯出 session 失敗：{exc}", file=sys.stderr)
        sys.exit(1)

    try:
        output_file = write_session_file(session_file_path, pathlib.Path(args.output_dir), encryption_password)
        print(f"Session 檔案已儲存至：{output_file}")
        if args.export_string:
            string_file = write_session_string(
                session_string=session_string,
                target_dir=pathlib.Path(args.output_dir),
                session_name=args.session_name,
                password=encryption_password,
            )
            print(f"Session string 已輸出：{string_file}")
    except Exception as exc:
        print(f"儲存 session 檔案時發生錯誤：{exc}", file=sys.stderr)
        sys.exit(1)

    print("完成。請妥善保管 session 檔案與加密密碼。")


if __name__ == "__main__":
    main()

