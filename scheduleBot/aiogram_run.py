import asyncio
import aiomysql
from decouple import config

from scheduleBot.create_bot import bot, scheduler, dp
from scheduleBot.handlers.back_to_main_menu import back_to_menu_router
from scheduleBot.handlers.start import start_router
from scheduleBot.handlers.switching_to_the_schedule import switch_router
from scheduleBot.handlers.search_schedule import search_router, choice_router
from scheduleBot.utils import set_schedule_pool

# Создание пула подключений для MySQL
async def create_schedule_pool():
    return await aiomysql.create_pool(
        host=config('DB_HOST'),
        port=int(config('DB_PORT')),
        user=config('DB_USER'),
        password=config('DB_PASSWORD'),
        db=config('DB_NAME'),
        minsize=1,
        maxsize=100
    )

# Основная асинхронная функция
async def main():
    schedule_pool = await create_schedule_pool()  # Создание пула подключений
    set_schedule_pool(schedule_pool)


    # Добавление роутеров
    dp.include_router(start_router)
    dp.include_router(switch_router)
    dp.include_router(search_router)
    dp.include_router(choice_router)
    dp.include_router(back_to_menu_router)
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)  # Запуск бота

if __name__ == "__main__":
    asyncio.run(main())
