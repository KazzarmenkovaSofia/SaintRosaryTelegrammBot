import logging
import requests
import locale
import time
from datetime import datetime
import rosario
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand
from aiogram.filters import Command
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message)
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
from bs4 import BeautifulSoup
from aiogram.enums import ParseMode
from aiogram.filters import Command
from openai import OpenAI
import os
from aiogram import Bot, types
from aiogram.types import FSInputFile
from aiohttp import web

# Вместо BOT TOKEN HERE нужно вставить токен вашего бота, полученный у @BotFather
BOT_TOKEN = '7247038755:AAE2GEPMR-XDaoFoTIZWidwH-ZQfD7g36pE'

TOGETHER_API_KEY = "09392b9d19cab71d0a2300b1df5ca81df0b78a1f97457528d4ef53f5e25c60c1"

client = OpenAI(
    api_key=TOGETHER_API_KEY,
    base_url="https://api.together.xyz/v1"
)
# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}
# Создаем объект выбора языка

chosenLanguage = False
# Логирование ошибок
logging.basicConfig(level=logging.INFO)

# Словарь для хранения состояния пользователя
user_choices = {}
user_state = {}

# Создаем объекты инлайн-кнопок
continuar = InlineKeyboardButton(
    text='▶️▶️',
    callback_data='continuar_pressed'
)

# Создаем объект инлайн-клавиатуры
keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[continuar]])

checkboxes_state = {}
params = {}

# Создаем объекты инлайн-кнопок
peticiones = InlineKeyboardButton(
    text='Peticiones',
    callback_data='peticiones_pressed'
)

PeticionesDelDia = InlineKeyboardButton(
    text='Peticiones Del Dia',
    callback_data='peticiones_dia'
)


# Создаем объект инлайн-клавиатуры
p_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[peticiones]])

# Создаем объект инлайн-клавиатуры
peticiones_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[PeticionesDelDia], [continuar]])

peticiones_dia_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[continuar]])

# Создаем объекты инлайн-кнопок для Отче Наш
aveMaria = InlineKeyboardButton(
    text='▶️▶️',
    callback_data='start_primera_ave'
)



# Создаем объект инлайн-клавиатуры
porSignum_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[continuar]])

# Создаем объект инлайн-клавиатуры
ave_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[aveMaria]])

latin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[continuar]])

# Создаем объекты инлайн-кнопок
letanias = InlineKeyboardButton(
    text='Letanías de la virgen',
    callback_data='let_pressed'
)

bajo = InlineKeyboardButton(
    text='▶️▶️',
    callback_data='bajo_pressed'
)

# Создаем объект инлайн-клавиатуры
finish_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[letanias],
                     [bajo]])

# Создаем объекты инлайн-кнопок
let_cycle_answer_next = InlineKeyboardButton(
    text=f'⏭️',
    callback_data='let_cycle_answer_pressed_next'
)

# Создаем объекты инлайн-кнопок
let_cycle_answer_back = InlineKeyboardButton(
    text=f'⏮️',
    callback_data='let_cycle_answer_pressed_back'
)

# Создаем объект инлайн-клавиатуры
let_cycle_keyboard_beginning = InlineKeyboardMarkup(
    inline_keyboard=[[let_cycle_answer_next]])

# Создаем объект инлайн-клавиатуры
let_cycle_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[let_cycle_answer_back,let_cycle_answer_next]])


# Функция для получения инлайн клавиатуры
def get_inline_keyboard(button_text: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data='let_cycle_answer_pressed')]
        ]
    )
# Создаем объекты инлайн-кнопок
let_fin = InlineKeyboardButton(
    text='▶️▶️',
    callback_data='let_fin_pressed'
)

# Создаем объект инлайн-клавиатуры
let_fin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[let_fin]])


# Создаем объект инлайн-клавиатуры
let_cycle_keyboard_last = InlineKeyboardMarkup(
    inline_keyboard=[[let_cycle_answer_back,let_fin]])

# Создаем объекты инлайн-кнопок
ruega = InlineKeyboardButton(
    text='▶️▶️',
    callback_data='ruega_pressed'
)

# Создаем объект инлайн-клавиатуры
ruega_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[ruega]])

def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Español", callback_data="lang:es"),
         InlineKeyboardButton(text="Latin", callback_data="lang:la")]
    ])
