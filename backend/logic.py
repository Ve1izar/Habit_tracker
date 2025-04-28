from datetime import datetime
import pandas as pd
from backend.database import fetch_table, move_entry, insert_to_table
from utils.helpers import format_day_of_week
from backend.calendar_sync import add_event_to_calendar
import datetime as dt

# --- Активні звички ---
def get_active_habits(user_id):
    habits = fetch_table("habits_active", user_id)
    for habit in habits:
        habit["day_name"] = format_day_of_week(int(habit.get("day_of_week") or 0))
    return habits

# --- Активні завдання ---
def get_active_tasks(user_id):
    return fetch_table("tasks_active", user_id)

# --- Завершені звички і завдання ---
def get_completed_items(user_id):
    habits = fetch_table("habits_completed", user_id)
    tasks = fetch_table("tasks_completed", user_id)
    return habits, tasks

# --- Відкладені звички і завдання ---
def get_postponed_items(user_id):
    habits = fetch_table("habits_postponed", user_id)
    tasks = fetch_table("tasks_postponed", user_id)
    for habit in habits:
        habit["day_name"] = format_day_of_week(int(habit.get("day_of_week") or 0))
    return habits, tasks

# --- Завершити запис ---
def complete_entry(entry_type, entry_id, user_id):
    if entry_type == "habit":
        # Завантажити поточну звичку по id
        habits = fetch_table("habits_active", user_id)
        habit = next((h for h in habits if h["id"] == entry_id), None)

        if habit:
            insert_to_table("habit_logs", {
                "habit_id": habit["id"],
                "habit_name": habit["name"],  # ⚡ нове поле
                "user_id": user_id,
                "completed_at": datetime.now().isoformat()
            })
    else:
        source_table = f"{entry_type}s_active"
        target_table = f"{entry_type}s_completed"
        move_entry(source_table, target_table, entry_id, user_id)

def get_completed_entries_by_month(user_id):
    habits = fetch_table("habit_logs", user_id)  # ⚡ тепер беремо habit_logs
    tasks = fetch_table("tasks_completed", user_id)

    for h in habits:
        h["type"] = "habit"
        h["date"] = h.get("completed_at") or datetime.now().isoformat()
        h["name"] = h.get("habit_name", "Невідома звичка")  # ⚡ беремо назву звички

    for t in tasks:
        t["type"] = "task"
        t["date"] = t.get("completed_at") or datetime.now().isoformat()

    return pd.DataFrame(habits + tasks)


# --- Відкласти запис ---
def postpone_entry(entry_type, entry_id, user_id):
    source_table = f"{entry_type}s_active"
    target_table = f"{entry_type}s_postponed"
    move_entry(source_table, target_table, entry_id, user_id)

# --- Повернути запис з відкладеного ---
def restore_entry(entry_type, entry_id, user_id):
    source_table = f"{entry_type}s_postponed"
    target_table = f"{entry_type}s_active"
    move_entry(source_table, target_table, entry_id, user_id)

# --- Статистика завершених ---
def get_completed_entries_by_month(user_id):
    habit_logs = fetch_table("habit_logs", user_id)
    tasks = fetch_table("tasks_completed", user_id)

    # Завантажити всі активні звички для відображення назв
    habits_active = fetch_table("habits_active", user_id)
    habits_mapping = {habit["id"]: habit["name"] for habit in habits_active}

    # Додаємо інформацію в логи звичок
    for log in habit_logs:
        log["type"] = "habit"
        log["date"] = log.get("completed_at") or datetime.now().isoformat()
        log["name"] = habits_mapping.get(log.get("habit_id"), "Невідома звичка")

    # Додаємо інформацію в завдання
    for t in tasks:
        t["type"] = "task"
        t["date"] = t.get("completed_at") or datetime.now().isoformat()

    return pd.DataFrame(habit_logs + tasks)


# --- Синхронізація з Google Calendar ---
def sync_events_to_google_calendar(user_id):
    habits = get_active_habits(user_id)
    tasks = get_active_tasks(user_id)

    # Синхронізація звичок
    for habit in habits:
        name = habit["name"]
        description = habit.get("description", "")
        frequency = habit.get("frequency", "daily")
        time = habit.get("time") or "08:00"  # <-- Безпечне значення, якщо time немає
        day_of_week = habit.get("day_of_week", 0)
        monthly_week = habit.get("monthly_week", 1)

        # Час початку
        start_time = dt.datetime.now().replace(hour=int(time[:2]), minute=int(time[3:5]), second=0)

        # Генерація recurrence для звичок
        recurrence = None
        if frequency == "daily":
            recurrence = ["RRULE:FREQ=DAILY"]
        elif frequency == "weekly":
            byday = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"][int(day_of_week)]
            recurrence = [f"RRULE:FREQ=WEEKLY;BYDAY={byday}"]
        elif frequency == "monthly":
            byday = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"][int(day_of_week)]
            recurrence = [f"RRULE:FREQ=MONTHLY;BYDAY={monthly_week}{byday}"]

        # Стандартно тривалість події = 1 година
        end_time = start_time + dt.timedelta(hours=1)

        add_event_to_calendar(name, start_time, end_time, description, recurrence)

    # Синхронізація завдань
    for task in tasks:
        name = task["name"]
        description = task.get("description", "")
        date_str = task["date"]
        time_str = task.get("time") or "08:00"  # <-- Безпечне значення, якщо time немає

        # Час початку і закінчення
        start_time = dt.datetime.fromisoformat(f"{date_str}T{time_str}")
        end_time = start_time + dt.timedelta(hours=1)

        add_event_to_calendar(name, start_time, end_time, description)