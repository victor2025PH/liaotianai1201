import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, AuthKeyUnregistered

import config

STATE_FILE = Path("login_state.json")


async def run_login(phone: str, code: str | None, password: str | None):
    app = Client(
        config.SESSION_NAME,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        workdir=".",
    )
    await app.connect()
    authorized = False
    try:
        me = await app.get_me()
        if me:
            authorized = True
    except AuthKeyUnregistered:
        authorized = False
    if authorized:
        print("ALREADY_AUTHORIZED")
        await app.disconnect()
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        return

    if code:
        if not STATE_FILE.exists():
            print("ERROR:CODE_HASH_NOT_FOUND")
            await app.disconnect()
            return
        state = json.loads(STATE_FILE.read_text())
        phone_code_hash = state.get("phone_code_hash")
        try:
            try:
                await app.sign_in(phone, phone_code_hash, code)
            except SessionPasswordNeeded:
                if not password:
                    print("PASSWORD_REQUIRED")
                    return
                await app.check_password(password)
                if STATE_FILE.exists():
                    STATE_FILE.unlink()
                print("LOGIN_SUCCESS")
                return
            if STATE_FILE.exists():
                STATE_FILE.unlink()
            print("LOGIN_SUCCESS")
        finally:
            await app.disconnect()
    else:
        sent_code = await app.send_code(phone)
        STATE_FILE.write_text(json.dumps({"phone": phone, "phone_code_hash": sent_code.phone_code_hash}))
        print("CODE_SENT")
        await app.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Pyrogram login helper")
    parser.add_argument("--phone", required=True, help="Telegram phone number")
    parser.add_argument("--code", help="Verification code")
    parser.add_argument("--password", help="Two-step verification password")
    args = parser.parse_args()
    asyncio.run(run_login(args.phone, args.code, args.password))


if __name__ == "__main__":
    main()