# Создаем объекты инлайн-кнопок
pray = InlineKeyboardButton(
    text='🙏Empezar a rezar el rosario🙏',
    callback_data='pray_pressed'
)


# Создаем объект инлайн-клавиатуры
pray_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[pray]])


# Получение новостей
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



# Вызов AI
def generate_prayers(links):
    joined_links = "\n\n".join(links)

    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[
            {
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
            }
        ]
    )

    return response.choices[0].message.content.strip()

# Создаем асинхронную функцию
async def set_main_menu(bot: Bot):

    # Создаем список с командами и их описанием для кнопки menu
    main_menu_commands = [
        BotCommand(command='/start',
                   description='🙏Empezar')
    ]

    await bot.set_my_commands(main_menu_commands)


# Узнаем язык устройства
language = locale.getlocale()[0].partition('_')[0].lower()

language = 'español'

#Указываем информацию о пользователе
user = {
    'in_pray': False,
    'pray_done': False
}

cycleOraciones = False

current_message = 0
cycle = 0
mystery = 0
answerNumber = 0
aveMtimes = 0
aveVercion = ''
oracionVercion = ''
m_type = ''
row = 0
message_list = []
beforeCycleList = [
    rosario.venEspirituSanto[language],
    rosario.credo[language]
]
orarCombiar = {
    'perSigniumcrucis': False,
    'padre': False
}

CallbackTypeAve = ''

keyboard_letania = ''


# Этот хэндлер будет срабатывать на команду "/start"
@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message):
    await message.answer(f'{rosario.textStart[language]}', reply_markup=get_language_keyboard())
    selected = await message.answer("Aún no has seleccionado un idioma.")
    user_data[message.from_user.id] = selected.message_id
    user_id = message.from_user.id


@dp.callback_query(F.data.startswith("lang:"))
async def language_callback(callback: CallbackQuery):
    global language
    lang_code = callback.data.split(":")[1]
    lang_name = "Español" if lang_code == "es" else "Latin"
    language = "español" if lang_code == "es" else "latin"

    user_id = callback.from_user.id
    selected_msg_id = user_data.get(user_id)

    if selected_msg_id:
        try:
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=selected_msg_id,
                text=f"Escogiste el idioma para orar:  {lang_name}",
                reply_markup = pray_keyboard
            )
        except Exception as e:
            logging.error(f"Ошибка при редактировании: {e}")

    await callback.answer()

# Этот хэндлер будет срабатывать на команду "/pray"
@dp.callback_query(F.data == 'pray_pressed')
async def answer(callback: CallbackQuery):
    current_date = datetime.now()
    wday = current_date.weekday()
    global m_type, message_list, orarCombiar, oracionVercion
    
    if wday == 0 or wday == 5:
        m_type = 'gaudiosa'
    elif wday == 3:
        m_type = 'luminosa'
    elif wday == 1 or wday == 4:
        m_type = 'dolorosa'
    else:
        m_type = 'gloriosa'

    message_list = [
        rosario.mysteries[m_type][language],
        rosario.paterNoster[language],
        rosario.gloria[language],
        rosario.oratioFatimae[language],
        rosario.MariaMadreDeGracia[language]
    ]
    if not user['in_pray']:
        user['in_pray'] = True
        orarCombiar['perSigniumcrucis'] = True
        oracionVercion = "original"

        # Send image with prayer text as caption
        photo = FSInputFile("persignum.jpg")
        await callback.message.answer_photo(photo, caption=f'{rosario.perSigniumcrucis[language]}', reply_markup=porSignum_keyboard)
    else:
        await callback.message.answer(text=f'El comando de oración ya está en ejecución. Para continuar, haga clic en "Continuar"', reply_markup=keyboard)

