import streamlit as st
from frontend.auth import require_login
from backend.logic import restore_entry, get_postponed_items
from backend.database import delete_entry, update_entry, move_entry
from utils.helpers import format_day_of_week
from datetime import datetime

# --- Завершення відкладеної звички або завдання ---
def complete_postponed_entry(entry_type, entry_id, user_id):
    source_table = f"{entry_type}s_postponed"
    target_table = f"{entry_type}s_completed"
    move_entry(source_table, target_table, entry_id, user_id)

def show_postponed():
    user = require_login()
    st.title("⏸️ Відкладені завдання та звички")

    habits, tasks = get_postponed_items(user.id)

    # --- Відкладені звички ---
    st.subheader("🔁 Відкладені звички")
    for habit in habits:
        with st.container():
            st.markdown(
                f"""
                <div style="border: 1px solid #ccc; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <strong>{habit['name']}</strong> — {habit['frequency']} ({habit.get('day_name', '–')})<br>
                    <small>{habit.get('description', '')}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

            cols = st.columns([2, 2, 2])
            with cols[0]:
                if st.button("✅ Завершити", key=f"complete_post_habit_{habit['id']}"):
                    complete_postponed_entry("habit", habit["id"], user.id)
                    st.rerun()
            with cols[1]:
                if st.button("↩️ Повернути", key=f"restore_post_habit_{habit['id']}"):
                    restore_entry("habit", habit["id"], user.id)
                    st.rerun()
            with cols[2]:
                if st.button("🗑️ Видалити", key=f"delete_post_habit_{habit['id']}"):
                    delete_entry("habits_postponed", habit["id"])
                    st.rerun()

            with st.expander("✏️ Редагувати"):
                new_name = st.text_input("Назва", value=habit["name"], key=f"edit_post_habit_name_{habit['id']}")
                new_description = st.text_area("Опис", value=habit.get("description", ""), key=f"edit_post_habit_desc_{habit['id']}")
                new_frequency = st.selectbox(
                    "Частота",
                    ["daily", "weekly", "monthly"],
                    index=["daily", "weekly", "monthly"].index(habit["frequency"]),
                    key=f"edit_post_habit_freq_{habit['id']}"
                )

                new_day_of_week = habit.get("day_of_week", 0)
                new_monthly_week = habit.get("monthly_week", 1)

                if new_frequency in ["weekly", "monthly"]:
                    new_day_of_week = st.selectbox(
                        "День тижня",
                        options=list(range(7)),
                        index=int(habit.get("day_of_week", 0)),
                        format_func=format_day_of_week,
                        key=f"edit_post_habit_day_{habit['id']}"
                    )
                if new_frequency == "monthly":
                    new_monthly_week = st.selectbox(
                        "Тиждень місяця",
                        options=[1, 2, 3, 4, -1],
                        index=[1, 2, 3, 4, -1].index(habit.get("monthly_week", 1)),
                        key=f"edit_post_habit_month_{habit['id']}"
                    )

                if st.button("💾 Зберегти", key=f"save_post_habit_{habit['id']}"):
                    update_entry("habits_postponed", habit["id"], {
                        "name": new_name,
                        "description": new_description,
                        "frequency": new_frequency,
                        "day_of_week": new_day_of_week,
                        "monthly_week": new_monthly_week,
                    })
                    st.success("✅ Звичку оновлено!")
                    st.rerun()

    # --- Відкладені завдання ---
    st.subheader("📌 Відкладені завдання")
    for task in tasks:
        with st.container():
            st.markdown(
                f"""
                <div style="border: 1px solid #ccc; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <strong>{task['name']}</strong> — {task['date']} о {task['time']}<br>
                    <small>{task.get('description', '')}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

            cols = st.columns([2, 2, 2])
            with cols[0]:
                if st.button("✅ Завершити", key=f"complete_post_task_{task['id']}"):
                    complete_postponed_entry("task", task["id"], user.id)
                    st.rerun()
            with cols[1]:
                if st.button("↩️ Повернути", key=f"restore_post_task_{task['id']}"):
                    restore_entry("task", task["id"], user.id)
                    st.rerun()
            with cols[2]:
                if st.button("🗑️ Видалити", key=f"delete_post_task_{task['id']}"):
                    delete_entry("tasks_postponed", task["id"])
                    st.rerun()

            with st.expander("✏️ Редагувати"):
                new_name = st.text_input("Назва", value=task["name"], key=f"edit_post_task_name_{task['id']}")
                new_description = st.text_area("Опис", value=task.get("description", ""), key=f"edit_post_task_desc_{task['id']}")
                new_date = st.date_input(
                    "Дата",
                    value=datetime.strptime(task["date"], "%Y-%m-%d").date(),
                    key=f"edit_post_task_date_{task['id']}"
                )
                new_time = st.time_input(
                    "Час",
                    value=datetime.strptime(task["time"], "%H:%M:%S").time(),
                    key=f"edit_post_task_time_{task['id']}"
                )

                if st.button("💾 Зберегти", key=f"save_post_task_{task['id']}"):
                    update_entry("tasks_postponed", task["id"], {
                        "name": new_name,
                        "description": new_description,
                        "date": str(new_date),
                        "time": str(new_time),
                    })
                    st.success("✅ Завдання оновлено!")
                    st.rerun()
