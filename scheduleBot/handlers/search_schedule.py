from tokenize import group
from scheduleBot.keyboards.all_keyboards import yes_no_kb, duration_choice_kb

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, F
from aiogram.types import Message
from scheduleBot.utils import has_fsm_group, has_fsm_teacher, has_fsm_auditorium
from scheduleBot.utils import find_group_in_db, find_teacher_in_db, find_auditorium_in_db
from scheduleBot.utils import find_schedule_for_day, find_schedule_for_week
from scheduleBot.handlers.back_to_main_menu import return_to_main_menu
import datetime
from collections import defaultdict

# Роутер поиска
search_router = Router()

# Роутер выбора
choice_router = Router()

# Роутер выбора даты поиска
date_router = Router()

# FSM
class SearchInfo(StatesGroup):
    group_name = State()
    group_id = State()

    teacher_name = State()
    teacher_id = State()

    auditorium_name = State()
    auditorium_id = State()

    # Состояние для удаления данных
    delete_data = State()
"""
    Функции для обработки группы
"""
# Пользователь выбирает группу
@search_router.message(F.text == "👨‍🎓Группа👩‍🎓")
async def search_schedule_group(message: Message, state: FSMContext):
    if await has_fsm_group(state):
        # Если ранее уже искали группу, спрашиваем пользователя
        data = await state.get_data()
        last_group = data['group_name']
        await state.set_state(SearchInfo.group_name)
        await message.answer(
            f'Вы уже искали "{last_group}" ранее. Хотите использовать её для поиска расписания?',
            reply_markup=yes_no_kb(message.from_user.id)
        )
    else:
        await state.set_state(SearchInfo.group_name)
        await message.answer("Напишите группу в коротком формате (например, прин-368)")

# Пользователь соглашается использовать ранее введённую группу
@choice_router.message(F.text == "✅Да✅", SearchInfo.group_name)
async def schedule_for_group_from_fsm(message: Message, state: FSMContext):
    data = await state.get_data()
    group_name = data['group_name']
    group_id = data['group_id']
    if group:
        await state.set_state(SearchInfo.group_id)
        await message.answer(f"На какой день вы хотите найти расписание?",
                             reply_markup=duration_choice_kb(message.from_user.id))
    else:
        await message.answer("Не удалось найти сохранённую группу. Напишите её заново.")

# Пользователь отказывается и вводит новую группу
@choice_router.message(F.text == "❌Нет❌", SearchInfo.group_name)
async def search_schedule_new_group(message: Message, state: FSMContext):
    await message.answer("Напишите группу в коротком формате (например, прин-368):")


# Пользователь вводит название группы
@choice_router.message(SearchInfo.group_name)
async def handle_group_input(msg: Message, state: FSMContext):
    group_name = msg.text
    # Проверка на возврат в главное меню
    if group_name == "⏪Вернуться в главное меню⏪":
        await return_to_main_menu(msg)
        return

    # Поиск группы в БД
    group_id = await find_group_in_db(group_name)

    if group_id:
        await state.update_data(group_name = group_name)
        await state.update_data(group_id = group_id)
        await state.set_state(SearchInfo.group_id)
        await msg.answer(f"Группа {group_name} найдена!"
                         f" На какой день вы хотите найти расписание?",
                         reply_markup=duration_choice_kb(msg.from_user.id))
    else:
        await msg.answer(f"Группа {group_name} не найдена в базе данных. Попробуйте снова.")

