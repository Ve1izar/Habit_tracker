import datetime as dt
from datetime import datetime, timezone
import pandas as pd

from backend.database import (
    fetch_table,
    insert_to_table,
    move_entry,
    update_entry,
    delete_entry
)

from backend.calendar_sync import (
    delete_event_by_id,
    update_event_in_calendar,
    sync_all_to_calendar
)

from utils.helpers import format_day_of_week
from backend.database import get_supabase_client_with_token, update_entry, move_entry
from backend.google_auth import get_calendar_service_for_user
from googleapiclient.errors import HttpError
import streamlit as st

def get_active_habits(user_id):
    """
    Отримати активні звички користувача.
    :param user_id:
    :return:
    """
    habits = fetch_table("habits_active", user_id)
    for habit in habits:
        habit["day_name"] = format_day_of_week(int(habit.get("day_of_week") or 0))
    return habits


def get_active_tasks(user_id):
    """
    Отримати активні завдання користувача.
    :param user_id:
    :return:
    """
    return fetch_table("tasks_active", user_id)


def get_postponed_habits(user_id):
    """
    Отримати відкладені звички користувача.
    :param user_id:
    :return:
    """
    habits = fetch_table("habits_postponed", user_id)
    for habit in habits:
        habit["day_name"] = format_day_of_week(int(habit.get("day_of_week") or 0))
    return habits


def get_postponed_tasks(user_id):
    """
    Отримати відкладені завдання користувача.
    :param user_id:
    :return:
    """
    return fetch_table("tasks_postponed", user_id)


def get_postponed_items(user_id: str):
    """
    Отримати відкладені звички і завдання користувача.
    :param user_id:
    :return:
    """
    habits = get_postponed_habits(user_id)
    tasks = get_postponed_tasks(user_id)
    return habits, tasks


def complete_entry(entry_type: str, entry_id: str, user_id: str):
    """
    Завершити запис (звичку або завдання).
    :param entry_type:
    :param entry_id:
    :param user_id:
    :return:
    """
    now = datetime.now(timezone.utc).isoformat()

    if entry_type == "habit":
        habit = fetch_table("habits_active", user_id, entry_id)
        if habit:
            habit = habit[0]
            insert_to_table("habit_logs", {
                "habit_id": habit["id"],
                "habit_name": habit["name"],
                "user_id": user_id,
                "completed_at": now
            })
    elif entry_type == "task":
        task = fetch_table("tasks_active", user_id, entry_id)
        if task:
            task = task[0]
            if task.get("event_id"):
                delete_event_by_id(user_id, task["event_id"])
            move_entry("tasks_active", "tasks_completed", entry_id, user_id, {
                "completed_at": now
            })


def complete_habit_perm(habit_id: str, user_id: str):
    token = st.session_state.get("token")
    if not token:
        raise Exception("❌ Access token не знайдено")

    client = get_supabase_client_with_token(token)
    result = client.table("habits_active").select("*").eq("id", habit_id).eq("user_id", user_id).execute()

    if not result.data:
        raise Exception("❌ Звичку не знайдено")

    habit = result.data[0]
    event_id = habit.get("event_id")

    # 🗑️ Видаляємо подію з Google Calendar
    if event_id:
        try:
            service = get_calendar_service_for_user(user_id)
            service.events().delete(calendarId="primary", eventId=event_id).execute()
        except HttpError as e:
            print(f"⚠️ Помилка при видаленні події з календаря: {e}")

    # 🧹 Очищаємо event_id у таблиці
    update_entry("habits_active", habit_id, {"event_id": None}, user_id)

    # 🔁 Переносимо запис до habits_completed
    move_entry("habits_active", "habits_completed", habit_id, user_id)


def postpone_entry(entry_type, entry_id, user_id):
    """
    Відкласти запис (звичку або завдання).
    :param entry_type:
    :param entry_id:
    :param user_id:
    :return:
    """
    source = f"{entry_type}s_active"
    target = f"{entry_type}s_postponed"
    move_entry(source, target, entry_id, user_id)


def restore_entry(entry_type, entry_id, user_id):
    """
    Повернути запис (звичку або завдання) з відкладених до активних.
    :param entry_type:
    :param entry_id:
    :param user_id:
    :return:
    """
    source = f"{entry_type}s_postponed"
    target = f"{entry_type}s_active"
    move_entry(source, target, entry_id, user_id)

def restore_from_completed(entry_type: str, entry_id: int, user_id: str):
    """
    Повернути запис із *_completed до *_active.
    """
    source = f"{entry_type}s_completed"
    target = f"{entry_type}s_active"
    move_entry(source, target, entry_id, user_id)

def update_entry_with_calendar(table, entry_id, data, user_id):
    """
    Оновити запис у таблиці та синхронізувати з Google Calendar.
    :param table:
    :param entry_id:
    :param data:
    :param user_id:
    :return:
    """
    update_entry(table, entry_id, data, user_id)
    updated = fetch_table(table, user_id, entry_id)
    if updated and updated[0].get("event_id"):
        update_event_in_calendar(user_id, updated[0]["event_id"], updated[0])


def get_completed_entries_by_month(user_id):
    """
    Отримати завершені звички та завдання за місяць.
    :param user_id:
    :return:
    """
    habit_logs = fetch_table("habit_logs", user_id)
    habits_completed = fetch_table("habits_completed", user_id)
    tasks = fetch_table("tasks_completed", user_id)

    habits_active = fetch_table("habits_active", user_id)
    habit_names = {h["id"]: h["name"] for h in habits_active}

    for log in habit_logs:
        log["type"] = "habit"
        log["date"] = log.get("completed_at") or datetime.now().isoformat()
        log["name"] = habit_names.get(log.get("habit_id"), log.get("habit_name", "Невідома звичка"))

    for h in habits_completed:
        h["type"] = "habit"
        h["date"] = h.get("completed_at") or datetime.now().isoformat()
        h["name"] = h.get("name", "Звичка")

    for t in tasks:
        t["type"] = "task"
        t["date"] = t.get("completed_at") or datetime.now().isoformat()

    return pd.DataFrame(habit_logs + habits_completed + tasks)


def sync_events_to_google_calendar(user_id):
    """
    Синхронізувати події з Google Calendar.
    :param user_id:
    :return:
    """
    sync_all_to_calendar(user_id)