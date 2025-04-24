import streamlit as st
from frontend.auth import require_login
from backend.logic import (
    get_active_habits,
    get_active_tasks,
    complete_entry,
    postpone_entry,
    sync_events_to_google_calendar
)
from backend.database import update_entry, delete_entry
from utils.helpers import format_day_of_week, format_monthly_position
from datetime import datetime

def show_home():
    user = require_login()
    st.title("🏠 Активні звички та завдання")

    # --- Синхронізація з календарем ---
    if st.button("🔄 Синхронізувати з Google Calendar"):
        sync_events_to_google_calendar(user.id)
        st.success("Синхронізація завершена!")

    # --- Звички ---
    st.subheader("🔁 Активні звички")
    habits = get_active_habits(user.id)

    for habit in habits:
        col1 = st.container()
        with col1:
            frequency = habit["frequency"]
            if frequency == "monthly":
                repeat_str = f"{format_monthly_position(habit.get('monthly_week'))} {format_day_of_week(habit.get('day_of_week', 0))}"
            elif frequency == "weekly":
                repeat_str = format_day_of_week(habit.get("day_of_week", 0))
            else:
                repeat_str = "Щодня"

            st.markdown(f"**{habit['name']}** — {habit['frequency']} ({repeat_str})")
            if habit.get("description"):
                st.caption(habit["description"])

            if st.button("✅ Завершити", key=f"complete_habit_{habit['id']}"):
                complete_entry("habit", habit["id"], user.id)
                st.rerun()

            if st.button("⏸️ Відкласти", key=f"postpone_habit_{habit['id']}"):
                postpone_entry("habit", habit["id"], user.id)
                st.rerun()

            with st.expander("✏️ Редагувати", expanded=False):
                new_name = st.text_input("Назва", value=habit["name"], key=f"name_habit_{habit['id']}")
                new_description = st.text_area("Опис", value=habit.get("description", ""), key=f"desc_habit_{habit['id']}")
                new_frequency = st.selectbox("Частота", ["daily", "weekly", "monthly"], index=["daily", "weekly", "monthly"].index(habit["frequency"]), key=f"freq_habit_{habit['id']}")

                new_day_of_week = 0
                new_monthly_week = 1
                if new_frequency in ["weekly", "monthly"]:
                    new_day_of_week = st.selectbox("День тижня", list(range(7)), index=habit.get("day_of_week", 0), format_func=format_day_of_week, key=f"day_habit_{habit['id']}")
                if new_frequency == "monthly":
                    new_monthly_week = st.selectbox("Тиждень місяця", [1, 2, 3, 4, -1], index=[1, 2, 3, 4, -1].index(habit.get("monthly_week", 1)), key=f"month_habit_{habit['id']}")

                if st.button("💾 Зберегти", key=f"save_habit_{habit['id']}"):
                    update_entry("habits_active", habit["id"], {
                        "name": new_name,
                        "description": new_description,
                        "frequency": new_frequency,
                        "day_of_week": new_day_of_week,
                        "monthly_week": new_monthly_week,
                    })
                    st.success("Звичку оновлено!")
                    st.rerun()

            if st.button("🗑️ Скасувати", key=f"delete_habit_{habit['id']}"):
                delete_entry("habits_active", habit["id"])
                st.rerun()

    # --- Завдання ---
    st.subheader("📌 Активні завдання")
    tasks = get_active_tasks(user.id)
    for task in tasks:
        col1 = st.container()
        with col1:
            st.markdown(f"**{task['name']}** — {task['date']} о {task['time']}")
            if task.get("description"):
                st.caption(task["description"])

            if st.button("✅ Завершити", key=f"complete_task_{task['id']}"):
                complete_entry("task", task["id"], user.id)
                st.rerun()

            if st.button("⏸️ Відкласти", key=f"postpone_task_{task['id']}"):
                postpone_entry("task", task["id"], user.id)
                st.rerun()

            with st.expander("✏️ Редагувати", expanded=False):
                new_name = st.text_input("Назва", value=task["name"], key=f"name_task_{task['id']}")
                new_description = st.text_area("Опис", value=task.get("description", ""), key=f"desc_task_{task['id']}")
                new_date = st.date_input("Дата", value=datetime.strptime(task["date"], "%Y-%m-%d").date(), key=f"date_task_{task['id']}")
                new_time = st.time_input("Час", value=datetime.strptime(task["time"], "%H:%M:%S").time(), key=f"time_task_{task['id']}")

                if st.button("💾 Зберегти", key=f"save_task_{task['id']}"):
                    update_entry("tasks_active", task["id"], {
                        "name": new_name,
                        "description": new_description,
                        "date": str(new_date),
                        "time": str(new_time),
                    })
                    st.success("Завдання оновлено!")
                    st.rerun()

            if st.button("🗑️ Скасувати", key=f"delete_task_{task['id']}"):
                delete_entry("tasks_active", task["id"])
                st.rerun()
