import asyncio

import uvicorn

import webhook.main as webhook_main
from bot.main import bot, dp
from config import settings
from db.admins import seed_super_admin
from db.pool import init_pool, run_migrations
from logger import setup_logging


async def notify(telegram_id: int, text: str) -> None:
    try:
        await bot.send_message(telegram_id, text)
    except Exception:
        pass


async def main() -> None:
    setup_logging()
    await init_pool()
    await run_migrations()
    await seed_super_admin()

    webhook_main.notify_bot = notify

    uvicorn_config = uvicorn.Config(
        webhook_main.app,
        host=settings.webhook_host,
        port=settings.webhook_port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(uvicorn_config)

    await asyncio.gather(
        dp.start_polling(bot),
        server.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())