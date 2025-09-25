import logging
import requests
import locale
from datetime import datetime
import rosario
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.enums import ParseMode
import asyncio
from aiohttp import web
from openai import OpenAI
import os

# --- Настройки ---
BOT_TOKEN = '7247038755:AAE2GEPMR-XDaoFoTIZWidwH-ZQfD7g36pE'
TOGETHER_API_KEY = "09392b9d19cab71d0a2300b1df5ca81df0b78a1f97457528d4ef53f5e25c60c1"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")

logging.basicConfig(level=logging.INFO)

# --- Данные пользователей ---
user_data = {}
user_state = {}
user = {'in_pray': False, 'pray_done': False}

# --- Web сервер для Render ---
async def handle(request):
    return web.Response(text="Rosary bot is running 🙏")

app = web.Application()
app.router.add_get("/", handle)

# --- Язык по умолчанию ---
language = locale.getlocale()[0].partition('_')[0].lower()
language = 'español'  # фиксируем для удобства

# --- Инлайн-клавиатуры (пример, твои уже есть) ---
def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Español", callback_data="lang:es"),
         InlineKeyboardButton(text="Latin", callback_data="lang:la")]
    ])

pray_keyboard = InlineKeybo_
