from db.pool import get_pool


async def create_account(ig_user_id: str, username: str, access_token: str) -> int:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO instagram_accounts (ig_user_id, username, access_token)
        VALUES ($1, $2, $3)
        ON CONFLICT (ig_user_id) DO UPDATE
            SET username = EXCLUDED.username,
                access_token = EXCLUDED.access_token,
                needs_reauth = false,
                last_error = NULL
        RETURNING id
        """,
        ig_user_id,
        username,
        access_token,
    )
    return row["id"]


async def list_accounts() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT id, ig_user_id, username, is_active, needs_reauth FROM instagram_accounts ORDER BY username"
    )
    return [dict(r) for r in rows]


async def get_account(account_id: int) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow("SELECT * FROM instagram_accounts WHERE id = $1", account_id)
    return dict(row) if row else None


async def get_account_by_ig_user_id(ig_user_id: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow("SELECT * FROM instagram_accounts WHERE ig_user_id = $1", ig_user_id)
    return dict(row) if row else None


async def set_active(account_id: int, is_active: bool) -> None:
    pool = get_pool()
    await pool.execute("UPDATE instagram_accounts SET is_active = $1 WHERE id = $2", is_active, account_id)


async def delete_account(account_id: int) -> None:
    pool = get_pool()
    # rule_accounts удаляются каскадно (ON DELETE CASCADE), сами правила — нет
    await pool.execute("DELETE FROM instagram_accounts WHERE id = $1", account_id)


async def mark_needs_reauth(account_id: int, error: str) -> None:
    pool = get_pool()
    await pool.execute(
        "UPDATE instagram_accounts SET needs_reauth = true, last_error = $1 WHERE id = $2",
        error,
        account_id,
    )