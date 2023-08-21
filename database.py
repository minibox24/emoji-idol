import json

import aiosqlite

db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global db

    if db is None:
        db = await aiosqlite.connect("./data.db")

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS level (
            user_id INTEGER PRIMARY KEY,
            count INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS noticed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL
        )
        """
    )

    return db


async def get_user_count(user_id: int) -> int:
    db = await get_db()

    async with db.execute(
        """
        SELECT count FROM level WHERE user_id = ?
        """,
        (user_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        return 0

    return row[0]


async def set_user_count(user_id: int, count: int) -> None:
    db = await get_db()

    await db.execute(
        """
        INSERT INTO level (user_id, count)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET count = ?
        """,
        (user_id, count, count),
    )

    await db.commit()


async def get_users() -> tuple[int, int]:
    db = await get_db()

    async with db.execute(
        """
        SELECT user_id, count FROM level
        ORDER BY count DESC
        """
    ) as cursor:
        rows = await cursor.fetchall()

    return rows


async def is_noticed(data) -> bool:
    db = await get_db()
    data = json.dumps(data)

    async with db.execute(
        """
        SELECT id FROM noticed WHERE data = ?
        """,
        (data,),
    ) as cursor:
        row = await cursor.fetchone()

    return row is not None


async def set_noticed(data) -> None:
    db = await get_db()

    data = json.dumps(data)

    await db.execute(
        """
        INSERT INTO noticed (data)
        VALUES (?)
        """,
        (data,),
    )

    await db.commit()
