import logging
import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiohttp import web
import rosario
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# ---------- Настройки ----------
BOT_TOKEN = '7247038755:AAE2GEPMR-XDaoFoTIZWidwH-ZQfD7g36pE'
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://YOUR_APP_NAME.onrender.com{WEBHOOK_PATH}"  # <== Заменить на URL вашего приложения Render
PORT = int(os.getenv("PORT", 8080))
TOGETHER_API_KEY = "09392b9d19cab71d0a2300b1df5ca81df0b78a1f97457528d4ef53f5e25c60c1"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = OpenAI(
    api_key=TOGETHER_API_KEY,
    base_url="https://api.together.xyz/v1"
)

# ---------- User state ----------
user_data = {}
user_state = {}
user_choices = {}

language = "español"
cycleOraciones = False
current_message = 0
cycle = 0
mystery = 0
aveMtimes = 0
message_list = []

# ---------- Inline keyboards ----------
def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Español", callback_data="lang:es"),
         InlineKeyboardButton(text="Latin", callback_data="lang:la")]
    ])

# Health check
async def handle(request):
    return web.Response(text="Rosary bot is running 🙏")

# ---------- AI and news helpers ----------
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
                "Read the following news articles, excluding irrelevant events from the perspective of Catholicism. "
                "Only consider news related to faith, spirituality, human rights, social issues, peace, health, and other important topics from a moral standpoint. "
                "Based on these news items, formulate one or more prayer intentions for the Holy Rosary. "
                "Each prayer intention should be a brief, complete sentence or a paragraph, in the form of a prayer. "
                "Avoid breaking the text into separate words or elements. "
                "The prayer should express a desire for peace, blessings, and help for those in need. "
                "Provide the result in a clean, readable text format with clear prayer intentions:\n\n"
                f"{joined_links}\n\n"
                "Write your result en spanish without numeration and finish with 'Amén'."
            )
        }]
    )
    return response.choices[0].message.content.strip()

# ---------- Commands ----------
async def set_main_menu(bot: Bot):
    main_menu_commands = [BotCommand(command='/start', description='🙏Empezar')]
    await bot.set_my_commands(main_menu_commands)

@dp.message(F.text.startswith("/start"))
async def process_start_command(message: Message):
    await message.answer(f'{rosario.textStart[language]}', reply_markup=get_language_keyboard())
    user_data[message.from_user.id] = message.message_id

@dp.callback_query(F.data.startswith("lang:"))
async def language_callback(callback: CallbackQuery):
    global language
    lang_code = callback.data.split(":")[1]
    language = "español" if lang_code == "es" else "latin"
    await callback.message.edit_text(f"Escogiste el idioma para orar: {language}")
    await callback.answer()

# ---------- Webhook ----------
async def webhook_handler(request):
    data = await request.json()
    update = dp.update_factory.update_from_raw(data)
    await dp.feed_update(update)
    return web.Response(text="OK")

# ---------- Start web server ----------
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Webhook server started on port {PORT}")

# ---------- Main ----------
async def main():
    await set_main_menu(bot)
    # Устанавливаем webhook
    await bot.set_webhook(WEBHOOK_URL)
    await start_web_server()
    # Бесконечный цикл, чтобы процесс не завершался
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