# Поиск расписания для группы на сегодня или завтра
@date_router.message(F.text.in_(["1️⃣Сегодня1️⃣", "2️⃣Завтра2️⃣"]), SearchInfo.group_id)
async def fetch_group_schedule(msg: Message, state: FSMContext):
    data = await state.get_data()
    group_name = data['group_name']
    group_id = data['group_id']
    date_filter = "today" if msg.text == "1️⃣Сегодня1️⃣" else "tomorrow"
    schedule_date = datetime.date.today().strftime("%d.%m.%Y") if msg.text == "1️⃣Сегодня1️⃣" else (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d.%m.%Y")

    if group_id:
        schedule = await find_schedule_for_day(participant_id=group_id, date_filter=date_filter)
        if schedule:
            schedule_text = "\n\n".join(
                f"📚 {item['subject_name']} ({item['event_kind']})\n"
                f"⏰ {item['start_time']} - {item['end_time']}\n"
                f"🏢 {item['room']}\n"
                for item in schedule
            )
            await msg.answer(f"Расписание группы {group_name} на {schedule_date}:\n\n{schedule_text}", reply_markup=duration_choice_kb(msg.from_user.id))
        else:
            await msg.answer("Расписание на выбранный день не найдено.", reply_markup=duration_choice_kb(msg.from_user.id))
    else:
        await msg.answer("ID группы не найден. Повторите поиск.")


# Поиск расписания для группы на эту или следующую неделю
@date_router.message(F.text.in_(["3️⃣Эта неделя3️⃣", "4️⃣Следующая неделя4️⃣"]), SearchInfo.group_id)
async def fetch_group_schedule_week(msg: Message, state: FSMContext):
    data = await state.get_data()
    group_name = data["group_name"]
    group_id = data["group_id"]

    # Определяем, какую неделю искать
    date_filter = "this_week" if msg.text == "3️⃣Эта неделя3️⃣" else "next_week"

    if not group_id:
        await msg.answer("ID группы не найден. Повторите поиск.")
        return

    # Вызываем функцию, которая вернёт расписание (список занятий за неделю)
    schedule = await find_schedule_for_week(participant_id = group_id, date_filter = date_filter)

    if not schedule:
        await msg.answer("Расписание на выбранную неделю не найдено.", reply_markup=duration_choice_kb(msg.from_user.id))
        return

    from collections import defaultdict
    import datetime

    # Группируем занятия по дате
    schedule_by_date = defaultdict(list)
    for item in schedule:
        schedule_by_date[item["date"]].append(item)

    # Формируем текст для каждой даты
    text_parts = []
    for date_str in sorted(schedule_by_date.keys()):
        items_for_day = schedule_by_date[date_str]
        # Преобразуем YYYY-MM-DD к DD.MM.YYYY
        day_formatted = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")

        # Можно выделить дату жирным с помощью HTML-тега <b> (или <u>, <i>, <code> и т.д.)
        # Важно: при отправке сообщения не забудьте указать parse_mode='HTML'.
        day_schedule_text = "\n\n".join(
            f"📚 {one['subject_name']} ({one['event_kind']})\n"
            f"⏰ {one['start_time']} - {one['end_time']}\n"
            f"🏢 {one['room']}"
            for one in items_for_day
        )

        # Выделяем дату жирным шрифтом
        text_parts.append(f"<b>{day_formatted}</b>\n{day_schedule_text}")

    schedule_text = "\n\n".join(text_parts)

    # Дополнительно выделим заголовок недели
    if date_filter == "this_week":
        week_title = "ЭТУ неделю"
    else:
        week_title = "СЛЕДУЮЩУЮ неделю"

    # Передаем parse_mode='HTML', чтобы теги <b> отработали
    await msg.answer(
        f"Расписание группы <b>{group_name}</b> на {week_title} (Пн–Сб):\n\n{schedule_text}",
        parse_mode="HTML", reply_markup=duration_choice_kb(msg.from_user.id)
    )


"""
    Функции для обработки преподавателя
"""
# Пользователь ищет расписание преподавателя
@search_router.message(F.text == "👨‍🏫Преподаватель👩‍🏫")
async def search_schedule_teacher(message: Message, state: FSMContext):
    if await has_fsm_teacher(state):
        # Если ранее уже искали преподавателя, спрашиваем пользователя
        data = await state.get_data()
        last_teacher = data['teacher_name']
        await state.set_state(SearchInfo.teacher_name)
        await message.answer(
            f'Вы уже искали расписание для "{last_teacher}" ранее. Хотите использовать ФИО повторно?',
            reply_markup=yes_no_kb(message.from_user.id)
        )
    else:
        await state.set_state(SearchInfo.teacher_name)
        await message.answer("Напишите ФИО преподавателя (например, Иванов Иван Иванович)")

# Пользователь соглашается использовать ранее введённого преподавателя
@choice_router.message(F.text == "✅Да✅", SearchInfo.teacher_name)
async def schedule_for_teacher_from_fsm(message: Message, state: FSMContext):
    data = await state.get_data()
    teacher_name = data['teacher_name']
    teacher_id = data['teacher_id']
    if group:
        await state.set_state(SearchInfo.teacher_id)
        await message.answer(f"На какой день вы хотите найти расписание?",
                             reply_markup=duration_choice_kb(message.from_user.id))
    else:
        await message.answer("Не удалось найти преподавателя. Напишите его ФИО заново.")

# Пользователь отказывается и вводит нового преподавателя
@choice_router.message(F.text == "❌Нет❌", SearchInfo.teacher_name)
async def search_schedule_new_teacher(message: Message, state: FSMContext):
    await message.answer("Напишите ФИО преподавателя (например, Иванов Иван Иванович)")

# Пользователь вводит ФИО преподавателя
@choice_router.message(SearchInfo.teacher_name)
async def handle_teacher_input(msg: Message, state: FSMContext):
    teacher_name = msg.text
    # Проверка на возврат в главное меню
    if teacher_name == "⏪Вернуться в главное меню⏪":
        await return_to_main_menu(msg)
        return

    # Поиск группы в БД
    teacher_id = await find_teacher_in_db(teacher_name)

    if teacher_id:
        await state.update_data(teacher_name = teacher_name)
        await state.update_data(teacher_id = teacher_id)
        await state.set_state(SearchInfo.teacher_id)
        await msg.answer(f"Преподаватель {teacher_name} найден!"
                         f" На какой день вы хотите найти расписание?",
                         reply_markup=duration_choice_kb(msg.from_user.id))
    else:
        await msg.answer(f"Преподаватель {teacher_name} не найден в базе данных. Попробуйте снова.")

# Поиск расписания для преподавателя на сегодня или завтра
@date_router.message(F.text.in_(["1️⃣Сегодня1️⃣", "2️⃣Завтра2️⃣"]), SearchInfo.teacher_id)
async def fetch_teacher_schedule(msg: Message, state: FSMContext):
    data = await state.get_data()
    teacher_name = data['teacher_name']
    teacher_id = data['teacher_id']
    date_filter = "today" if msg.text == "1️⃣Сегодня1️⃣" else "tomorrow"
    schedule_date = datetime.date.today().strftime("%d.%m.%Y") if msg.text == "1️⃣Сегодня1️⃣" else (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d.%m.%Y")

    if teacher_id:
        schedule = await find_schedule_for_day(participant_id=teacher_id, date_filter=date_filter)
        if schedule:
            schedule_text = "\n\n".join(
                f"📚 {item['subject_name']} ({item['event_kind']})\n"
                f"⏰ {item['start_time']} - {item['end_time']}\n"
                f"🏢 {item['room']}\n"
                for item in schedule
            )
            await msg.answer(f"Расписание преподавателя {teacher_name} на {schedule_date}:\n\n{schedule_text}", reply_markup=duration_choice_kb(msg.from_user.id))
        else:
            await msg.answer("Расписание на выбранный день не найдено.", reply_markup=duration_choice_kb(msg.from_user.id))
    else:
        await msg.answer("ID преподавателя не найден. Повторите поиск.")

# Поиск расписания для преподавателя на эту или следующую неделю
@date_router.message(F.text.in_(["3️⃣Эта неделя3️⃣", "4️⃣Следующая неделя4️⃣"]), SearchInfo.teacher_id)
async def fetch_teacher_schedule_week(msg: Message, state: FSMContext):
    data = await state.get_data()
    teacher_name = data["teacher_name"]
    teacher_id = data["teacher_id"]

    # Определяем, какую неделю искать
    date_filter = "this_week" if msg.text == "3️⃣Эта неделя3️⃣" else "next_week"

    if not teacher_id:
        await msg.answer("ID преподавателя не найден. Повторите поиск.")
        return

    # Вызываем функцию, которая вернёт расписание (список занятий за неделю)
    schedule = await find_schedule_for_week(participant_id = teacher_id, date_filter = date_filter)

    if not schedule:
        await msg.answer("Расписание на выбранную неделю не найдено.", reply_markup=duration_choice_kb(msg.from_user.id))
        return

    # Группируем занятия по дате
    schedule_by_date = defaultdict(list)
    for item in schedule:
        schedule_by_date[item["date"]].append(item)

    # Формируем текст для каждой даты
    text_parts = []
    for date_str in sorted(schedule_by_date.keys()):
        items_for_day = schedule_by_date[date_str]
        # Преобразуем YYYY-MM-DD к DD.MM.YYYY
        day_formatted = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")

        # Можно выделить дату жирным с помощью HTML-тега <b> (или <u>, <i>, <code> и т.д.)
        # Важно: при отправке сообщения не забудьте указать parse_mode='HTML'.
        day_schedule_text = "\n\n".join(
            f"📚 {one['subject_name']} ({one['event_kind']})\n"
            f"⏰ {one['start_time']} - {one['end_time']}\n"
            f"🏢 {one['room']}"
            for one in items_for_day
        )

        # Выделяем дату жирным шрифтом
        text_parts.append(f"<b>{day_formatted}</b>\n{day_schedule_text}")

    schedule_text = "\n\n".join(text_parts)

    # Дополнительно выделим заголовок недели
    if date_filter == "this_week":
        week_title = "ЭТУ неделю"
    else:
        week_title = "СЛЕДУЮЩУЮ неделю"

    # Передаем parse_mode='HTML', чтобы теги <b> отработали
    await msg.answer(
        f"Расписание преподавателя <b>{teacher_name}</b> на {week_title} (Пн–Сб):\n\n{schedule_text}",
        parse_mode="HTML", reply_markup=duration_choice_kb(msg.from_user.id)
    )

"""
    Функции для обработки аудиторий
"""
# Пользователь ищет расписание аудитории
@search_router.message(F.text == "🏬Аудитория🏬")
async def search_auditorium(message: Message, state: FSMContext):
    if await has_fsm_auditorium(state):
        # Если ранее уже искали аудиторию, спрашиваем пользователя
        data = await state.get_data()
        last_auditorium = data['auditorium_name']
        await state.set_state(SearchInfo.auditorium_name)
        await message.answer(
            f'Вы уже искали расписание для "{last_auditorium}" ранее. Хотите использовать номер аудитории повторно?',
            reply_markup=yes_no_kb(message.from_user.id)
        )
    else:
        await state.set_state(SearchInfo.auditorium_name)
        await message.answer("Напишите номер аудитории (например, В903)")

# Пользователь соглашается использовать ранее введённую аудиторию
@choice_router.message(F.text == "✅Да✅", SearchInfo.auditorium_name)
async def schedule_for_auditorium_from_fsm(message: Message, state: FSMContext):
    data = await state.get_data()
    auditorium_name = data['auditorium_name']
    auditorium_id = data['auditorium_id']
    if group:
        await state.set_state(SearchInfo.auditorium_id)
        await message.answer(f"На какой день вы хотите найти расписание?",
                             reply_markup=duration_choice_kb(message.from_user.id))
    else:
        await message.answer("Не удалось найти преподавателя. Напишите его ФИО заново.")

# Пользователь отказывается и вводит новую аудиторию
@choice_router.message(F.text == "❌Нет❌", SearchInfo.auditorium_name)
async def search_schedule_new_auditorium(message: Message, state: FSMContext):
    await message.answer("Напишите номер аудитории (например, В903")

@choice_router.message(SearchInfo.auditorium_name)
async def handle_auditorium_input(msg: Message, state: FSMContext):
    auditorium_name = msg.text
    # Проверка на возврат в главное меню
    if auditorium_name == "⏪Вернуться в главное меню⏪":
        await return_to_main_menu(msg)
        return

    # Поиск группы в БД
    auditorium_id = await find_auditorium_in_db(auditorium_name)

    if auditorium_id:
        await state.update_data(auditorium_name = auditorium_name)
        await state.update_data(auditorium_id = auditorium_id)
        await state.set_state(SearchInfo.auditorium_id)
        await msg.answer(f"Аудитория {auditorium_name} найдена!"
                         f" На какой день вы хотите найти расписание?",
                         reply_markup=duration_choice_kb(msg.from_user.id))
    else:
        await msg.answer(f"Аудитория {auditorium_name} не найдена в базе данных. Попробуйте снова.")

# Поиск расписания для аудитории на сегодня или завтра
@date_router.message(F.text.in_(["1️⃣Сегодня1️⃣", "2️⃣Завтра2️⃣"]), SearchInfo.auditorium_id)
async def fetch_teacher_schedule(msg: Message, state: FSMContext):
    data = await state.get_data()
    auditorium_name = data['auditorium_name']
    auditorium_id = data['auditorium_id']
    date_filter = "today" if msg.text == "1️⃣Сегодня1️⃣" else "tomorrow"
    schedule_date = datetime.date.today().strftime("%d.%m.%Y") if msg.text == "1️⃣Сегодня1️⃣" else (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d.%m.%Y")

    if auditorium_id:
        schedule = await find_schedule_for_day(place_id=auditorium_id, date_filter=date_filter)
        if schedule:
            schedule_text = "\n\n".join(
                f"📚 {item['subject_name']} ({item['event_kind']})\n"
                f"⏰ {item['start_time']} - {item['end_time']}\n"
                f"🏢 {item['room']}\n"
                for item in schedule
            )
            await msg.answer(f"Расписание аудитории {auditorium_name} на {schedule_date}:\n\n{schedule_text}", reply_markup=duration_choice_kb(msg.from_user.id))
        else:
            await msg.answer("Расписание на выбранный день не найдено.", reply_markup=duration_choice_kb(msg.from_user.id))
    else:
        await msg.answer("ID аудитории не найден. Повторите поиск.")

# Поиск расписания для аудитории на эту или следующую неделю
@date_router.message(F.text.in_(["3️⃣Эта неделя3️⃣", "4️⃣Следующая неделя4️⃣"]), SearchInfo.auditorium_id)
async def fetch_teacher_schedule_week(msg: Message, state: FSMContext):
    data = await state.get_data()
    auditorium_name = data["auditorium_name"]
    auditorium_id = data["auditorium_id"]

    # Определяем, какую неделю искать
    date_filter = "this_week" if msg.text == "3️⃣Эта неделя3️⃣" else "next_week"

    if not auditorium_id:
        await msg.answer("ID аудитории не найден. Повторите поиск.")
        return

    # Вызываем функцию, которая вернёт расписание (список занятий за неделю)
    schedule = await find_schedule_for_week(place_id = auditorium_id, date_filter = date_filter)

    if not schedule:
        await msg.answer("Расписание на выбранную неделю не найдено.", reply_markup=duration_choice_kb(msg.from_user.id))
        return

    # Группируем занятия по дате
    schedule_by_date = defaultdict(list)
    for item in schedule:
        schedule_by_date[item["date"]].append(item)

    # Формируем текст для каждой даты
    text_parts = []
    for date_str in sorted(schedule_by_date.keys()):
        items_for_day = schedule_by_date[date_str]
        # Преобразуем YYYY-MM-DD к DD.MM.YYYY
        day_formatted = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")

        # Можно выделить дату жирным с помощью HTML-тега <b> (или <u>, <i>, <code> и т.д.)
        # Важно: при отправке сообщения не забудьте указать parse_mode='HTML'.
        day_schedule_text = "\n\n".join(
            f"📚 {one['subject_name']} ({one['event_kind']})\n"
            f"⏰ {one['start_time']} - {one['end_time']}\n"
            f"🏢 {one['room']}"
            for one in items_for_day
        )

        # Выделяем дату жирным шрифтом
        text_parts.append(f"<b>{day_formatted}</b>\n{day_schedule_text}")

    schedule_text = "\n\n".join(text_parts)

    # Дополнительно выделим заголовок недели
    if date_filter == "this_week":
        week_title = "ЭТУ неделю"
    else:
        week_title = "СЛЕДУЮЩУЮ неделю"

    # Передаем parse_mode='HTML', чтобы теги <b> отработали
    await msg.answer(
        f"Расписание аудитории <b>{auditorium_name}</b> на {week_title} (Пн–Сб):\n\n{schedule_text}",
        parse_mode="HTML", reply_markup=duration_choice_kb(msg.from_user.id)
    )