from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from scheduleBot.create_bot import admins


# Клавиатура "Главное меню"
def main_kb(user_telegram_id: int):
    kb_list = [
        [KeyboardButton(text="📖О нас📖")],
        [KeyboardButton(text="👤Стереть данные поиска👤")],
        [KeyboardButton(text="📚Перейти к расписанию📚")]
    ]
    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text="⚙️Админ панель⚙️")])
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)

    return keyboard


# Клавиатура выбора группы/преподавателя/аудитории
def schedule_choice_kb(user_telegram_id: int):
    kb_list = [
        [KeyboardButton(text="👨‍🎓Группа👩‍🎓")],
        [KeyboardButton(text="👨‍🏫Преподаватель👩‍🏫")],
        [KeyboardButton(text="🏬Аудитория🏬")],
        [KeyboardButton(text="⏪Вернуться в главное меню⏪")]
    ]
    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text="⚙️Админ панель⚙️")])
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)

    return keyboard

# Клавиатура выбора промежутка расписания(сегодня, завтра, эта неделя, следующая неделя)
def duration_choice_kb(user_telegram_id: int):
    kb_list = [
        [KeyboardButton(text="1️⃣Сегодня1️⃣")],
        [KeyboardButton(text="2️⃣Завтра2️⃣")],
        [KeyboardButton(text="3️⃣Эта неделя3️⃣")],
        [KeyboardButton(text="4️⃣Следующая неделя4️⃣")],
        [KeyboardButton(text="⏪Вернуться в главное меню⏪")]

    ]
    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text="⚙️Админ панель⚙️")])
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)

    return keyboard

# Клавиатура да/нет
def yes_no_kb(user_telegram_id: int):
    kb_list = [
        [KeyboardButton(text = "✅Да✅")],
        [KeyboardButton(text = "❌Нет❌")],
        [KeyboardButton(text="⏪Вернуться в главное меню⏪")]
    ]
    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text="⚙️Админ панель⚙️")])
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)

    return keyboard
