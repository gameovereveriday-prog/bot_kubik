import aiosqlite

DB_PATH = "data/stats.db"


async def init_db():
    import os
    os.makedirs("data", exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                chat_id INTEGER,
                user_id INTEGER,
                name TEXT,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        await db.commit()


async def record_result(chat_id: int, user_id: int, name: str, result: str):
    """result: 'win' | 'loss' | 'draw'"""
    column = {"win": "wins", "loss": "losses", "draw": "draws"}[result]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO stats (chat_id, user_id, name, wins, losses, draws)
            VALUES (?, ?, ?, 0, 0, 0)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET name = excluded.name
        """, (chat_id, user_id, name))
        await db.execute(
            f"UPDATE stats SET {column} = {column} + 1 WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id)
        )
        await db.commit()


async def get_user_stats(chat_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT name, wins, losses, draws FROM stats WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id)
        ) as cursor:
            return await cursor.fetchone()


async def get_top_stats(chat_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT name, wins, losses, draws
            FROM stats
            WHERE chat_id = ?
            ORDER BY wins DESC, losses ASC
            LIMIT ?
        """, (chat_id, limit)) as cursor:
            return await cursor.fetchall()