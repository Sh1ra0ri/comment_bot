from config import settings
from db.pool import get_pool


async def is_admin(telegram_id: int) -> bool:
    pool = get_pool()
    row = await pool.fetchrow("SELECT 1 FROM admins WHERE telegram_id = $1", telegram_id)
    return row is not None


async def add_admin(telegram_id: int, added_by: int) -> None:
    pool = get_pool()
    await pool.execute(
        "INSERT INTO admins (telegram_id, added_by) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        telegram_id,
        added_by,
    )


async def remove_admin(telegram_id: int) -> None:
    pool = get_pool()
    await pool.execute("DELETE FROM admins WHERE telegram_id = $1", telegram_id)


async def list_admins() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch("SELECT * FROM admins ORDER BY id")
    return [dict(r) for r in rows]


async def count_admins() -> int:
    pool = get_pool()
    row = await pool.fetchrow("SELECT COUNT(*) AS cnt FROM admins")
    return row["cnt"]


async def seed_super_admin() -> None:
    await add_admin(settings.super_admin_id, added_by=settings.super_admin_id)