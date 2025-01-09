from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from scheduleBot.keyboards.all_keyboards import schedule_choice_kb, yes_no_kb, main_kb
from scheduleBot.handlers.search_schedule import SearchInfo

switch_router = Router()

@switch_router.message(F.text == "📚Перейти к расписанию📚")
async def switch_to_schedule(message: Message):
    await message.answer(text= "Выбери, для кого ты хочешь найти расписание",
                         reply_markup=schedule_choice_kb(message.from_user.id))

@switch_router.message(F.text == "👤Стереть данные поиска👤")
async def delete_data(message: Message, state: FSMContext):
    await state.set_state(SearchInfo.delete_data)
    await message.answer(
        text="Вы уверены, что хотите удалить все данные поиска?",
        reply_markup=yes_no_kb(message.from_user.id)
    )

@switch_router.message(SearchInfo.delete_data)
async def handle_delete_confirmation(message: Message, state: FSMContext):
    if message.text == "✅Да✅":
        # Удаляем данные из FSM
        #await state.update_data(group=None, teacher=None, auditorium=None)
        await state.clear()
        await message.answer("Данные поиска успешно удалены!", reply_markup=main_kb(message.from_user.id))
    elif message.text == "❌Нет❌":
        await message.answer("Удаление данных отменено.", reply_markup=main_kb(message.from_user.id))

