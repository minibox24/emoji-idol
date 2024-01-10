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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            server INTEGER NOT NULL,
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


async def get_user_count(user_id: int, server: int) -> int:
    db = await get_db()

    async with db.execute(
        """
        SELECT count FROM level WHERE user_id = ? AND server = ?
        """,
        (user_id, server),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        return 0

    return row[0]


async def set_user_count(user_id: int, count: int, server: int) -> None:
    db = await get_db()

    existing_record = await db.execute(
        "SELECT * FROM level WHERE user_id = ? AND server = ?", (user_id, server)
    )

    existing_record = await existing_record.fetchone()

    if existing_record:
        await db.execute(
            "UPDATE level SET count = ? WHERE user_id = ? AND server = ?",
            (count, user_id, server),
        )
    else:
        await db.execute(
            "INSERT INTO level (user_id, server, count) VALUES (?, ?, ?)",
            (user_id, server, count),
        )

    # 트랜잭션 커밋
    await db.commit()


async def get_users(server: int) -> tuple[int, int]:
    db = await get_db()

    async with db.execute(
        """
        SELECT user_id, count FROM level
        WHERE server = ?
        ORDER BY count DESC
        """,
        (server,),
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
