import datetime
from typing import List, Dict
from aiogram.fsm.context import FSMContext

schedule_pool = None  # Глобальная переменная для пула подключений

def set_schedule_pool(pool):
    global schedule_pool
    schedule_pool = pool

def get_schedule_pool():
    return schedule_pool


# Поиск расписания на сегодня или завтра
async def find_schedule_for_day(participant_id: str, date_filter: str) -> List[Dict]:
    """
    Поиск расписания для участника (группы, преподавателя) или аудитории.

    :param participant_id: UUID участника (группа или преподаватель)
    :param date_filter: Фильтр даты (например, 'today' или 'tomorrow')
    :return: Список расписания (список словарей)
    """
    # Определяем дату для фильтра
    today = datetime.date.today()
    if date_filter == "today":
        target_date = today
    elif date_filter == "tomorrow":
        target_date = today + datetime.timedelta(days=1)
    else:
        raise ValueError("Invalid date_filter. Use 'today' or 'tomorrow'.")

    # Приводим дату в строковый формат для MySQL
    target_date_str = target_date.strftime("%Y-%m-%d")

    # Формируем запрос
    # Обратите внимание, что в WHERE мы используем:
    #   JSON_CONTAINS(e.data, JSON_QUOTE(%s), '$.participants')
    # чтобы искать participant_id в массиве participants
    query = """
        SELECT 
            e.idnumber AS event_id,
            JSON_UNQUOTE(JSON_EXTRACT(s.data, '$.name')) AS subject_name,
            JSON_UNQUOTE(JSON_EXTRACT(ek.data, '$.name')) AS event_kind,
            JSON_UNQUOTE(JSON_EXTRACT(tp.data, '$.start_time')) AS start_time,
            JSON_UNQUOTE(JSON_EXTRACT(tp.data, '$.end_time'))   AS end_time,
            JSON_UNQUOTE(JSON_EXTRACT(pl.data, '$.room'))       AS room,
            JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.date'))       AS date
        FROM events e
            JOIN holding_info hi 
                ON JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.event_id')) = e.idnumber
            JOIN time_slots tp 
                ON JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.slot_id')) = tp.idnumber
            JOIN event_places pl 
                ON JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.place_id')) = pl.idnumber
            JOIN subjects s 
                ON JSON_UNQUOTE(JSON_EXTRACT(e.data, '$.subject_id')) = s.idnumber
            JOIN event_kinds ek 
                ON JSON_UNQUOTE(JSON_EXTRACT(e.data, '$.kind_id')) = ek.idnumber
        WHERE 
            JSON_CONTAINS(e.data->>'$.participants', JSON_QUOTE(%s))
            AND JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.date')) = %s
        ORDER BY
            JSON_UNQUOTE(JSON_EXTRACT(tp.data, '$.start_time'));
    """

    # Выполняем запрос с помощью пула соединений
    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (participant_id, target_date_str))
            rows = await cursor.fetchall()

    # Преобразуем результат в список словарей
    schedule = []
    for row in rows:
        schedule.append({
            "event_id":      row[0],
            "subject_name":  row[1],
            "event_kind":    row[2],
            "start_time":    row[3],
            "end_time":      row[4],
            "room":          row[5],
            "date":          row[6],
        })

    return schedule

