import streamlit as st
import pandas as pd
from datetime import datetime
from frontend.auth import require_login
from backend.logic import fetch_table, restore_from_completed, delete_entry
from utils.helpers import format_day_of_week, format_monthly_position

def show_completed():
    user = require_login()
    user_id = user.id

    st.title("✅ Завершені звички, завдання і логи")

    # --- Отримуємо завершені записи ---
    habits = fetch_table("habits_completed", user_id)
    tasks = fetch_table("tasks_completed", user_id)
    logs = fetch_table("habit_logs", user_id)

    # --- Форматуємо дати для фільтрації ---
    def extract_month(date_str):
        try:
            return pd.to_datetime(date_str).to_period("M").strftime("%Y-%m")
        except:
            return "Невідомо"

    for h in habits:
        h["month"] = extract_month(h.get("completed_at"))
    for t in tasks:
        t["month"] = extract_month(t.get("completed_at"))
    for l in logs:
        l["month"] = extract_month(l.get("completed_at"))

    all_months = sorted(set(h["month"] for h in habits) |
                        set(t["month"] for t in tasks) |
                        set(l["month"] for l in logs))
    selected_month = st.selectbox("📅 Оберіть місяць:", all_months, index=len(all_months)-1 if all_months else 0)

    st.markdown("---")

    # --- Завершені звички ---
    st.subheader("🔁 Завершені звички")
    month_habits = [h for h in habits if h["month"] == selected_month]
    if not month_habits:
        st.info("ℹ️ Немає завершених звичок за цей місяць.")
    else:
        for habit in month_habits:
            repeat_str = {
                "daily": "Щодня",
                "weekly": format_day_of_week(habit.get("day_of_week", 0)),
                "monthly": f"{format_monthly_position(habit.get('monthly_week'))} {format_day_of_week(habit.get('day_of_week', 0))}",
            }.get(habit["frequency"], "—")

            st.markdown(
                f"""
                <div style="border:1px solid #ccc;padding:10px;border-radius:8px;margin-bottom:10px;">
                <strong>{habit['name']}</strong> — {habit['frequency']} ({repeat_str})<br>
                <small>{habit.get('description', '')}</small><br>
                <i>Завершено: {habit.get('completed_at', '')}</i>
                </div>
                """, unsafe_allow_html=True)

            cols = st.columns([1, 1])
            with cols[0]:
                if st.button("🔁 Повернути", key=f"restore_habit_{habit['id']}"):
                    restore_from_completed("habit", habit["id"], user_id)
                    st.rerun()
            with cols[1]:
                if st.button("🗑️ Видалити", key=f"delete_habit_{habit['id']}"):
                    delete_entry("habits_completed", habit["id"], user_id)
                    st.rerun()

    # --- Завершені завдання ---
    st.subheader("📌 Завершені завдання")
    month_tasks = [t for t in tasks if t["month"] == selected_month]
    if not month_tasks:
        st.info("ℹ️ Немає завершених завдань за цей місяць.")
    else:
        for task in month_tasks:
            st.markdown(
                f"""
                <div style="border:1px solid #ccc;padding:10px;border-radius:8px;margin-bottom:10px;">
                <strong>{task['name']}</strong> — {task['date']} о {task['time']}<br>
                <small>{task.get('description', '')}</small><br>
                <i>Завершено: {task.get('completed_at', '')}</i>
                </div>
                """, unsafe_allow_html=True)

            cols = st.columns([1, 1])
            with cols[0]:
                if st.button("🔁 Повернути", key=f"restore_task_{task['id']}"):
                    restore_from_completed("task", task["id"], user_id)
                    st.rerun()
            with cols[1]:
                if st.button("🗑️ Видалити", key=f"delete_task_{task['id']}"):
                    delete_entry("tasks_completed", task["id"], user_id)
                    st.rerun()

    # --- Логи виконання звичок ---
    st.subheader("📝 Логи виконання звичок")
    month_logs = [l for l in logs if l["month"] == selected_month]
    if not month_logs:
        st.info("ℹ️ Немає логів за цей місяць.")
    else:
        for log in month_logs:
            st.markdown(f"• **{log['habit_name']}** — {log.get('completed_at', '—')}")
            if st.button("🗑️ Видалити лог", key=f"delete_log_{log['id']}"):
                delete_entry("habit_logs", log["id"], user_id)
                st.rerun()
