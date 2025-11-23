import argparse
from datetime import datetime

from tabulate import tabulate

from tools.session_manager.account_db import (
    DEFAULT_DB_PATH,
    init_db,
    list_accounts,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Session 帳號狀態看板")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="資料庫路徑")
    parser.add_argument("--init", action="store_true", help="若資料庫不存在則初始化")
    return parser.parse_args()


def main():
    args = parse_args()
    db_path = DEFAULT_DB_PATH if args.db == str(DEFAULT_DB_PATH) else args.db
    if args.init:
        init_db(db_path)
        print(f"已初始化資料庫：{db_path}")

    rows = list_accounts(db_path)
    headers = ["Phone", "Display", "Roles", "Status", "Session Path", "Session String", "Last Heartbeat"]
    formatted = []
    for phone, display, roles, status, session_path, session_string_path, last_hb in rows:
        last_hb_fmt = last_hb or "-"
        formatted.append([phone, display or "-", roles or "-", status, session_path, session_string_path or "-", last_hb_fmt])
    print(tabulate(formatted, headers=headers, tablefmt="grid"))
    print(f"更新時間：{datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()