# Поиск расписания на эту или следующую неделю
async def find_schedule_for_week(participant_id: str, date_filter: str) -> List[Dict]:
    """
    Поиск расписания для участника (группы, преподавателя) или аудитории
    на неделю (с понедельника по субботу текущей недели).

    :param date_filter: Эта неделя или следующая
    :param participant_id: UUID участника (группа или преподаватель)
    :return: Список расписания (список словарей) за неделю
    """
    today = datetime.date.today()
    # Находим понедельник текущей недели
    # weekday(): Понедельник = 0, ... , Воскресенье = 6
    monday = today - datetime.timedelta(days=today.weekday())
    # Суббота = понедельник + 5 дней
    saturday = monday + datetime.timedelta(days=5)

    today = datetime.date.today()
    # Находим понедельник «текущей» недели
    # weekday(): Понедельник = 0, ..., Воскресенье = 6
    monday = today - datetime.timedelta(days=today.weekday())
    # Суббота = понедельник + 5 дней
    saturday = monday + datetime.timedelta(days=5)

    # Если нужно следующую неделю — сдвигаем на 7 дней вперёд
    if date_filter == "next_week":
        monday += datetime.timedelta(weeks=1)
        saturday += datetime.timedelta(weeks=1)
    elif date_filter != "this_week":
        raise ValueError("Invalid date_filter. Use 'this_week' or 'next_week'.")

    # Приводим даты в строковый формат YYYY-MM-DD для MySQL
    monday_str = monday.strftime("%Y-%m-%d")
    saturday_str = saturday.strftime("%Y-%m-%d")

    # Сформируем запрос на период (BETWEEN monday AND saturday)
    query = """
        SELECT 
            e.idnumber AS event_id,
            JSON_UNQUOTE(JSON_EXTRACT(s.data, '$.name'))    AS subject_name,
            JSON_UNQUOTE(JSON_EXTRACT(ek.data, '$.name'))   AS event_kind,
            JSON_UNQUOTE(JSON_EXTRACT(tp.data, '$.start_time')) AS start_time,
            JSON_UNQUOTE(JSON_EXTRACT(tp.data, '$.end_time'))   AS end_time,
            JSON_UNQUOTE(JSON_EXTRACT(pl.data, '$.room'))       AS room,
            JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.date'))       AS date
        FROM events e
            JOIN holding_info hi
                ON JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.event_id')) = e.idnumber
            JOIN time_slots tp
                ON JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.slot_id')) = tp.idnumber
            JOIN event_places pl
                ON JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.place_id')) = pl.idnumber
            JOIN subjects s
                ON JSON_UNQUOTE(JSON_EXTRACT(e.data, '$.subject_id')) = s.idnumber
            JOIN event_kinds ek
                ON JSON_UNQUOTE(JSON_EXTRACT(e.data, '$.kind_id'))   = ek.idnumber
        WHERE 
            JSON_CONTAINS(e.data->>'$.participants', JSON_QUOTE(%s))
            AND JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.date')) BETWEEN %s AND %s
        ORDER BY
            JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.date')),
            JSON_UNQUOTE(JSON_EXTRACT(tp.data, '$.start_time'));
    """

    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            # Передаем параметр participant_id, затем monday_str, saturday_str
            await cursor.execute(query, (participant_id, monday_str, saturday_str))
            rows = await cursor.fetchall()

    schedule = []
    for row in rows:
        schedule.append({
            "event_id":      row[0],
            "subject_name":  row[1],
            "event_kind":    row[2],
            "start_time":    row[3],
            "end_time":      row[4],
            "room":          row[5],
            "date":          row[6],
        })

    return schedule

# Функция для поиска группы в MySQL
async def find_group_in_db(group_name: str):
    query = """
    SELECT idnumber
    FROM event_participants
    WHERE JSON_UNQUOTE(JSON_EXTRACT(data, '$.name')) = %s;
    """

    # Подключение к пулу MySQL
    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, group_name)
            result = await cursor.fetchone()

    if result:
        return result[0]  # Возвращаем найденный idnumber
    else:
        return None  # Группа не найдена


# Функция для поиска преподавателя в MySQL
async def find_teacher_in_db(teacher_name: str):
    query = """
    SELECT idnumber
    FROM event_participants
    WHERE JSON_UNQUOTE(JSON_EXTRACT(data, '$.name')) = %s;
    """

    # Подключение к пулу MySQL
    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, teacher_name)
            result = await cursor.fetchone()

    if result:
        return result[0]  # Возвращаем найденный idnumber
    else:
        return None  # Преподаватель не найден


# Функция для поиска аудитории в MySQL
async def find_auditorium_in_db(auditorium_name: str):
    query = """
    SELECT idnumber
    FROM event_participants
    WHERE JSON_UNQUOTE(JSON_EXTRACT(data, '$.name')) = %s;
    """

    # Подключение к пулу MySQL
    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, auditorium_name)
            result = await cursor.fetchone()

    if result:
        return result[0]  # Возвращаем найденный idnumber
    else:
        return None  # Аудитория не найдена


# Функция для проверки наличия группы в FSM
async def has_fsm_group(state: FSMContext) -> bool:
    data = await state.get_data()
    return 'group_id' in data and data['group_id'] is not None


# Функция для проверки наличия преподавателя в FSM
async def has_fsm_teacher(state: FSMContext) -> bool:
    data = await state.get_data()
    return 'teacher_id' in data and data['teacher_id'] is not None


# Функция для проверки наличия аудитории в FSM
async def has_fsm_auditorium(state: FSMContext) -> bool:
    data = await state.get_data()
    return 'auditorium_id' in data and data['auditorium_id'] is not None