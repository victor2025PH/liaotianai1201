import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

DEFAULT_DB_PATH = Path("data/session_accounts.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT UNIQUE,
    display_name TEXT,
    session_path TEXT NOT NULL,
    session_string_path TEXT,
    roles TEXT DEFAULT 'player',
    status TEXT DEFAULT 'OFFLINE',
    throttle_profile TEXT DEFAULT '{}',
    last_heartbeat_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TRIGGER IF NOT EXISTS trg_accounts_updated_at
AFTER UPDATE ON accounts
FOR EACH ROW
BEGIN
    UPDATE accounts SET updated_at = datetime('now') WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS account_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    event TEXT NOT NULL,
    payload TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(account_id) REFERENCES accounts(id)
);
"""


@contextmanager
def get_conn(db_path: Path = DEFAULT_DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA)


@dataclass
class AccountRecord:
    phone: str
    display_name: Optional[str]
    roles: List[str]
    status: str
    session_path: str
    session_string_path: Optional[str]
    last_heartbeat_at: Optional[str]


def register_account(
    phone: str,
    session_path: str,
    display_name: Optional[str] = None,
    session_string_path: Optional[str] = None,
    roles: Optional[Iterable[str]] = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> None:
    roles_str = ",".join(roles) if roles else "player"
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO accounts (phone, display_name, session_path, session_string_path, roles, status)
            VALUES (?, ?, ?, ?, ?, 'OFFLINE')
            ON CONFLICT(phone) DO UPDATE SET
                display_name=excluded.display_name,
                session_path=excluded.session_path,
                session_string_path=excluded.session_string_path,
                roles=excluded.roles
            """,
            (phone, display_name, session_path, session_string_path, roles_str),
        )
        account_id = conn.execute("SELECT id FROM accounts WHERE phone=?", (phone,)).fetchone()[0]
        conn.execute(
            "INSERT INTO account_logs (account_id, event, payload) VALUES (?, ?, ?)",
            (account_id, "REGISTERED", None),
        )


def update_status(phone: str, status: str, db_path: Path = DEFAULT_DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE accounts SET status=?, last_heartbeat_at=datetime('now') WHERE phone=?",
            (status, phone),
        )
        account = conn.execute("SELECT id FROM accounts WHERE phone=?", (phone,)).fetchone()
        if account:
            conn.execute(
                "INSERT INTO account_logs (account_id, event, payload) VALUES (?, ?, ?)",
                (account[0], f"STATUS_{status}", None),
            )


def list_accounts(db_path: Path = DEFAULT_DB_PATH):
    with get_conn(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT phone, display_name, roles, status, session_path, session_string_path, last_heartbeat_at
            FROM accounts ORDER BY created_at DESC
            """
        )
        return cursor.fetchall()


def fetch_account_records(
    roles: Optional[Sequence[str]] = None,
    status_in: Optional[Sequence[str]] = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> List[AccountRecord]:
    conditions = []
    params: List[str] = []
    if roles:
        placeholders = ",".join("?" for _ in roles)
        conditions.append(
            f"(" + " OR ".join([f"roles LIKE '%' || ? || '%'" for _ in roles]) + ")"
        )
        params.extend(roles)
    if status_in:
        placeholders = ",".join("?" for _ in status_in)
        conditions.append(f"status IN ({placeholders})")
        params.extend(status_in)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT phone, display_name, roles, status, session_path, session_string_path, last_heartbeat_at
        FROM accounts
        {where_clause}
        ORDER BY created_at ASC
    """
    records: List[AccountRecord] = []
    with get_conn(db_path) as conn:
        for row in conn.execute(query, params):
            roles_list = row[2].split(",") if row[2] else []
            records.append(
                AccountRecord(
                    phone=row[0],
                    display_name=row[1],
                    roles=[role.strip() for role in roles_list if role.strip()],
                    status=row[3],
                    session_path=row[4],
                    session_string_path=row[5],
                    last_heartbeat_at=row[6],
                )
            )
    return records


def record_event(phone: str, event: str, payload: Optional[str] = None, db_path: Path = DEFAULT_DB_PATH) -> None:
    with get_conn(db_path) as conn:
        account = conn.execute("SELECT id FROM accounts WHERE phone=?", (phone,)).fetchone()
        if not account:
            raise ValueError(f"未知帳號：{phone}")
        conn.execute(
            "INSERT INTO account_logs (account_id, event, payload) VALUES (?, ?, ?)",
            (account[0], event, payload),
        )

