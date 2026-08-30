import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from db.admins import seed_super_admin
from db.pool import init_pool, run_migrations
from bot.handlers import accounts, admins as admins_handlers, common, rules
from bot.middlewares.admin_only import AdminOnlyMiddleware

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher(storage=MemoryStorage())

dp.message.middleware(AdminOnlyMiddleware())
dp.callback_query.middleware(AdminOnlyMiddleware())

dp.include_router(common.router)
dp.include_router(accounts.router)
dp.include_router(rules.router)
dp.include_router(admins_handlers.router)


async def start_bot() -> None:
    await init_pool()
    await run_migrations()
    await seed_super_admin()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())