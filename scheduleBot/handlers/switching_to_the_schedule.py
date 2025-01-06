import asyncio

from aiogram.utils.chat_action import ChatActionSender
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
import scheduleBot.keyboards.all_keyboards
from decouple import config

from scheduleBot.keyboards.all_keyboards import schedule_choice_kb

switch_router = Router()

@switch_router.message(F.text == "📚Перейти к расписанию📚")
async def switch_to_schedule(message: Message):
    await message.answer(text= "Выбери, для кого ты хочешь найти расписание",
                         reply_markup=schedule_choice_kb(message.from_user.id))