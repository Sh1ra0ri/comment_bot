import asyncio
from typing import Awaitable, Callable, Optional

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import PlainTextResponse

from config import settings
from db import accounts as db_accounts
from db import oauth as db_oauth
from db.pool import close_pool, init_pool, run_migrations
from logger import logger, setup_logging
from webhook.meta_client import (
    MetaAPIError,
    exchange_code_for_token,
    get_ig_business_account,
    get_long_lived_token,
)
from webhook.processor import process_comment_event

app = FastAPI()

notify_bot: Optional[Callable[[int, str], Awaitable[None]]] = None


@app.on_event("startup")
async def on_startup() -> None:
    setup_logging()
    await init_pool()
    await run_migrations()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_pool()


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
) -> Response:
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        return PlainTextResponse(hub_challenge)
    return PlainTextResponse("Forbidden", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict:
    payload = await request.json()
    logger.info(f"Получено webhook-событие от Meta: {payload}")

    for entry in payload.get("entry", []):
        ig_user_id = entry.get("id")
        for change in entry.get("changes", []):
            if change.get("field") != "comments":
                continue
            value = change.get("value", {})
            comment_id = value.get("id")
            comment_text = value.get("text", "")
            if not comment_id:
                continue
            asyncio.create_task(process_comment_event(ig_user_id, comment_id, comment_text))

    return {"status": "ok"}


@app.get("/oauth/callback")
async def oauth_callback(code: str = "", state: str = "") -> PlainTextResponse:
    telegram_id = await db_oauth.pop_state(state)
    if telegram_id is None:
        return PlainTextResponse("Неверный или устаревший state.", status_code=400)

    try:
        token_data = await exchange_code_for_token(code)
        long_lived = await get_long_lived_token(token_data["access_token"])
        ig_info = await get_ig_business_account(long_lived["access_token"])
        await db_accounts.create_account(
            ig_user_id=ig_info["ig_user_id"],
            username=ig_info["username"],
            access_token=ig_info["access_token"],
        )
        text = f"Аккаунт успешно подключён."
        response_text = f"Аккаунт @{ig_info['username']} успешно подключён. Можно закрыть эту страницу."
    except MetaAPIError as e:
        logger.error(f"Ошибка подключения Instagram-аккаунта для telegram_id={telegram_id}: {e}")
        text = f"Не удалось подключить аккаунт: {e}"
        response_text = text

    if notify_bot is not None:
        await notify_bot(telegram_id, text)

    return PlainTextResponse(response_text)