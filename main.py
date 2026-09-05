import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import API_TOKEN
from commands import router, setup_bot_commands

# Bot & Dispatcher Setup
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

async def handle_ping(request):
    return web.Response(text="RCC Professional Bot is Live!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await start_web_server()
    await setup_bot_commands(bot)
    print("\n" + "="*50)
    print("🚀 RCC PROFESSIONAL BOT IS LIVE AND RUNNING!")
    print("="*50 + "\n")
    
    try:
        # Pending updates delete karke fresh start
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())