from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from scheduleBot.keyboards.all_keyboards import main_kb

start_router = Router()


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет, я бот расписания ВолгГТУ! Я помогу тебе разобраться'
                         ', где у тебя проходит пара, не важно, студент ты или преподаватель!'
                         'Также ты сможешь узнать расписание любой интересующей тебя аудитории.',
                         reply_markup=main_kb(message.from_user.id))


