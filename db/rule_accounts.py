from db.pool import get_pool


class DuplicateKeywordError(Exception):
    """На этом аккаунте уже есть другое правило с таким же ключевым словом
    (без учёта регистра) — нельзя, т.к. неоднозначно, какое сообщение отправлять."""


async def link_rule_account(rule_id: int, account_id: int, keyword: str) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            conflict = await conn.fetchrow(
                """
                SELECT r.id
                FROM rules r
                JOIN rule_accounts ra ON ra.rule_id = r.id
                WHERE ra.account_id = $1
                  AND lower(r.keyword) = lower($2)
                  AND r.id != $3
                FOR UPDATE OF r
                """,
                account_id,
                keyword,
                rule_id,
            )
            if conflict:
                raise DuplicateKeywordError()
            await conn.execute(
                """
                INSERT INTO rule_accounts (rule_id, account_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
                """,
                rule_id,
                account_id,
            )


async def unlink_rule_account(rule_id: int, account_id: int) -> None:
    pool = get_pool()
    await pool.execute(
        "DELETE FROM rule_accounts WHERE rule_id = $1 AND account_id = $2",
        rule_id,
        account_id,
    )


async def is_linked(rule_id: int, account_id: int) -> bool:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT 1 FROM rule_accounts WHERE rule_id = $1 AND account_id = $2",
        rule_id,
        account_id,
    )
    return row is not None