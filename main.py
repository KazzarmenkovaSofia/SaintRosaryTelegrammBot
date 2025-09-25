import os
import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiohttp import web
import rosario  # твой модуль с молитвами
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

# ===== Логирование =====
logging.basicConfig(level=logging.INFO)

# ===== Токены =====
BOT_TOKEN = "7247038755:AAE2GEPMR-XDaoFoTIZWidwH-ZQfD7g36pE"
TOGETHER_API_KEY = "09392b9d19cab71d0a2300b1df5ca81df0b78a1f97457528d4ef53f5e25c60c1"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")

# ===== Переменные состояния =====
user_state = {}
user_data = {}
language = "español"
current_message = 0
cycleOraciones = False
cycle = 0
mystery = 0

# ===== Клавиатуры =====
def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Español", callback_data="lang:es"),
         InlineKeyboardButton(text="Latin", callback_data="lang:la")]
    ])

pray_button = InlineKeyboardButton(text='🙏Empezar a rezar el rosario🙏', callback_data='pray_pressed')
pray_keyboard = InlineKeyboardMarkup(inline_keyboard=[[pray_button]])

continuar_button = InlineKeyboardButton(text='▶️▶️', callback_data='continuar_pressed')
continuar_keyboard = InlineKeyboardMarkup(inline_keyboard=[[continuar_button]])

# ===== Обработчики команд =====
@dp.message(F.command == "start")
async def start_command(message: types.Message):
    await message.answer("¡Bienvenido! Selecciona tu idioma:", reply_markup=get_language_keyboard())

@dp.callback_query(F.data.startswith("lang:"))
async def language_selected(callback: types.CallbackQuery):
    global language
    lang_code = callback.data.split(":")[1]
    language = "español" if lang_code == "es" else "latin"
    await callback.message.edit_text(f"Has seleccionado: {'Español' if language=='español' else 'Latin'}", reply_markup=pray_keyboard)
    await callback.answer()

# ===== Функции для новостей и генерации молитв =====
def get_news_links():
    current_date = datetime.now()
    formatted_date = current_date.strftime('%Y-%m')
    url = 'https://www.vaticannews.va/ru.html'
    response = requests.get(url)
    response.encoding = 'utf-8'

    links = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('a', href=True, title=True)
        for article in articles:
            link = f"https://www.vaticannews.va{article['href']}"
            if f'/ru/pope/news/{formatted_date}' in link and link not in links:
                links.append(link)
    return links

def generate_prayers(links):
    joined_links = "\n\n".join(links)
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[{
            "role": "user",
            "content": (
                "Read the following news articles and create prayer intentions for the Rosary in Spanish:\n\n"
                f"{joined_links}\n\nWrite a clean text with 'Amén' at the end."
            )
        }]
    )
    return response.choices[0].message.content.strip()

# ===== Пример обработчика молитвы =====
@dp.callback_query(F.data == "pray_pressed")
async def start_prayer(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    # Определяем тип таинства
    wday = datetime.now().weekday()
    if wday == 0 or wday == 5:
        m_type = 'gaudiosa'
    elif wday == 3:
        m_type = 'luminosa'
    elif wday == 1 or wday == 4:
        m_type = 'dolorosa'
    else:
        m_type = 'gloriosa'

    # Список сообщений
    message_list = [
        rosario.mysteries[m_type][language],
        rosario.paterNoster[language],
        rosario.gloria[language],
        rosario.oratioFatimae[language],
        rosario.MariaMadreDeGracia[language]
    ]

    # Сохраняем состояние пользователя
    user_state[user_id] = {
        'in_pray': True,
        'pray_done': False,
        'message_list': message_list,
        'current_message': 0
    }

    photo = FSInputFile("persignum.jpg")
    await callback.message.answer_photo(photo, caption=f'{rosario.perSigniumcrucis[language]}', reply_markup=continuar_keyboard)
    await callback.answer()

# ===== Продолжение молитвы =====
@dp.callback_query(F.data == "continuar_pressed")
async def continue_prayer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = user_state.get(user_id)
    if not state or not state['in_pray']:
        await callback.message.answer("Para comenzar a orar ingrese el comando /start")
        return

    messages = state['message_list']
    idx = state['current_message']

    if idx < len(messages):
        await callback.message.answer(messages[idx], reply_markup=continuar_keyboard)
        state['current_message'] += 1
    else:
        await callback.message.answer("🙏 La oración ha terminado 🙏")
        state['in_pray'] = False
        state['pray_done'] = True

    await callback.answer()

# ===== Webhook =====
async def webhook_handler(request):
    data = await request.json()
    update = dp.update_factory.update_from_raw(data)
    await dp.feed_update(update)
    return web.Response(text="OK")

async def start_web_app():
    app = web.Application()
    async def handle_root(request):
        return web.Response(text="Bot is running 🙏")
    app.router.add_get("/", handle_root)
    app.router.add_post(f"/webhook/{BOT_TOKEN}", webhook_handler)

    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Webhook server running on port {port}")

    while True:
        await asyncio.sleep(3600)

# ===== Настройка webhook =====
async def on_startup():
    await bot.set_my_commands([BotCommand(command="start", description="Iniciar el bot")])
    webhook_url = f"https://saintrosarytelegrammbot-1.onrender.com/webhook/{BOT_TOKEN}"
    await bot.set_webhook(webhook_url)
    logging.info(f"Webhook set: {webhook_url}")

# ===== Запуск =====
if __name__ == "__main__":
    asyncio.run(on_startup())
    asyncio.run(start_web_app())
