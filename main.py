import logging
import os
import asyncio
from datetime import datetime
import locale
import requests
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import BotCommand, Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.enums import ParseMode

from openai import OpenAI
from aiohttp import web

import rosario  # твой модуль с молитвами

# ================== Настройки ==================
BOT_TOKEN = '7247038755:AAE2GEPMR-XDaoFoTIZWidwH-ZQfD7g36pE'

TOGETHER_API_KEY = "09392b9d19cab71d0a2300b1df5ca81df0b78a1f97457528d4ef53f5e25c60c1"

client = OpenAI(
    api_key=TOGETHER_API_KEY,
    base_url="https://api.together.xyz/v1"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# ================== Глобальные переменные ==================
user_data = {}
user_state = {}
user_choices = {}
current_message = 0
cycleOraciones = False
cycle = 0
mystery = 0
aveMtimes = 0
language = 'español'

# ================== Клавиатуры ==================
def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Español", callback_data="lang:es"),
         InlineKeyboardButton(text="Latin", callback_data="lang:la")]
    ])

continuar_button = InlineKeyboardButton(text='▶️▶️', callback_data='continuar_pressed')
keyboard = InlineKeyboardMarkup(inline_keyboard=[[continuar_button]])

peticiones_button = InlineKeyboardButton(text='Peticiones', callback_data='peticiones_pressed')
PeticionesDelDia = InlineKeyboardButton(text='Peticiones Del Dia', callback_data='peticiones_dia')
p_keyboard = InlineKeyboardMarkup(inline_keyboard=[[peticiones_button]])
peticiones_keyboard = InlineKeyboardMarkup(inline_keyboard=[[PeticionesDelDia], [continuar_button]])
peticiones_dia_keyboard = InlineKeyboardMarkup(inline_keyboard=[[continuar_button]])

aveMaria_button = InlineKeyboardButton(text='▶️▶️', callback_data='start_primera_ave')
ave_keyboard = InlineKeyboardMarkup(inline_keyboard=[[aveMaria_button]])
latin_keyboard = InlineKeyboardMarkup(inline_keyboard=[[continuar_button]])

letanias_button = InlineKeyboardButton(text='Letanías de la virgen', callback_data='let_pressed')
bajo_button = InlineKeyboardButton(text='▶️▶️', callback_data='bajo_pressed')
finish_keyboard = InlineKeyboardMarkup(inline_keyboard=[[letanias_button],[bajo_button]])

let_cycle_answer_next = InlineKeyboardButton(text=f'⏭️', callback_data='let_cycle_answer_pressed_next')
let_cycle_answer_back = InlineKeyboardButton(text=f'⏮️', callback_data='let_cycle_answer_pressed_back')
let_cycle_keyboard_beginning = InlineKeyboardMarkup(inline_keyboard=[[let_cycle_answer_next]])
let_cycle_keyboard = InlineKeyboardMarkup(inline_keyboard=[[let_cycle_answer_back,let_cycle_answer_next]])
let_fin = InlineKeyboardButton(text='▶️▶️', callback_data='let_fin_pressed')
let_cycle_keyboard_last = InlineKeyboardMarkup(inline_keyboard=[[let_cycle_answer_back, let_fin]])

ruega_button = InlineKeyboardButton(text='▶️▶️', callback_data='ruega_pressed')
ruega_keyboard = InlineKeyboardMarkup(inline_keyboard=[[ruega_button]])

pray_button = InlineKeyboardButton(text='🙏Empezar a rezar el rosario🙏', callback_data='pray_pressed')
pray_keyboard = InlineKeyboardMarkup(inline_keyboard=[[pray_button]])

# ================== Функции ==================
def get_mystery_type():
    wday = datetime.now().weekday()
    if wday in [0,5]:
        return 'gaudiosa'
    elif wday == 3:
        return 'luminosa'
    elif wday in [1,4]:
        return 'dolorosa'
    else:
        return 'gloriosa'

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
                "Read the following news articles and write one or more prayer intentions in Spanish, finish with 'Amén'.\n\n"
                f"{joined_links}"
            )
        }]
    )
    return response.choices[0].message.content.strip()

async def set_main_menu(bot: Bot):
    main_menu_commands = [BotCommand(command='/start', description='🙏Empezar')]
    await bot.set_my_commands(main_menu_commands)

# ================== Хэндлеры ==================
@dp.message(Command(commands=["start"]))
async def start_command(message: Message):
    selected = await message.answer(f'{rosario.textStart[language]}', reply_markup=get_language_keyboard())
    user_data[message.from_user.id] = selected.message_id

@dp.callback_query(F.data.startswith("lang:"))
async def language_callback(callback: CallbackQuery):
    global language
    lang_code = callback.data.split(":")[1]
    language = "español" if lang_code == "es" else "latin"
    user_id = callback.from_user.id
    selected_msg_id = user_data.get(user_id)
    if selected_msg_id:
        await bot.edit_message_text(chat_id=callback.message.chat.id,
                                    message_id=selected_msg_id,
                                    text=f"Escogiste el idioma para orar: {language}",
                                    reply_markup=pray_keyboard)
    await callback.answer()

