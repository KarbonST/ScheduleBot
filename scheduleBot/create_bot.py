import logging
from datetime import timezone

import aiomysql
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from decouple import config
from apscheduler.schedulers.asyncio import AsyncIOScheduler




# Создание пула для подключения к БД Redis с FSM пользователей
redis_pool = Redis(
    host=config('REDIS_HOST'),
    port=int(config('REDIS_PORT')),
    db=int(config('REDIS_DB')),
    #password=config('REDIS_PASSWORD', default=None)
)

# Инициализация объекта AsyncIOScheduler для планирования и выполнения задач по времени
scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

# Настройка администраторов
admins = [int(admin_id) for admin_id in config('ADMINS').split(',')]

# Настройка базового логирования с уровнем INFO
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Создание логгера с именем текущего модуля для записи лог-сообщений
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=config('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Инициализация диспетчера, в котором будут храниться состояния конечных автоматов
redis = Redis(host= config('REDIS_HOST'), port=config('REDIS_PORT'), db=config('REDIS_DB'))
storage = RedisStorage(redis_pool)
dp = Dispatcher(storage=storage)



