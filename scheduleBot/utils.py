import datetime
from typing import List, Dict
from aiogram.fsm.context import FSMContext

schedule_pool = None  # Глобальная переменная для пула подключений

def set_schedule_pool(pool):
    global schedule_pool
    schedule_pool = pool

def get_schedule_pool():
    return schedule_pool


import datetime
from typing import List, Dict, Optional


# from your_db_module import get_schedule_pool

async def find_schedule_for_day(
        participant_id: Optional[str] = None,
        place_id: Optional[str] = None,
        date_filter: str = "today"
) -> List[Dict]:
    """
    Поиск расписания:
    1) Для участника (группы, преподавателя), если передан participant_id,
    2) Или для аудитории, если передан place_id.

    :param participant_id: UUID участника (группа или преподаватель)
    :param place_id: UUID аудитории (из таблицы event_places.idnumber),
                     если ищем расписание по аудитории.
    :param date_filter: 'today' или 'tomorrow'
    :return: Список расписания (список словарей)
    """
    # 1. Определяем дату для фильтра
    today = datetime.date.today()
    if date_filter == "today":
        target_date = today
    elif date_filter == "tomorrow":
        target_date = today + datetime.timedelta(days=1)
    else:
        raise ValueError("Invalid date_filter. Use 'today' or 'tomorrow'.")

    # 2. Приводим дату в строковый формат
    target_date_str = target_date.strftime("%Y-%m-%d")

    # 3. Строим WHERE-часть динамически, в зависимости от того,
    #    ищем ли мы по participant_id или place_id (или сразу по обоим).
    where_clauses = []
    params = []

    # Если нужен поиск по участнику
    if participant_id is not None:
        where_clauses.append("JSON_CONTAINS(e.data->>'$.participants', JSON_QUOTE(%s))")
        params.append(participant_id)

    # Если нужен поиск по аудитории
    if place_id is not None:
        where_clauses.append("JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.place_id')) = %s")
        params.append(place_id)

    # Фильтр по дате
    where_clauses.append("JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.date')) = %s")
    params.append(target_date_str)

    # Объединяем все условия (AND между ними)
    where_condition = " AND ".join(where_clauses)

    # 4. Сам запрос
    query = f"""
        SELECT 
            e.idnumber AS event_id,
            JSON_UNQUOTE(JSON_EXTRACT(s.data, '$.name'))       AS subject_name,
            JSON_UNQUOTE(JSON_EXTRACT(ek.data, '$.name'))      AS event_kind,
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
            {where_condition}
        ORDER BY
            JSON_UNQUOTE(JSON_EXTRACT(tp.data, '$.start_time'));
    """

    # 5. Выполняем запрос
    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()

    # 6. Преобразуем результат в список словарей
    schedule = []
    for row in rows:
        schedule.append({
            "event_id": row[0],
            "subject_name": row[1],
            "event_kind": row[2],
            "start_time": row[3],
            "end_time": row[4],
            "room": row[5],
            "date": row[6],
        })

    return schedule


import datetime
from typing import List, Dict, Optional


# from your_db_module import get_schedule_pool

async def find_schedule_for_week(
        date_filter: str,
        participant_id: Optional[str] = None,
        place_id: Optional[str] = None
) -> List[Dict]:
    """
    Поиск расписания на неделю (с понедельника по субботу) для:
      - Участника (группа или преподаватель), если задан participant_id,
      - Или аудитории, если задан place_id,
      - Или и того, и другого одновременно, если заданы оба.

    :param date_filter: 'this_week' или 'next_week'
    :param participant_id: UUID участника (группы или преподавателя)
    :param place_id: UUID аудитории (из таблицы event_places.idnumber)
    :return: Список занятий (словарей) за заданный период.
    """

    # 1. Определяем границы недели (понедельник–суббота)
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())  # weekday(): Пн=0, Вс=6
    saturday = monday + datetime.timedelta(days=5)

    if date_filter == "next_week":
        monday += datetime.timedelta(weeks=1)
        saturday += datetime.timedelta(weeks=1)
    elif date_filter != "this_week":
        raise ValueError("Invalid date_filter. Use 'this_week' or 'next_week'.")

    monday_str = monday.strftime("%Y-%m-%d")
    saturday_str = saturday.strftime("%Y-%m-%d")

    # 2. Динамически формируем WHERE‑условия
    where_clauses = []
    params = []

    # Если ищем по участнику
    if participant_id is not None:
        where_clauses.append("JSON_CONTAINS(e.data->>'$.participants', JSON_QUOTE(%s))")
        params.append(participant_id)

    # Если ищем по аудитории
    if place_id is not None:
        where_clauses.append("JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.place_id')) = %s")
        params.append(place_id)

    # Добавляем условие по диапазону дат
    where_clauses.append("JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.date')) BETWEEN %s AND %s")
    params.append(monday_str)
    params.append(saturday_str)

    # Склеиваем условия через AND
    where_condition = " AND ".join(where_clauses)

    # 3. Составляем запрос
    query = f"""
        SELECT
            e.idnumber AS event_id,
            JSON_UNQUOTE(JSON_EXTRACT(s.data, '$.name'))         AS subject_name,
            JSON_UNQUOTE(JSON_EXTRACT(ek.data, '$.name'))        AS event_kind,
            JSON_UNQUOTE(JSON_EXTRACT(tp.data, '$.start_time'))  AS start_time,
            JSON_UNQUOTE(JSON_EXTRACT(tp.data, '$.end_time'))    AS end_time,
            JSON_UNQUOTE(JSON_EXTRACT(pl.data, '$.room'))        AS room,
            JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.date'))        AS date
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
            {where_condition}
        ORDER BY
            JSON_UNQUOTE(JSON_EXTRACT(hi.data, '$.date')),
            JSON_UNQUOTE(JSON_EXTRACT(tp.data, '$.start_time'));
    """

    # 4. Выполняем запрос
    async with get_schedule_pool().acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()

    # 5. Преобразуем результат в список словарей
    schedule = []
    for row in rows:
        schedule.append({
            "event_id": row[0],
            "subject_name": row[1],
            "event_kind": row[2],
            "start_time": row[3],
            "end_time": row[4],
            "room": row[5],
            "date": row[6],
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
    FROM event_places
    WHERE JSON_UNQUOTE(JSON_EXTRACT(data, '$.room')) = %s;
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