#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的 Telegram Session 生成工具 - 防风控版本
包含以下防风控措施：
1. 随机延迟
2. 设备信息模拟
3. 速率限制
4. IP代理支持（可选）
5. 用户代理随机化
"""
import argparse
import asyncio
import os
import pathlib
import random
import sys
import time
from getpass import getpass
from typing import Optional
from datetime import datetime

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, FloodWait, PhoneNumberBanned
from pyrogram.raw.types import InputClientInfo

from tools.session_manager.crypto_utils import encrypt_bytes, prompt_passphrase


# 防风控配置
ANTI_DETECTION_CONFIG = {
    # 延迟配置（秒）
    "min_delay_before_connect": 2,  # 连接前最小延迟
    "max_delay_before_connect": 5,  # 连接前最大延迟
    "min_delay_after_code": 3,  # 输入验证码后最小延迟
    "max_delay_after_code": 8,  # 输入验证码后最大延迟
    "min_delay_between_sessions": 60,  # 两个session之间的最小间隔（秒）
    "max_delay_between_sessions": 180,  # 两个session之间的最大间隔（秒）
    
    # 设备信息模拟
    "device_model": [
        "iPhone 14 Pro",
        "iPhone 13 Pro Max",
        "Samsung Galaxy S23",
        "Xiaomi 13 Pro",
        "OnePlus 11",
    ],
    "system_version": [
        "iOS 17.0",
        "iOS 16.5",
        "Android 13",
        "Android 12",
    ],
    "app_version": [
        "10.0.0",
        "9.8.5",
        "9.7.2",
    ],
    "lang_code": "en",
    "system_lang_code": "en-US",
    
    # 速率限制
    "max_sessions_per_hour": 3,  # 每小时最多生成3个session
    "max_sessions_per_day": 10,  # 每天最多生成10个session
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="生成 Telegram Session（防风控版本）",
    )
    parser.add_argument("--api-id", type=int, help="Telegram API ID")
    parser.add_argument("--api-hash", help="Telegram API Hash")
    parser.add_argument("--phone", help="登入使用的手機號碼（含國碼）")
    parser.add_argument("--session-name", default="generated_session", help="Pyrogram session 名稱")
    parser.add_argument("--output-dir", default="sessions", help="儲存 session 的目錄")
    parser.add_argument("--encrypt", action="store_true", help="啟用加密輸出（建議）")
    parser.add_argument("--export-string", action="store_true", help="同時輸出 session string 檔案")
    parser.add_argument("--proxy", help="代理服务器 (格式: protocol://host:port 或 protocol://user:pass@host:port)")
    parser.add_argument("--skip-delay", action="store_true", help="跳过延迟（仅用于测试）")
    parser.add_argument("--device-info", help="自定义设备信息 (JSON格式)")
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


def random_delay(min_seconds: float, max_seconds: float):
    """随机延迟"""
    delay = random.uniform(min_seconds, max_seconds)
    print(f"[防风控] 延迟 {delay:.2f} 秒...")
    time.sleep(delay)


def get_random_device_info():
    """获取随机设备信息"""
    return {
        "device_model": random.choice(ANTI_DETECTION_CONFIG["device_model"]),
        "system_version": random.choice(ANTI_DETECTION_CONFIG["system_version"]),
        "app_version": random.choice(ANTI_DETECTION_CONFIG["app_version"]),
        "lang_code": ANTI_DETECTION_CONFIG["lang_code"],
        "system_lang_code": ANTI_DETECTION_CONFIG["system_lang_code"],
    }


def check_rate_limit(session_dir: pathlib.Path) -> tuple[bool, str]:
    """检查速率限制"""
    if not session_dir.exists():
        return True, ""
    
    now = time.time()
    hour_ago = now - 3600
    day_ago = now - 86400
    
    sessions = list(session_dir.glob("*.session"))
    sessions_hour = [s for s in sessions if s.stat().st_mtime > hour_ago]
    sessions_day = [s for s in sessions if s.stat().st_mtime > day_ago]
    
    if len(sessions_hour) >= ANTI_DETECTION_CONFIG["max_sessions_per_hour"]:
        return False, f"速率限制：过去1小时内已生成 {len(sessions_hour)} 个session（限制：{ANTI_DETECTION_CONFIG['max_sessions_per_hour']}）"
    
    if len(sessions_day) >= ANTI_DETECTION_CONFIG["max_sessions_per_day"]:
        return False, f"速率限制：过去24小时内已生成 {len(sessions_day)} 个session（限制：{ANTI_DETECTION_CONFIG['max_sessions_per_day']}）"
    
    return True, ""


def parse_proxy(proxy_str: str) -> Optional[dict]:
    """解析代理字符串"""
    if not proxy_str:
        return None
    
    try:
        # 格式: protocol://host:port 或 protocol://user:pass@host:port
        if "://" not in proxy_str:
            return None
        
        protocol, rest = proxy_str.split("://", 1)
        if "@" in rest:
            auth, host_port = rest.split("@", 1)
            username, password = auth.split(":", 1)
            host, port = host_port.split(":", 1)
            return {
                "scheme": protocol,
                "hostname": host,
                "port": int(port),
                "username": username,
                "password": password,
            }
        else:
            host, port = rest.split(":", 1)
            return {
                "scheme": protocol,
                "hostname": host,
                "port": int(port),
            }
    except Exception:
        print(f"[警告] 代理格式错误，将不使用代理: {proxy_str}")
        return None


def login_and_export(
    api_id: int,
    api_hash: str,
    phone: str,
    session_name: str,
    proxy: Optional[dict] = None,
    device_info: Optional[dict] = None,
    skip_delay: bool = False,
) -> tuple[str, str]:
    """
    回傳 (session_file_path, session_string)
    """
    # 检查速率限制
    session_dir = pathlib.Path("sessions")
    allowed, error_msg = check_rate_limit(session_dir)
    if not allowed:
        raise ValueError(error_msg)
    
    # 随机延迟（连接前）
    if not skip_delay:
        random_delay(
            ANTI_DETECTION_CONFIG["min_delay_before_connect"],
            ANTI_DETECTION_CONFIG["max_delay_before_connect"],
        )
    
    # 设备信息
    if not device_info:
        device_info = get_random_device_info()
    
    print(f"[设备信息] {device_info['device_model']} - {device_info['system_version']}")
    
    # 创建客户端
    client_kwargs = {
        "session_name": session_name,
        "api_id": api_id,
        "api_hash": api_hash,
        "workdir": ".",
        "device_model": device_info["device_model"],
        "system_version": device_info["system_version"],
        "app_version": device_info["app_version"],
        "lang_code": device_info["lang_code"],
        "system_lang_code": device_info["system_lang_code"],
    }
    
    if proxy:
        client_kwargs["proxy"] = proxy
        print(f"[代理] 使用代理: {proxy['hostname']}:{proxy['port']}")
    
    client = Client(**client_kwargs)
    
    try:
        print("[连接] 正在连接到 Telegram...")
        client.connect()
        
        # 检查是否已授权
        if client.is_authorized():
            me = client.get_me()
            print(f"[成功] 已授权: {me.first_name} (@{me.username or 'N/A'})")
            client.storage.save()
            session_path = pathlib.Path(client.storage.file.name).resolve()
            session_string = client.export_session_string()
            client.disconnect()
            return str(session_path), session_string
        
        # 发送验证码
        print(f"[验证码] 正在发送验证码到 {phone}...")
        try:
            sent = client.send_code(phone)
            print(f"[验证码] 验证码已发送，请查收")
        except PhoneNumberBanned:
            raise ValueError("手机号码已被封禁，请使用其他号码")
        except FloodWait as e:
            raise ValueError(f"触发速率限制，请等待 {e.value} 秒后重试")
        
        # 输入验证码
        code = input("輸入 Telegram 驗證碼（SMS 或 Telegram App）：").strip()
        
        # 延迟（输入验证码后）
        if not skip_delay:
            random_delay(
                ANTI_DETECTION_CONFIG["min_delay_after_code"],
                ANTI_DETECTION_CONFIG["max_delay_after_code"],
            )
        
        # 登录
        try:
            client.sign_in(phone, code, phone_code_hash=sent.phone_code_hash)
        except SessionPasswordNeeded:
            password = getpass("輸入兩步驗證密碼：")
            client.check_password(password)
        except FloodWait as e:
            raise ValueError(f"触发速率限制，请等待 {e.value} 秒后重试")
        
        # 验证登录
        me = client.get_me()
        print(f"[成功] 登录成功: {me.first_name} (@{me.username or 'N/A'})")
        
        # 保存session
        client.storage.save()
        session_path = pathlib.Path(client.storage.file.name).resolve()
        session_string = client.export_session_string()
        
    finally:
        if client.is_connected:
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
    
    print("=" * 60)
    print("Telegram Session 生成工具 - 防风控版本")
    print("=" * 60)
    print()
    
    api_id = int(prompt_if_missing(args.api_id, "輸入 Telegram API ID："))
    api_hash = prompt_if_missing(args.api_hash, "輸入 Telegram API Hash：")
    phone = prompt_if_missing(args.phone, "輸入手機號碼（含國碼）：")
    
    ensure_output_dir(pathlib.Path(args.output_dir))
    
    # 解析代理
    proxy = None
    if args.proxy:
        proxy = parse_proxy(args.proxy)
    
    # 解析设备信息
    device_info = None
    if args.device_info:
        import json
        device_info = json.loads(args.device_info)
    
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
            proxy=proxy,
            device_info=device_info,
            skip_delay=args.skip_delay,
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
    
    print()
    print("=" * 60)
    print("完成。請妥善保管 session 檔案與加密密碼。")
    print("=" * 60)
    print()
    print("[防风控提示]")
    print(f"  - 建议在生成下一个session前等待 {ANTI_DETECTION_CONFIG['min_delay_between_sessions']}-{ANTI_DETECTION_CONFIG['max_delay_between_sessions']} 秒")
    print(f"  - 每小时最多生成 {ANTI_DETECTION_CONFIG['max_sessions_per_hour']} 个session")
    print(f"  - 每天最多生成 {ANTI_DETECTION_CONFIG['max_sessions_per_day']} 个session")


if __name__ == "__main__":
    main()

