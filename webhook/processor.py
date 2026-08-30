from db import accounts as db_accounts
from db import events as db_events
from db.pool import get_pool
from logger import logger
from webhook.meta_client import MetaAPIError, send_private_reply


async def _rules_for_account(account_id: int) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT r.id, r.name, r.keyword, r.message
        FROM rules r
        JOIN rule_accounts ra ON ra.rule_id = r.id
        WHERE ra.account_id = $1
        """,
        account_id,
    )
    return [dict(r) for r in rows]


async def process_comment_event(ig_user_id: str, comment_id: str, comment_text: str) -> None:
    event_id = comment_id

    account = await db_accounts.get_account_by_ig_user_id(ig_user_id)
    if not account:
        logger.info(f"Комментарий от неизвестного Instagram-аккаунта {ig_user_id}, пропуск.")
        return

    # атомарная защита от повторной обработки одного и того же webhook-события
    first_time = await db_events.try_mark_processed(event_id, account["id"], "processing")
    if not first_time:
        logger.info(f"Событие {event_id} уже было обработано ранее, повторный webhook пропущен.")
        return

    if not account["is_active"]:
        logger.info(f"Аккаунт @{account['username']} деактивирован, комментарий {event_id} пропущен.")
        await db_events.update_result(event_id, "account_inactive")
        return

    normalized_comment = comment_text.strip().lower()
    rules = await _rules_for_account(account["id"])

    matched = next((r for r in rules if r["keyword"].strip().lower() == normalized_comment), None)
    if not matched:
        logger.info(f"Комментарий '{comment_text}' не совпал ни с одним правилом аккаунта @{account['username']}.")
        await db_events.update_result(event_id, "no_match")
        return

    try:
        await send_private_reply(comment_id, matched["message"], account["access_token"])
        logger.info(
            f"Private reply отправлен по комментарию {comment_id} "
            f"(правило «{matched['name']}», аккаунт @{account['username']})."
        )
        await db_events.update_result(event_id, "sent")
    except MetaAPIError as e:
        if e.is_auth_error:
            await db_accounts.mark_needs_reauth(account["id"], str(e))
            logger.error(f"Аккаунт @{account['username']} помечен как требующий переподключения: {e}")
        else:
            logger.error(f"Не удалось отправить private reply для комментария {comment_id}: {e}")
        await db_events.update_result(event_id, "error")
    except Exception as e:
        logger.exception(f"Неожиданная ошибка при обработке комментария {comment_id}: {e}")
        await db_events.update_result(event_id, "error")