# ================== Логика молитвы ==================
@dp.callback_query(F.data == 'pray_pressed')
async def start_prayer(callback: CallbackQuery):
    global m_type, message_list, orarCombiar, oracionVercion
    user_id = callback.from_user.id
    m_type = get_mystery_type()
    messages = [
        rosario.mysteries[m_type][language],
        rosario.paterNoster[language],
        rosario.gloria[language],
        rosario.oratioFatimae[language],
        rosario.MariaMadreDeGracia[language]
    ]
    user_state[user_id] = {
        'in_pray': True,
        'message_list': messages,
        'current_message': 0,
        'cycle': 0
    }
    photo = FSInputFile("persignum.jpg")
    await callback.message.answer_photo(photo, caption=f'{rosario.perSigniumcrucis[language]}', reply_markup=keyboard)
    await callback.answer()

# ================== Peticiones ==================
@dp.callback_query(F.data == 'peticiones_pressed')
async def peticiones(callback: CallbackQuery):
    global cycleOraciones
    await callback.message.answer(text=f'Pensale de tus peticiones:\n\n🙏 Se pronuncia la intención en la que se recita el Rosario.', reply_markup=peticiones_keyboard)
    cycleOraciones = True

@dp.callback_query(F.data == 'peticiones_dia')
async def peticiones_dia(callback: CallbackQuery):
    await callback.message.edit_text(text=f'⏳ Preparamos peticiones relevantes ⌛', reply_markup=peticiones_dia_keyboard)
    links = get_news_links()
    if not links:
        await callback.message.edit_text("⚠️ Не удалось найти свежих новостей.", reply_markup=peticiones_dia_keyboard)
        return
    try:
        prayers = generate_prayers(links)
        await callback.message.edit_text(f"🙏 Peticiones:\n\n{prayers}", reply_markup=peticiones_dia_keyboard, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Ошибка при генерации молитвы: {e}")
        await callback.message.edit_text("🚫 Произошла ошибка при генерации молитвы.", reply_markup=peticiones_dia_keyboard)

# ================== Letanías ==================
@dp.callback_query(F.data == 'let_pressed')
async def letanias_start(callback: CallbackQuery):
    global current_message
    current_message = 0
    await callback.message.answer(text=f'{rosario.letaniasDeLaVirgenMessage[current_message]}', parse_mode='Markdown', reply_markup=let_cycle_keyboard_beginning)

@dp.callback_query(F.data == 'let_cycle_answer_pressed_next')
async def let_next(callback: CallbackQuery):
    global current_message
    current_message += 1
    if current_message >= len(rosario.letaniasDeLaVirgenMessage):
        current_message = len(rosario.letaniasDeLaVirgenMessage) - 1
    if current_message == len(rosario.letaniasDeLaVirgenMessage) - 1:
        reply_markup = let_cycle_keyboard_last
    elif current_message == 0:
        reply_markup = let_cycle_keyboard_beginning
    else:
        reply_markup = let_cycle_keyboard
    await callback.message.edit_text(text=f'{rosario.letaniasDeLaVirgenMessage[current_message]}', parse_mode='Markdown', reply_markup=reply_markup)

@dp.callback_query(F.data == 'let_cycle_answer_pressed_back')
async def let_back(callback: CallbackQuery):
    global current_message
    current_message -= 1
    if current_message < 0:
        current_message = 0
    if current_message == 0:
        reply_markup = let_cycle_keyboard_beginning
    elif current_message == len(rosario.letaniasDeLaVirgenMessage) - 1:
        reply_markup = let_cycle_keyboard_last
    else:
        reply_markup = let_cycle_keyboard
    await callback.message.edit_text(text=f'{rosario.letaniasDeLaVirgenMessage[current_message]}', parse_mode='Markdown', reply_markup=reply_markup)

@dp.callback_query(F.data == 'let_fin_pressed')
async def let_fin(callback: CallbackQuery):
    await callback.message.edit_text(text=f'{rosario.letaniasDeLaVirgenFin}', reply_markup=pray_keyboard)

# ================== Webhook ==================
async def handle_webhook(request: web.Request):
    update = await request.json()
    update_obj = types.Update.to_object(update)
    await dp.process_update(update_obj)
    return web.Response()

async def on_startup(app):
    await set_main_menu(bot)
    await bot.delete_webhook()
    print("Webhook удалён, бот готов к приёму сообщений")

# ================== Запуск ==================
if __name__ == "__main__":
    app = web.Application()
    app.router.add_post(f"/{BOT_TOKEN}", handle_webhook)
    app.on_startup.append(on_startup)

    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)


