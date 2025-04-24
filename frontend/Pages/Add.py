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
            day_name = st.selectbox("День тижня повторення", [
                "Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця", "Субота", "Неділя"
            ])
            day_of_week = day_name
        if frequency == "monthly":
            monthly_week = st.selectbox("Тиждень місяця", [1, 2, 3, 4, -1])

        if st.button("Додати звичку"):
            if not name:
                st.warning("❗ Введіть назву звички.")
            else:
                insert_to_table("habits_active", {
                    "name": name,
                    "description": description,
                    "frequency": frequency,
                    "day_of_week": day_of_week,
                    "monthly_week": monthly_week,
                    "completed": False,
                    "user_id": user.id
                })
                st.success("✅ Звичку додано!")

    elif option == "Завдання":
        date = st.date_input("Дата виконання")
        time = st.time_input("Час виконання")

        if st.button("Додати завдання"):
            if not name:
                st.warning("❗ Введіть назву завдання.")
            else:
                insert_to_table("tasks_active", {
                    "name": name,
                    "description": description,
                    "date": date.isoformat(),
                    "time": time.strftime('%H:%M:%S'),
                    "completed": False,
                    "user_id": user.id
                })
                st.success("✅ Завдання додано!")
