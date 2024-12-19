import asyncio
import aiomysql
from decouple import config

from create_bot import bot, scheduler
from create_bot import dp
from handlers.start import start_router

schedule_pool = None  # Глобальная переменная для пула подключений
def get_schedule_pool():
    return schedule_pool

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
    global schedule_pool
    schedule_pool = await create_schedule_pool()  # Создание пула подключений

    dp.include_router(start_router)  # Добавление роутера
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)  # Запуск бота

if __name__ == "__main__":
    asyncio.run(main())
