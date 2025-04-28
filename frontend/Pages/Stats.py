import streamlit as st
import pandas as pd
from frontend.auth import require_login
from backend.logic import get_completed_entries_by_month

def show_statistics():
    user = require_login()
    st.title("📊 Статистика виконаних завдань і звичок")

    df = get_completed_entries_by_month(user.id)
    if df.empty:
        st.info("Поки немає завершених записів.")
        return

    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)

    # --- Графік завершених звичок ---
    st.subheader("✅ Завершені звички по місяцях")
    habits = df[df["type"] == "habit"]
    if not habits.empty:
        habit_summary = habits.groupby("month").size()
        st.bar_chart(habit_summary)

        months_habits = habits["month"].sort_values().unique().tolist()
        selected_month_habit = st.selectbox("Оберіть місяць для звичок:", months_habits)

        st.markdown(f"### Завершені звички за {selected_month_habit}")
        filtered_habits = habits[habits["month"] == selected_month_habit]
        for _, habit in filtered_habits.iterrows():
            st.markdown(f"• **{habit['name']}** — {habit.get('completed_at', '')}")

    else:
        st.info("Немає завершених звичок.")

    st.markdown("---")

    # --- Графік завершених завдань ---
    st.subheader("✅ Завершені завдання по місяцях")
    tasks = df[df["type"] == "task"]
    if not tasks.empty:
        task_summary = tasks.groupby("month").size()
        st.bar_chart(task_summary)

        months_tasks = tasks["month"].sort_values().unique().tolist()
        selected_month_task = st.selectbox("Оберіть місяць для завдань:", months_tasks)

        st.markdown(f"### Завершені завдання за {selected_month_task}")
        filtered_tasks = tasks[tasks["month"] == selected_month_task]
        for _, task in filtered_tasks.iterrows():
            st.markdown(f"• **{task['name']}** — {task.get('date', '')} о {task.get('time', '')}")

    else:
        st.info("Немає завершених завдань.")
