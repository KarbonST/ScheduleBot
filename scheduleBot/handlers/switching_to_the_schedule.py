import asyncio

from aiogram.utils.chat_action import ChatActionSender
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, F
from aiogram.types import Message
from scheduleBot.handlers.search_schedule import SearchInfo


from scheduleBot.keyboards.all_keyboards import schedule_choice_kb, yes_no_kb

switch_router = Router()

@switch_router.message(F.text == "📚Перейти к расписанию📚")
async def switch_to_schedule(message: Message):
    await message.answer(text= "Выбери, для кого ты хочешь найти расписание",
                         reply_markup=schedule_choice_kb(message.from_user.id))

@switch_router.message(F.text == "👤Стереть данные поиска👤")
async def delete_data(message:Message):
    await message.answer(text = "Вы уверены, что хотите удалить все данные поиска?",
                         reply_markup=yes_no_kb(message.from_user.id))