@dp.callback_query(F.data == 'continuar_pressed')
async def answer(callback: CallbackQuery):
    global rosario, mystery, message_list, user, orarCombiar, oracionVercion, cycleOraciones, cycle, current_message, user_choices, user_state, aveMtimes
    if user['in_pray'] and not cycleOraciones:
        if current_message == 0:
            await callback.message.answer(text=f'{rosario.venEspirituSanto[language]}', reply_markup=keyboard)
            current_message += 1
        elif current_message == 1:
            await callback.message.answer(text=f'{rosario.credo[language]}', reply_markup=keyboard)
            current_message += 1
        elif current_message == 2:
            await callback.message.answer(text=f'{rosario.actoDeContricion[language]}', reply_markup=p_keyboard)
            current_message = 0
    if user['in_pray'] and cycleOraciones:
        if cycle == 0:
            if current_message == 0:
                orarCombiar['perSigniumcrucis'] = False
                orarCombiar['padre'] = True
                oracionVercion = "original"
                current_message += 1
                await callback.message.answer(text=f'{message_list[current_message]}', reply_markup=ave_keyboard)
                current_message = 0
                cycle += 1
        elif cycle == 5 and current_message >= len(message_list):
            await callback.message.answer(text=f'{rosario.salveRegina[language]}', reply_markup=finish_keyboard)
            await callback.answer(text='Continúe con la letanías o la oración final')
            user['in_pray'] = False
            cycleOraciones = False
            current_message = 0
            cycle = 0
            mystery = 0
        elif current_message >= len(message_list):
            cycle += 1
            current_message = 0
            await callback.message.answer(text=f'{message_list[current_message][mystery]}', reply_markup=keyboard)
            current_message += 1
            mystery += 1
            user_choices = {}
            user_state = {}
            aveMtimes += 1
        elif current_message == 0:
            await callback.message.answer(text=f'{message_list[current_message][mystery]}', reply_markup=keyboard)
            current_message += 1
            mystery += 1
            user_choices = {}
            user_state = {}
            aveMtimes += 1
        elif current_message == 1:
            await callback.message.answer(text=f'{message_list[current_message]}', reply_markup=ave_keyboard)
            current_message += 1
        elif current_message == 2:
            await callback.message.answer(text=f'{message_list[current_message]}', reply_markup=latin_keyboard)
            current_message += 1
        else:
            await callback.message.answer(text=f'{message_list[current_message]}', reply_markup=keyboard)
            current_message += 1
    elif not user['in_pray']:
        await callback.message.answer(text=f'Para comenzar a orar ingrese el comando /pray')


@dp.callback_query(F.data == 'peticiones_pressed')
async def answer(callback: CallbackQuery):
    global cycleOraciones
    await callback.message.answer(text=f'Pensale de tus peticiones:\n\n🙏 Se pronuncia la intención en la que se recita el Rosario. \nPuedes decir la oración inicial:\n\n“¡Señor nuestro Jesucristo!\nDedico / Te dedicamos / A Ti este santo Rosario para gloria de Tu nombre,\nen honor de Vuestra Madre Purísima y por la salvación de las almas" 🙏', reply_markup=peticiones_keyboard)
    cycleOraciones = True


