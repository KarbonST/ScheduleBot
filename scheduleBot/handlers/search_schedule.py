import asyncio
#from importlib.metadata import pass_none


from aiogram.utils.chat_action import ChatActionSender
from scheduleBot.aiogram_run import get_schedule_pool
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

search_router = Router()
schedule_pool = None



# FSM
class SearchInfo(StatesGroup):
    group = State()
    teacher = State()
    auditorium = State()

# Функция для поиска группы в MySQL
async def find_group_in_db(group_name: str):
    query = """
    SELECT *
    FROM schedules
    WHERE JSON_CONTAINS(
        event_participants,
        %s,
        '$'
    )
    """
    # Подключение к пулу MySQL
    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            # Формируем JSON-строку для поиска
            search_value = json.dumps({"name": group_name})
            await cursor.execute(query, (search_value,))
            result = await cursor.fetchall()
            return result


# Пользователь ищет расписание группы
@search_router.message(F.text == "👨‍🎓Группа👩‍🎓")
async def search_schedule(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(2)
        await message.answer('Напиши группу в коротком формате(прин-368)')

    # Поиск группы в БД
    @search_router.message()
    async def handle_group_input(msg: Message, state: FSMContext):
        group_name = msg.text
        result = await find_group_in_db(group_name)

        if result:
            await msg.answer(f"Группа {group_name} найдена:\n{result}")
        else:
            await msg.answer(f"Группа {group_name} не найдена в базе данных.")


# Пользователь ищет расписание преподавателя
@search_router.message(F.text == "👨‍🏫Преподаватель👩‍🏫")
async def search_teacher(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(2)
        await message.answer('Напиши ФИО преподавателя')

# Пользователь ищет расписание аудитории
@search_router.message(F.text == "🏬Аудитория🏬")
async def search_auditorium(message: Message, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(2)
        await message.answer('Напиши номер аудитории(В-903)')


