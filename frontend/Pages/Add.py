# import streamlit as st
# from frontend.auth import require_login
# from backend.database import insert_to_table
#
# def show_add():
#     user = require_login()
#     st.title("➕ Додати звичку або завдання")
#
#     option = st.selectbox("Що ви хочете додати?", ["Звичку", "Завдання"])
#
#     name = st.text_input("Назва", key="name")
#     description = st.text_area("Опис (необов’язково)", key="desc")
#
#     if option == "Звичку":
#         frequency = st.selectbox("Частота", ["daily", "weekly", "monthly"], key="freq")
#
#         day_of_week = None
#         monthly_week = None
#
#         if frequency in ["weekly", "monthly"]:
#             day_of_week = st.selectbox(
#                 "День тижня для повторення",
#                 options=list(range(7)),
#                 format_func=lambda x: ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця", "Субота", "Неділя"][x],
#             )
#
#         if frequency == "monthly":
#             monthly_week = st.selectbox(
#                 "Тиждень місяця",
#                 options=[1, 2, 3, 4, -1],
#                 format_func=lambda x: {1: "Перший", 2: "Другий", 3: "Третій", 4: "Четвертий", -1: "Останній"}[x],
#             )
#
#         if st.button("Додати звичку"):
#             if not name:
#                 st.warning("❗ Введіть назву звички.")
#             else:
#                 habit_data = {
#                     "name": name,
#                     "description": description,
#                     "frequency": frequency,
#                     "day_of_week": day_of_week,
#                     "monthly_week": monthly_week,
#                     "completed": False,
#                     "user_id": user.id
#                 }
#                 insert_to_table("habits_active", habit_data)
#                 st.success("✅ Звичку додано!")
#
#     elif option == "Завдання":
#         date = st.date_input("Дата виконання")
#         time = st.time_input("Час виконання")
#
#         if st.button("Додати завдання"):
#             if not name:
#                 st.warning("❗ Введіть назву завдання.")
#             else:
#                 task_data = {
#                     "name": name,
#                     "description": description,
#                     "date": date.isoformat(),
#                     "time": time.strftime('%H:%M:%S'),
#                     "completed": False,
#                     "user_id": user.id
#                 }
#                 insert_to_table("tasks_active", task_data)
#                 st.success("✅ Завдання додано!")

import streamlit as st
from pytz import timezone
from datetime import datetime, timedelta, time, date

from frontend.auth import require_login
from backend.database import insert_to_table
from backend.calendar_sync import add_event_to_calendar
from backend.google_auth import get_credentials
from utils.helpers import format_day_of_week, format_monthly_position, get_next_occurrence

def show_add():
    user = require_login()
    user_id = user.id
    st.title("➕ Додати звичку або завдання")

    option = st.selectbox("Що ви хочете додати?", ["Звичку", "Завдання"])

    name = st.text_input("Назва")
    description = st.text_area("Опис (необов’язково)")

    if option == "Звичку":
        frequency = st.selectbox("Частота", ["daily", "weekly", "monthly"])
        day_of_week = None
        monthly_week = None
        time_str = "09:00"  # Статичний час для звичок

        if frequency in ["weekly", "monthly"]:
            day_of_week = st.selectbox(
                "День тижня",
                options=list(range(7)),
                format_func=format_day_of_week
            )

        if frequency == "monthly":
            monthly_week = st.selectbox(
                "Тиждень місяця",
                options=[1, 2, 3, 4],
                format_func=format_monthly_position
            )

        if st.button("✅ Додати звичку"):
            if not name:
                st.warning("❗ Введіть назву звички.")
                return

            start = datetime.now().replace(hour=9, minute=0, second=0)
            recurrence = None

            if frequency == "weekly":
                byday = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"][day_of_week]
                recurrence = [f"RRULE:FREQ=WEEKLY;BYDAY={byday}"]
            elif frequency == "monthly":
                try:
                    next_date = get_next_occurrence(day_of_week, monthly_week)
                    start = datetime.combine(next_date.date(), time(hour=9))
                    byday = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"][day_of_week]
                    recurrence = [f"RRULE:FREQ=MONTHLY;BYDAY={monthly_week}{byday}"]
                except Exception as e:
                    st.error(f"❌ Помилка при визначенні дати: {e}")
                    return
            elif frequency == "daily":
                recurrence = ["RRULE:FREQ=DAILY"]

            end = start + timedelta(hours=1)

            habit_data = {
                "name": name,
                "description": description,
                "frequency": frequency,
                "time": time_str,
                "user_id": user_id
            }
            if day_of_week is not None:
                habit_data["day_of_week"] = day_of_week
            if monthly_week is not None:
                habit_data["monthly_week"] = monthly_week

            try:
                get_credentials(user_id)
                event_id = add_event_to_calendar(user_id, name, start, end, description, recurrence)
                habit_data["event_id"] = event_id
            except Exception as e:
                st.warning(f"⚠️ Подія не додана в Google Calendar: {e}")

            insert_to_table("habits_active", habit_data)
            st.success("✅ Звичку додано!")

    else:
        kyiv_tz = timezone("Europe/Kyiv")

        # --- Вибір дати та часу ---
        date_value = st.date_input("Дата виконання", value=date.today(), key="task_date")
        time_value = st.time_input("Час виконання", key="task_time")

        # --- Додавання завдання ---
        if st.button("✅ Додати завдання"):
            if not name:
                st.warning("❗ Введіть назву завдання.")
            else:
                # Формуємо aware datetime у таймзоні Києва
                start = kyiv_tz.localize(datetime.combine(date_value, time_value))
                end = start + timedelta(hours=1)

                task_data = {
                    "name": name,
                    "description": description,
                    "date": str(date_value),
                    "time": time_value.strftime('%H:%M:%S'),
                    "user_id": user_id
                }

                try:
                    get_credentials(user_id)
                    event_id = add_event_to_calendar(user_id, name, start, end, description)
                    task_data["event_id"] = event_id
                except Exception as e:
                    st.warning(f"⚠️ Подія не додана в Google Calendar: {e}")

                insert_to_table("tasks_active", task_data)
                st.success("✅ Завдання додано!")