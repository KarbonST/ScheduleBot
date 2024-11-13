from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

start_router = Router()


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет, я бот расписания ВолгГТУ! Я помогу тебе разобраться'
                         ', где у тебя проходит пара, будь ты студентом или преподавателем!'
                         'Так же ты сможешь узнать расписание любой интересующей тебя аудитории')


