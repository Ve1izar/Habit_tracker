import streamlit as st
import pandas as pd
from datetime import datetime
from frontend.auth import require_login
from backend.logic import get_completed_entries_by_month

def show_statistics():
    user = require_login()
    st.title("📊 Статистика виконаних завдань і звичок")

    df = get_completed_entries_by_month(user.id)
    if df.empty:
        st.info("Поки немає завершених записів.")
        return

    # Додаємо місяць у вигляді YYYY-MM
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)

    # --- Стовпчаста діаграма по місяцях ---
    st.subheader("📈 Виконано по місяцях")
    monthly_summary = df.groupby(["month", "type"]).size().unstack(fill_value=0)
    st.bar_chart(monthly_summary)

    # --- Фільтр по місяцю ---
    months = df["month"].sort_values().unique().tolist()
    selected_month = st.selectbox("Оберіть місяць для перегляду деталей:", months)

    st.markdown(f"### Деталі за {selected_month}")
    filtered = df[df["month"] == selected_month]

    habits = filtered[filtered["type"] == "habit"]
    tasks = filtered[filtered["type"] == "task"]

    st.subheader("✅ Завершені звички")
    for _, habit in habits.iterrows():
        st.markdown(f"• **{habit['name']}** — {habit.get('frequency', '')} ({habit.get('day_of_week', '')})")

    st.subheader("✅ Завершені завдання")
    for _, task in tasks.iterrows():
        st.markdown(f"• **{task['name']}** — {task.get('date', '')} о {task.get('time', '')}")
