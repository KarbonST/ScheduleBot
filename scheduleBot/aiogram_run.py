import asyncio
from create_bot import bot, dp, scheduler
from handlers.start import start_router


# from work_time.time_func import send_time_msg

# Определение основной асинхронной функции main
async def main():
    dp.include_router(start_router)  # Добавление роутера
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)  # Запуск бота в режиме опроса(polling)


if __name__ == "__main__":
    asyncio.run(main())
