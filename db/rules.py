from db.pool import get_pool


async def create_rule(name: str, keyword: str, message: str) -> int:
    pool = get_pool()
    row = await pool.fetchrow(
        "INSERT INTO rules (name, keyword, message) VALUES ($1, $2, $3) RETURNING id",
        name,
        keyword,
        message,
    )
    return row["id"]


async def list_rules() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch("SELECT id, name, keyword FROM rules ORDER BY created_at")
    return [dict(r) for r in rows]


async def get_rule(rule_id: int) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow("SELECT * FROM rules WHERE id = $1", rule_id)
    return dict(row) if row else None


async def update_rule_field(rule_id: int, field: str, value: str) -> None:
    assert field in ("name", "keyword", "message"), f"Недопустимое поле: {field}"
    pool = get_pool()
    await pool.execute(f"UPDATE rules SET {field} = $1 WHERE id = $2", value, rule_id)


async def delete_rule(rule_id: int) -> None:
    pool = get_pool()
    await pool.execute("DELETE FROM rules WHERE id = $1", rule_id)


async def rule_accounts(rule_id: int) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT a.id, a.username
        FROM instagram_accounts a
        JOIN rule_accounts ra ON ra.account_id = a.id
        WHERE ra.rule_id = $1
        ORDER BY a.username
        """,
        rule_id,
    )
    return [dict(r) for r in rows]