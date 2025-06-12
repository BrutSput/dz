import os
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.utils.token import TokenValidationError
from dotenv import load_dotenv

from app.core.config import settings


from bot.handlers.handlers import router

load_dotenv()

logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(token=settings.bot_tockn)
    dp = Dispatcher()
    dp.include_routers(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


asyncio.run(main())