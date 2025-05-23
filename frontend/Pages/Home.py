import streamlit as st
from datetime import datetime
from googleapiclient.errors import HttpError

from frontend.auth import require_login
from backend.logic import (
    get_active_habits,
    get_active_tasks,
    complete_entry,
    postpone_entry,
    delete_entry,
    complete_habit_perm,
)
from backend.database import update_entry
from backend.google_auth import get_calendar_service_for_user, get_token_path
from utils.helpers import format_day_of_week, format_monthly_position


def verify_event_exists(user_id: str, event_id: str, table: str, entry_id: str, token_warned_flag: dict):
    try:
        service = get_calendar_service_for_user(user_id)
        service.events().get(calendarId='primary', eventId=event_id).execute()
    except HttpError as e:
        if e.resp.status == 404:
            update_entry(table, entry_id, {"event_id": None}, user_id)
        elif e.resp.status == 401 and not token_warned_flag["warned"]:
            st.warning("❗ Авторизація Google недійсна. Перейдіть на сторінку керування календарем для повторної авторизації.")
            token_warned_flag["warned"] = True
    except Exception as e:
        if "Access token" in str(e) and not token_warned_flag["warned"]:
            st.warning("❗ Токен Google не знайдено. Перейдіть на сторінку керування календарем та авторизуйтесь.")
            token_warned_flag["warned"] = True


