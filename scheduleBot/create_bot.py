import logging
from datetime import timezone

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import _mysql_connector

# Инициализация объекта AsyncIOScheduler для планирования и выполнения задач по времени
scheduler = AsyncIOScheduler(timezone = 'Europe/Moscow')

# Настройка администраторов
admins = [int(admin_id) for admin_id in config('ADMINS').split(',')]

# Настройка базового логирования с уровнем INFO
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Создание логгера с именем текущего модуля для записи лог-сообщений
logger = logging.getLogger(__name__)



