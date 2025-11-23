"""
資料庫遷移定義。

每個遷移以 dict 定義：
{
    "version": "20241024_add_indexes",
    "description": "為 chat_history.user_id 建立索引以加速查詢",
    "statements": [
        "CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id)",
    ],
}
"""

MIGRATIONS = [
    {
        "version": "20241024_add_indexes",
        "description": "為 chat_history.user_id 及 users.tags 建立索引",
        "statements": [
            "CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_tags ON users(tags)",
        ],
    },
]