def show_home():
    user = require_login()
    user_id = user.id

    st.title("🏠 Активні звички та завдання")

    token_warned_flag = {"warned": False}
    token_path = get_token_path(user_id)

    if not token_path.exists():
        st.warning("❗ Токен Google не знайдено. Перейдіть на сторінку керування календарем та авторизуйтесь.")
        token_warned_flag["warned"] = True

    # --- Звички ---
    st.subheader("🔁 Активні звички")
    habits = get_active_habits(user_id)

    if not habits:
        st.info("ℹ️ У вас немає активних звичок.")
    else:
        for habit in habits:
            if habit.get("event_id"):
                verify_event_exists(user_id, habit["event_id"], "habits_active", habit["id"], token_warned_flag)

        for habit in habits:
            with st.container():
                frequency = habit["frequency"]
                if frequency == "monthly":
                    repeat_str = f"{format_monthly_position(habit.get('monthly_week'))} {format_day_of_week(habit.get('day_of_week', 0))}"
                elif frequency == "weekly":
                    repeat_str = format_day_of_week(habit.get("day_of_week", 0))
                else:
                    repeat_str = "Щодня"

                calendar_status = "✅ Синхронізовано" if habit.get("event_id") else "❌ Не синхронізовано"

                st.markdown(
                    f"""
                    <div style="border: 1px solid #ccc; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                        <strong>{habit['name']}</strong> — {habit['frequency']} ({repeat_str})<br>
                        <small>{habit.get('description', '')}</small><br>
                        <i>{calendar_status}</i>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                cols = st.columns([1, 1, 1, 1])
                with cols[0]:
                    if st.button("☑️ Завершити", key=f"complete_habit_{habit['id']}"):
                        complete_entry("habit", habit["id"], user_id)
                        st.rerun()
                with cols[1]:
                    if st.button("⏸️ Відкласти", key=f"postpone_habit_{habit['id']}"):
                        postpone_entry("habit", habit["id"], user_id)
                        st.rerun()
                with cols[2]:
                    if st.button("🗑️ Скасувати", key=f"delete_habit_{habit['id']}"):
                        delete_entry("habits_active", habit["id"], user_id)
                        st.rerun()
                with cols[3]:
                    if st.button("✅ Завершити повністю", key=f"perm_complete_habit_{habit['id']}"):
                        complete_habit_perm(habit["id"], user_id)
                        st.success("🎯 Звичка завершена остаточно!")
                        st.rerun()

                with st.expander("✏️ Редагувати"):
                    new_name = st.text_input("Назва", value=habit["name"], key=f"name_habit_{habit['id']}")
                    new_description = st.text_area("Опис", value=habit.get("description", ""), key=f"desc_habit_{habit['id']}")
                    new_frequency = st.selectbox(
                        "Частота",
                        ["daily", "weekly", "monthly"],
                        index=["daily", "weekly", "monthly"].index(habit["frequency"]),
                        key=f"freq_habit_{habit['id']}"
                    )

                    new_day_of_week = habit.get("day_of_week", 0)
                    new_monthly_week = habit.get("monthly_week", 1)

                    if new_frequency in ["weekly", "monthly"]:
                        new_day_of_week = st.selectbox(
                            "День тижня",
                            options=list(range(7)),
                            index=int(habit.get("day_of_week", 0)),
                            format_func=format_day_of_week,
                            key=f"day_habit_{habit['id']}"
                        )
                    if new_frequency == "monthly":
                        new_monthly_week = st.selectbox(
                            "Тиждень місяця",
                            options=[1, 2, 3, 4, -1],
                            index=[1, 2, 3, 4, -1].index(habit.get("monthly_week", 1)),
                            key=f"month_habit_{habit['id']}"
                        )

                    if st.button("💾 Зберегти", key=f"save_habit_{habit['id']}"):
                        update_entry("habits_active", habit["id"], {
                            "name": new_name,
                            "description": new_description,
                            "frequency": new_frequency,
                            "day_of_week": new_day_of_week,
                            "monthly_week": new_monthly_week,
                        }, user_id)
                        st.success("✅ Звичку оновлено!")
                        st.rerun()

    # --- Завдання ---
    st.markdown("---")
    st.subheader("📌 Активні завдання")
    tasks = get_active_tasks(user_id)

    if not tasks:
        st.info("ℹ️ У вас немає активних завдань.")
    else:
        for task in tasks:
            if task.get("event_id"):
                verify_event_exists(user_id, task["event_id"], "tasks_active", task["id"], token_warned_flag)

        for task in tasks:
            calendar_status = "✅ Синхронізовано" if task.get("event_id") else "❌ Не синхронізовано"

            with st.container():
                st.markdown(
                    f"""
                        <div style="border: 1px solid #ccc; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                            <strong>{task['name']}</strong> — {task['date']} о {task['time']}<br>
                            <small>{task.get('description', '')}</small><br>
                            <i>{calendar_status}</i>
                        </div>
                        """,
                    unsafe_allow_html=True
                )

                cols = st.columns([1, 1, 1])
                with cols[0]:
                    if st.button("✅ Завершити", key=f"complete_task_{task['id']}"):
                        complete_entry("task", task["id"], user_id)
                        st.rerun()
                with cols[1]:
                    if st.button("⏸️ Відкласти", key=f"postpone_task_{task['id']}"):
                        postpone_entry("task", task["id"], user_id)
                        st.rerun()
                with cols[2]:
                    if st.button("🗑️ Скасувати", key=f"delete_task_{task['id']}"):
                        delete_entry("tasks_active", task["id"], user_id)
                        st.rerun()

                with st.expander("✏️ Редагувати"):
                    new_name = st.text_input("Назва", value=task["name"], key=f"name_task_{task['id']}")
                    new_description = st.text_area("Опис", value=task.get("description", ""), key=f"desc_task_{task['id']}")
                    new_date = st.date_input(
                        "Дата",
                        value=datetime.strptime(task["date"], "%Y-%m-%d").date(),
                        key=f"date_task_{task['id']}"
                    )
                    new_time = st.time_input(
                        "Час",
                        value=datetime.strptime(task["time"], "%H:%M:%S").time(),
                        key=f"time_task_{task['id']}"
                    )

                    if st.button("💾 Зберегти", key=f"save_task_{task['id']}"):
                        update_entry("tasks_active", task["id"], {
                            "name": new_name,
                            "description": new_description,
                            "date": str(new_date),
                            "time": str(new_time),
                        }, user_id)
                        st.success("✅ Завдання оновлено!")
                        st.rerun()
