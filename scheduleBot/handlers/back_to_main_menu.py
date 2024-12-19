from aiogram import Router, F
from scheduleBot.keyboards.all_keyboards import main_kb
from aiogram.types import Message

back_to_menu_router = Router()

# Хендлер для возврата в главное меню
@back_to_menu_router.message(F.text == "⏪Вернуться в главное меню⏪")
async def return_to_main_menu(message: Message):
    await message.answer(
        text="Вы вернулись в главное меню!",
        reply_markup=main_kb(message.from_user.id)
    )