@dp.callback_query(F.data == 'peticiones_dia')
async def send_prayers(callback: CallbackQuery):
    await callback.message.edit_text(text=f'⏳ Preparamos peticiones relevantes ⌛', reply_markup=peticiones_dia_keyboard)
    links = get_news_links()

    if not links:
        await callback.message.edit_text("⚠️ Не удалось найти свежих новостей для анализа.", reply_markup=peticiones_dia_keyboard)
        return

    try:
        prayers = generate_prayers(links)
        await callback.message.edit_text(f"🙏 Peticiones:\n\n{prayers}", reply_markup=peticiones_dia_keyboard, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Ошибка при обращении к AI: {e}")
        await callback.message.edit_text("🚫 Произошла ошибка при генерации молитвы. Попробуй позже.", reply_markup=peticiones_dia_keyboard)



# Обработчик для изменения языка
@dp.callback_query(F.data == "combiar_vercion")
async def ask_question(query):
    global oracionVercion, orarCombiar, rosario, mystery, message_list, user, cycleOraciones, cycle, current_message
    if oracionVercion == "" or oracionVercion == "original":
        if orarCombiar['perSigniumcrucis']:
            await query.message.edit_caption(caption=f'{rosario.perSigniumcrucis['latin']}', parse_mode="HTML", reply_markup=porSignum_keyboard)
        elif orarCombiar['padre']:
            await query.message.edit_text(text=f'{rosario.paterNoster['latin']}', reply_markup=ave_keyboard)
        else:
            await query.message.edit_text(text=f'{rosario.gloria['latin']}', reply_markup=latin_keyboard)

        oracionVercion = "latin"
    else:
        if orarCombiar['perSigniumcrucis']:
            await query.message.edit_caption(caption=f'{rosario.perSigniumcrucis[language]}', parse_mode="HTML", reply_markup=porSignum_keyboard)
        elif orarCombiar['padre']:
            await query.message.edit_text(text=f'{rosario.paterNoster[language]}', reply_markup=ave_keyboard)
        else:
            await query.message.edit_text(text=f'{rosario.gloria[language]}', reply_markup=latin_keyboard)

        oracionVercion = "original"

    await query.answer()

# Обработчик для начала опроса
@dp.callback_query(F.data == "start_primera_ave")
async def ask_question(query):
    global aveMtimes, aveVercion, row
    aveVercion = "original"
    user_state[query.from_user.id] = 4  # Переход к вопросу с цветами
    builder = InlineKeyboardBuilder()
    if aveMtimes == 0:
        colors = ["1", "2", "3"]
        row = 3
    else:
        colors = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        row = 3

    # Разделяем кнопки на 2 ряда
    row_size = row  # Размер каждого ряда
    for i in range(0, len(colors), row_size):
        row_colors = colors[i:i + row_size]
        buttons = [InlineKeyboardButton(text=f"{color} {'🙏' if color in user_choices.get(query.from_user.id, []) else ''}", callback_data=f"color_{color}") for color in row_colors]
        builder.row(*buttons)  # Добавляем ряд из кнопок


    markup = builder.as_markup()

    if aveMtimes == 0:
        await query.message.answer(text=f'{rosario.aveMaria[language]}\nRepetir 3 veces', reply_markup=markup)
    else:
        await query.message.answer(text=f'{rosario.aveMaria[language]}\nRepetir 10 veces', reply_markup=markup)

    await query.answer()


# Обработчик выбора цвета
@dp.callback_query(F.data.startswith("color_"))
async def handle_color_choice(query):
    global cycle, row, CallbackTypeAve
    color = int(query.data.split("_")[1])  # Преобразуем номер цвета в целое число
    user_id = query.from_user.id

    if user_id not in user_choices:
        user_choices[user_id] = []

    # Проверка, что выбраны все предыдущие цвета
    for i in range(1, color):
        if str(i) not in user_choices[user_id]:
            await query.answer(text=f"Has orado {i-1} veces. Ahora usted elige el número {color}. Por favor, elija el número correcto ({i}).", show_alert=True)
            return

    # Добавляем или удаляем цвет из списка выбранных
    if str(color) in user_choices[user_id]:
        user_choices[user_id].remove(str(color))
    else:
        user_choices[user_id].append(str(color))

    builder = InlineKeyboardBuilder()

    if aveMtimes == 0:
        colors = ["1", "2", "3"]
        row = 3
    else:
        colors = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        row = 3

    # Разделяем кнопки на 2 ряда
    row_size = row  # Размер каждого ряда
    for i in range(0, len(colors), row_size):
        row_colors = colors[i:i + row_size]
        buttons = [InlineKeyboardButton(text=f"{color} {'🙏' if color in user_choices[user_id] else ''}", callback_data=f"color_{color}") for color in row_colors]
        builder.row(*buttons)  # Добавляем ряд из кнопок

    # Указываем коллбэк для кнопки "▶️▶️"
    if aveMtimes == 0:
        if "3" in user_choices[user_id]:
            CallbackTypeAve = "continuar_pressed"
        else:
            CallbackTypeAve = "ave_continuar_cancelar"
    else:
        if "10" in user_choices[user_id]:
            CallbackTypeAve = "continuar_pressed"
        else:
            CallbackTypeAve = "ave_continuar_cancelar"

    # Добавляем кнопку "▶️▶️"
    if aveMtimes == 0:
        if "2" in user_choices[user_id]:
            builder.add(InlineKeyboardButton(text="▶️▶️", callback_data=CallbackTypeAve))
    else:
        if "9" in user_choices[user_id]:
            builder.add(InlineKeyboardButton(text="▶️▶️", callback_data=CallbackTypeAve))

    markup = builder.as_markup()


    # Обновляем сообщение с новым состоянием кнопок
    await query.message.edit_reply_markup(reply_markup=markup)
    await query.answer()

@dp.callback_query(F.data == 'ave_continuar_cancelar')
async def answer(callback: CallbackQuery):
    await callback.answer(text='Terminale todas las veces y luego continuemos')


@dp.callback_query(F.data == 'bajo_pressed')
async def answer(callback: CallbackQuery):
    global cycleOraciones
    await callback.message.answer(text=f'{rosario.bajoTuAmparo[language]}', reply_markup=ruega_keyboard)
    cycleOraciones = False

@dp.callback_query(F.data == 'let_pressed')
async def answer(callback: CallbackQuery):
    global current_message
    await callback.message.answer(text=f'{rosario.letaniasDeLaVirgenMessage[0]}', parse_mode='Markdown', reply_markup=let_cycle_keyboard_beginning)


@dp.callback_query(F.data == 'let_cycle_answer_pressed_next')
async def answer(callback: CallbackQuery):
    global current_message
    current_message += 1

    if current_message == 0:
        await callback.message.edit_text(
            text=f'{rosario.letaniasDeLaVirgenMessage[current_message]}',
            parse_mode='Markdown',
            reply_markup=let_cycle_keyboard_beginning
        )
    elif current_message == len(rosario.letaniasDeLaVirgenMessage) - 1:
        await callback.message.edit_text(
            text=f'{rosario.letaniasDeLaVirgenMessage[current_message]}',
            parse_mode='Markdown',
            reply_markup=let_cycle_keyboard_last
        )
    elif current_message > len(rosario.letaniasDeLaVirgenMessage) - 1:
        # Чтобы не выйти за пределы массива
        current_message = len(rosario.letaniasDeLaVirgenMessage) - 1
    else:
        await callback.message.edit_text(
            text=f'{rosario.letaniasDeLaVirgenMessage[current_message]}',
            parse_mode='Markdown',
            reply_markup=let_cycle_keyboard
        )


@dp.callback_query(F.data == 'let_cycle_answer_pressed_back')
async def answer(callback: CallbackQuery):
    global current_message
    current_message -= 1
    if current_message == 0:
        await callback.message.edit_text(text=f'{rosario.letaniasDeLaVirgenMessage[current_message]}', parse_mode='Markdown', reply_markup=let_cycle_keyboard_beginning)
    elif current_message <= 12:
        await callback.message.edit_text(text=f'{rosario.letaniasDeLaVirgenMessage[current_message]}', parse_mode='Markdown', reply_markup=let_cycle_keyboard)
    else:
        await callback.message.edit_text(text=f'{rosario.letaniasDeLaVirgenMessage[current_message]}', parse_mode='Markdown', reply_markup=let_cycle_keyboard_last)


@dp.callback_query(F.data == 'let_fin_pressed')
async def answer(callback: CallbackQuery):
    global cycleOraciones, current_message
    current_message = 0
    await callback.message.answer(text=f'{rosario.bajoTuAmparo[language]}', reply_markup=ruega_keyboard)
    cycleOraciones = False
@dp.callback_query(F.data == 'ruega_pressed')
async def answer(callback: CallbackQuery):
    global cycleOraciones
    await callback.message.answer(text=f'*Guía:* Ruega por nosotros Santa Madre de Dios\n*Todos:* Para que seamos dignos de las promesas de Cristo\n\n Amen', parse_mode='Markdown')
    await callback.answer(text='La oración ha terminado\n\nDios lo bendiga')
    cycleOraciones = False


# Этот хэндлер будет срабатывать на любые ваши текстовые сообщения,
# кроме команд "/start" и "/help"
@dp.message()
async def send_echo(message: Message):
    await message.reply(text=message.text)

# Новое окончание бота

async def handle(request):
    return web.Response(text="Bot is running 🙏")

async def main():
    try:
        # Удаляем старый webhook (если был)
        await bot.delete_webhook()

        # Запускаем polling
        polling_task = asyncio.create_task(dp.start_polling(bot))

        # Запускаем aiohttp сервер для Render
        app = web.Application()
        app.router.add_get("/", handle)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT", 10000))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()

        print(f"Bot is running on port {port}")

        # Чтобы процесс не завершался
        await polling_task

    finally:
        # закрываем сессию бота корректно
        await bot.session.close()



if __name__ == "__main__":
    asyncio.run(main())

















