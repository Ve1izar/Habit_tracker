import streamlit as st
from frontend.auth import require_login
from backend.database import insert_to_table

def show_add():
    user = require_login()
    st.title("➕ Додати звичку або завдання")

    option = st.selectbox("Що ви хочете додати?", ["Звичку", "Завдання"])

    name = st.text_input("Назва", key="name")
    description = st.text_area("Опис (необов’язково)", key="desc")

    if option == "Звичку":
        frequency = st.selectbox("Частота", ["daily", "weekly", "monthly"], key="freq")

        day_of_week = None
        monthly_week = None

        if frequency in ["weekly", "monthly"]:
            day_of_week = st.selectbox(
                "День тижня для повторення",
                options=list(range(7)),
                format_func=lambda x: ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця", "Субота", "Неділя"][x],
            )

        if frequency == "monthly":
            monthly_week = st.selectbox(
                "Тиждень місяця",
                options=[1, 2, 3, 4, -1],
                format_func=lambda x: {1: "Перший", 2: "Другий", 3: "Третій", 4: "Четвертий", -1: "Останній"}[x],
            )

        if st.button("Додати звичку"):
            if not name:
                st.warning("❗ Введіть назву звички.")
            else:
                habit_data = {
                    "name": name,
                    "description": description,
                    "frequency": frequency,
                    "day_of_week": day_of_week,
                    "monthly_week": monthly_week,
                    "completed": False,
                    "user_id": user.id
                }
                insert_to_table("habits_active", habit_data)
                st.success("✅ Звичку додано!")

    elif option == "Завдання":
        date = st.date_input("Дата виконання")
        time = st.time_input("Час виконання")

        if st.button("Додати завдання"):
            if not name:
                st.warning("❗ Введіть назву завдання.")
            else:
                task_data = {
                    "name": name,
                    "description": description,
                    "date": date.isoformat(),
                    "time": time.strftime('%H:%M:%S'),
                    "completed": False,
                    "user_id": user.id
                }
                insert_to_table("tasks_active", task_data)
                st.success("✅ Завдання додано!")
