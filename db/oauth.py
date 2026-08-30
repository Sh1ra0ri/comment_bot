import secrets

from db.pool import get_pool


async def create_state(telegram_id: int) -> str:
    pool = get_pool()
    state = secrets.token_urlsafe(24)
    await pool.execute(
        "INSERT INTO oauth_states (state, telegram_id) VALUES ($1, $2)",
        state,
        telegram_id,
    )
    return state


async def pop_state(state: str) -> int | None:
    pool = get_pool()
    row = await pool.fetchrow(
        "DELETE FROM oauth_states WHERE state = $1 RETURNING telegram_id",
        state,
    )
    return row["telegram_id"] if row else None