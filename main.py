import logging
import requests
import locale
from datetime import datetime
import rosario
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, FSInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
from bs4 import BeautifulSoup
from openai import OpenAI
import os
from aiohttp import web

# ---------- Настройки ----------
BOT_TOKEN = '7247038755:AAE2GEPMR-XDaoFoTIZWidwH-ZQfD7g36pE'
TOGETHER_API_KEY = "09392b9d19cab71d0a2300b1df5ca81df0b78a1f97457528d4ef53f5e25c60c1"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

user_data = {}
user_state = {}
user = {'in_pray': False, 'pray_done': False}
language = 'español'

client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")

# ---------- Web сервер ----------
async def handle(request):
    return web.Response(text="Rosary bot is running 🙏")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.getenv("PORT", 8080))  # Render автоматически даёт PORT
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server running on port {port}")

# ---------- Основные команды ----------
async def set_main_menu(bot: Bot):
    main_menu_commands = [BotCommand(command='/start', description='🙏Empezar')]
    await bot.set_my_commands(main_menu_commands)

dp.startup.register(set_main_menu)

# ---------- Фоновая задача уведомлений ----------
async def notify_users():
    while True:
        current_time = datetime.now().time()
        for user_id in user_data.keys():
            if not user['in_pray'] and not user['pray_done'] and current_time.hour == 20 and current_time.minute == 30:
                try:
                    await bot.send_message(user_id, f'⏰ ¡Es hora de rezar el Rosario! ({datetime.now().hour}:{datetime.now().minute})')
                except Exception as e:
                    logging.error(f"Error enviando notificación a {user_id}: {e}")
        await asyncio.sleep(60)

# ---------- Запуск бота и веб-сервера ----------
async def main():
    # Запуск бота
    asyncio.create_task(dp.start_polling(bot))
    # Запуск веб-сервера
    await start_web_server()
    # Запуск фоновой задачи уведомлений
    asyncio.create_task(notify_users())
    # Чтобы процесс не завершался
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())


