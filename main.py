import logging
import requests
import locale
from datetime import datetime
import rosario
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
import asyncio
from bs4 import BeautifulSoup
from openai import OpenAI
import os
from aiohttp import web

# ======== Настройки ========
BOT_TOKEN = '7247038755:AAE2GEPMR-XDaoFoTIZWidwH-ZQfD7g36pE'
TOGETHER_API_KEY = "09392b9d19cab71d0a2300b1df5ca81df0b78a1f97457528d4ef53f5e25c60c1"

client = OpenAI(
    api_key=TOGETHER_API_KEY,
    base_url="https://api.together.xyz/v1"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

user_data = {}
user_state = {}
user_choices = {}

language = 'español'
user = {'in_pray': False, 'pray_done': False}
cycleOraciones = False
current_message = 0
cycle = 0
mystery = 0
aveMtimes = 0

# ======== Сервисы для Render ========
async def handle(request):
    return web.Response(text="Rosary bot is running 🙏")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# ======== Клавиатуры ========
def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Español", callback_data="lang:es"),
         InlineKeyboardButton(text="Latin", callback_data="lang:la")]
    ])

continuar = InlineKeyboardButton(text='▶️▶️', callback_data='continuar_pressed')
keyboard = InlineKeyboardMarkup(inline_keyboard=[[continuar]])

pray = InlineKeyboardButton(text='🙏Empezar a rezar el rosario🙏', callback_data='pray_pressed')
pray_keyboard = InlineKeyboardMarkup(inline_keyboard=[[pray]])

# ======== Установка меню ========
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/start', description='🙏Empezar')
    ]
    await bot.set_my_commands(main_menu_commands)

dp.startup.register(set_main_menu)

# ======== Хэндлер /start ========
@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message):
    msg = await message.answer(f'{rosario.textStart[language]}', reply_markup=get_language_keyboard())
    user_data[message.from_user.id] = msg.message_id
    await message.answer("Aún no has seleccionado un idioma.")

# ======== Выбор языка ========
@dp.callback_query(F.data.startswith("lang:"))
async def language_callback(callback: CallbackQuery):
    global language
    lang_code = callback.data.split(":")[1]
    language = "español" if lang_code == "es" else "latin"

    user_id = callback.from_user.id
    selected_msg_id = user_data.get(user_id)

    if selected_msg_id:
        try:
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=selected_msg_id,
                text=f"Escogiste el idioma para orar:  {'Español' if language=='español' else 'Latin'}",
                reply_markup=pray_keyboard
            )
        except Exception as e:
            logging.error(f"Ошибка при редактировании: {e}")
    await callback.answer()

# ======== Определение типа таинства ========
def get_mystery_type():
    wday = datetime.now().weekday()
    if wday == 0 or wday == 5:
        return 'gaudiosa'
    elif wday == 3:
        return 'luminosa'
    elif wday == 1 or wday == 4:
        return 'dolorosa'
    else:
        return 'gloriosa'

# ======== Запуск веб-сервера и бота ========
async def main():
    # Запуск веб-сервера для Render
    await start_web_server()

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
