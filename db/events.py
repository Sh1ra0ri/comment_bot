from db.pool import get_pool


async def try_mark_processed(event_id: str, account_id: int | None, result: str) -> bool:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO processed_events (event_id, account_id, result)
        VALUES ($1, $2, $3)
        ON CONFLICT (event_id) DO NOTHING
        RETURNING event_id
        """,
        event_id,
        account_id,
        result,
    )
    return row is not None


async def update_result(event_id: str, result: str) -> None:
    pool = get_pool()
    await pool.execute(
        "UPDATE processed_events SET result = $1 WHERE event_id = $2",
        result,
        event_id,
    )