import asyncio
from tokenize import group

#from importlib.metadata import pass_none


from aiogram.utils.chat_action import ChatActionSender

from scheduleBot.keyboards.all_keyboards import yes_no_kb, duration_choice_kb
from scheduleBot.utils import get_schedule_pool
from scheduleBot.create_bot import bot, redis_pool
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
import scheduleBot.keyboards.all_keyboards
from scheduleBot.handlers.start import start_router
from decouple import config
import json
from scheduleBot.handlers.back_to_main_menu import return_to_main_menu

# Роутер поиска
search_router = Router()

# Роутер выбора
choice_router = Router()

# FSM
class SearchInfo(StatesGroup):
    group_name = State()
    group_id = State()

    teacher_name = State()
    teacher_id = State()

    auditorium_name = State()
    auditorium_id = State()

# Функция для поиска группы в MySQL
async def find_group_in_db(group_name: str):
    query = """
    SELECT idnumber
    FROM event_participants
    WHERE name = %s;
    """

    # Подключение к пулу MySQL
    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, group_name)
            result = await cursor.fetchone()

    if result:
        return result[0]  # Возвращаем найденный idnumber
    else:
        return None  # Группа не найдена

# Функция для поиска преподавателя в MySQL
async def find_teacher_in_db(teacher_name: str):
    query = """
        SELECT idnumber
        FROM event_participants
        WHERE name = %s AND role = 'teacher';
        """

    # Подключение к пулу MySQL
    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, teacher_name)
            result = await cursor.fetchone()

    if result:
        return result[0]  # Возвращаем найденный idnumber
    else:
        return None  # Преподаватель не найден

# Функция для поиска аудитории в MySQL
async def find_auditorium_in_db(auditorium_name: str):
    query = """
        SELECT idnumber
        FROM event_places
        WHERE auditorium = %s;
        """

    # Подключение к пулу MySQL
    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, auditorium_name)
            result = await cursor.fetchone()

    if result:
        return result[0]  # Возвращаем найденный idnumber
    else:
        return None  # Аудитория не найдена

# Функция для проверки наличия группы в FSM
async def has_fsm_group(state: FSMContext) -> bool:
    data = await state.get_data()
    return 'group_id' in data and data['group_id'] is not None

# Функция для проверки наличия преподавателя в FSM
async def has_fsm_teacher(state: FSMContext) -> bool:
    data = await state.get_data()
    return 'teacher_id' in data and data['teacher_id'] is not None

# Функция для проверки наличия аудитории в FSM
async def has_fsm_auditorium(state: FSMContext) -> bool:
    data = await state.get_data()
    return 'auditorium_id' in data and data['auditorium_id'] is not None

"""
    Функции для обработки группы
"""
# Пользователь выбирает группу
@search_router.message(F.text == "👨‍🎓Группа👩‍🎓")
async def search_schedule_group(message: Message, state: FSMContext):
    if await has_fsm_group(state):
        # Если ранее уже искали группу, спрашиваем пользователя
        data = await state.get_data()
        last_group = data['group_name']
        await state.set_state(SearchInfo.group_name)
        await message.answer(
            f'Вы уже искали "{last_group}" ранее. Хотите использовать её для поиска расписания?',
            reply_markup=yes_no_kb(message.from_user.id)
        )
    else:
        await state.set_state(SearchInfo.group_name)
        await message.answer("Напишите группу в коротком формате (например, прин-368)")

# Пользователь соглашается использовать ранее введённую группу
@choice_router.message(F.text == "✅Да✅", SearchInfo.group_name)
async def schedule_for_group_from_fsm(message: Message, state: FSMContext):
    data = await state.get_data()
    group_name = data['group_name']
    group_id = data['group_id']
    if group:
        await message.answer(f"Ищу расписание для группы: {group_name}...")

    else:
        await message.answer("Не удалось найти сохранённую группу. Напишите её заново.")

# Пользователь отказывается и вводит новую группу
@choice_router.message(F.text == "❌Нет❌", SearchInfo.group_name)
async def search_schedule_new_group(message: Message, state: FSMContext):
    await message.answer("Напишите группу в коротком формате (например, прин-368):")


# Пользователь вводит название группы
@choice_router.message(SearchInfo.group_name)
async def handle_group_input(msg: Message, state: FSMContext):
    group_name = msg.text
    # Проверка на возврат в главное меню
    if group_name == "⏪Вернуться в главное меню⏪":
        await return_to_main_menu(msg)
        return

    # Поиск группы в БД
    group_id = await find_group_in_db(group_name)

    if group_id:
        await msg.answer(f"Группа {group_name}, {group_id} найдена!")
        await state.update_data(group_name = group_name)
        await state.update_data(group_id = group_id)
        # Перейти к следующему шагу, если требуется
    else:
        await msg.answer(f"Группа {group_name} не найдена в базе данных. Попробуйте снова.")


# Пользователь ищет расписание преподавателя
@search_router.message(F.text == "👨‍🏫Преподаватель👩‍🏫")
async def search_teacher(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await message.answer('Напиши ФИО преподавателя')

# Пользователь ищет расписание аудитории
@search_router.message(F.text == "🏬Аудитория🏬")
async def search_auditorium(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await message.answer('Напиши номер аудитории(В-903)')


