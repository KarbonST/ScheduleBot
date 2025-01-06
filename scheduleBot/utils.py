
schedule_pool = None  # Глобальная переменная для пула подключений

def set_schedule_pool(pool):
    global schedule_pool
    schedule_pool = pool

def get_schedule_pool():
    return schedule_pool