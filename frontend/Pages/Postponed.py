import streamlit as st
from frontend.auth import require_login
from backend.logic import (
    get_postponed_items,
    restore_entry,
    delete_entry,
    complete_entry
)
from utils.helpers import format_day_of_week, format_monthly_position

def show_postponed():
    user = require_login()
    st.title("⏸️ Відкладені звички та завдання")

    habits, tasks = get_postponed_items(user.id)

    st.subheader("🕒 Відкладені звички")
    if not habits:
        st.info("ℹ️ Немає відкладених звичок.")
    else:
        for habit in habits:
            with st.container():
                frequency = habit["frequency"]
                if frequency == "monthly":
                    repeat_str = f"{format_monthly_position(habit.get('monthly_week'))} {format_day_of_week(habit.get('day_of_week', 0))}"
                elif frequency == "weekly":
                    repeat_str = format_day_of_week(habit.get("day_of_week", 0))
                else:
                    repeat_str = "Щодня"

                st.markdown(
                    f"""
                    <div style="border: 1px solid #ccc; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                        <strong>{habit['name']}</strong> — {habit['frequency']} ({repeat_str})<br>
                        <small>{habit.get('description', '')}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            cols = st.columns([1, 1, 1])
            with cols[0]:
                if st.button("🔁 Повернути", key=f"restore_habit_{habit['id']}"):
                    restore_entry("habit", habit["id"], user.id)
                    st.rerun()
            with cols[1]:
                if st.button("🗑️ Видалити", key=f"delete_habit_{habit['id']}"):
                    delete_entry("habits_postponed", habit["id"], user.id)
                    st.rerun()
            with cols[2]:
                if st.button("✅ Завершити", key=f"complete_habit_perm_{habit['id']}"):
                    complete_entry("habit", habit["id"], user.id)
                    delete_entry("habits_postponed", habit["id"], user.id)
                    st.success("🎉 Звичку завершено!")
                    st.rerun()

    st.markdown("---")
    st.subheader("🕒 Відкладені завдання")
    if not tasks:
        st.info("ℹ️ Немає відкладених завдань.")
    else:
        for task in tasks:
            with st.container():
                st.markdown(
                    f"""
                    <div style="border: 1px solid #ccc; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                        <strong>{task['name']}</strong> — {task['date']} о {task['time']}<br>
                        <small>{task.get('description', '')}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            cols = st.columns([1, 1, 1])
            with cols[0]:
                if st.button("🔁 Повернути", key=f"restore_task_{task['id']}"):
                    restore_entry("task", task["id"], user.id)
                    st.rerun()
            with cols[1]:
                if st.button("🗑️ Видалити", key=f"delete_task_{task['id']}"):
                    delete_entry("tasks_postponed", task["id"], user.id)
                    st.rerun()
            with cols[2]:
                if st.button("✅ Завершити", key=f"complete_task_{task['id']}"):
                    complete_entry("task", task["id"], user.id)
                    delete_entry("tasks_postponed", task["id"], user.id)
                    st.success("🎉 Завдання завершено!")
                    st.rerun()
