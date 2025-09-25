import logging
import requests
import locale
from datetime import datetime
import rosario
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.filters import Command
from openai import OpenAI
import os
import asyncio
from aiohttp import web

# ========================== Настройки ==========================
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

language = locale.getlocale()[0].partition('_')[0].lower()
language = 'español'
user = {'in_pray': False, 'pray_done': False}
cycleOraciones = False
current_message = 0
cycle = 0
mystery = 0
aveMtimes = 0
message_list = []
oracionVercion = ''
m_type = ''
# ================================================================

# ========================== Клавиатуры ==========================
def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Español", callback_data="lang:es"),
         InlineKeyboardButton(text="Latin", callback_data="lang:la")]
    ])

continuar = InlineKeyboardButton(text='▶️▶️', callback_data='continuar_pressed')
keyboard = InlineKeyboardMarkup(inline_keyboard=[[continuar]])

pray = InlineKeyboardButton(text='🙏Empezar a rezar el rosario🙏', callback_data='pray_pressed')
pray_keyboard = InlineKeyboardMarkup(inline_keyboard=[[pray]])

# ... (Добавь здесь остальные клавиатуры точно как у тебя было)

# ========================== AI ==========================
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

# ========================== Новости ==========================
def get_news_links():
    current_date = datetime.now()
    formatted_date = current_date.strftime('%Y-%m')
    url = 'https://www.vaticannews.va/ru.html'
    response = requests.get(url)
    response.encoding = 'utf-8'
    links = []
    if response.status_code == 200:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('a', href=True, title=True)
        for article in articles:
            link = f"https://www.vaticannews.va{article['href']}"
            if f'/ru/pope/news/{formatted_date}' in link and link not in links:
                links.append(link)
    return links

# ========================== Меню ==========================
async def set_main_menu(bot: Bot):
    main_menu_commands = [BotCommand(command='/start', description='🙏Empezar')]
    await bot.set_my_commands(main_menu_commands)

# ========================== Тип таинств ==========================
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

# ========================== Хэндлеры ==========================
@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message):
    await message.answer(f'{rosario.textStart[language]}', reply_markup=get_language_keyboard())
    selected = await message.answer("Aún no has seleccionado un idioma.")
    user_data[message.from_user.id] = selected.message_id

@dp.callback_query(F.data.startswith("lang:"))
async def language_callback(callback: CallbackQuery):
    global language
    lang_code = callback.data.split(":")[1]
    language = "español" if lang_code == "es" else "latin"
    user_id = callback.from_user.id
    selected_msg_id = user_data.get(user_id)
    if selected_msg_id:
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=selected_msg_id,
            text=f"Escogiste el idioma para orar:  {'Español' if language=='español' else 'Latin'}",
            reply_markup=pray_keyboard
        )
    await callback.answer()

# ========================== Фоновый сервер ==========================
async def handle(request):
    return web.Response(text="Rosary bot is running 🙏")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# ========================== Main ==========================
async def main():
    await set_main_menu(bot)
    asyncio.create_task(dp.start_polling(bot))
    await start_web_server()
    print("Bot is running...")
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
