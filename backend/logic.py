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


# --- Активні звички ---
def get_active_habits(user_id):
    habits = fetch_table("habits_active", user_id)
    for habit in habits:
        habit["day_name"] = format_day_of_week(int(habit.get("day_of_week") or 0))
    return habits

# --- Активні завдання ---
def get_active_tasks(user_id):
    return fetch_table("tasks_active", user_id)

# --- Відкладені звички і завдання ---
def get_postponed_habits(user_id):
    habits = fetch_table("habits_postponed", user_id)
    for habit in habits:
        habit["day_name"] = format_day_of_week(int(habit.get("day_of_week") or 0))
    return habits

def get_postponed_tasks(user_id):
    return fetch_table("tasks_postponed", user_id)

def get_postponed_items(user_id: str):
    habits = get_postponed_habits(user_id)
    tasks = get_postponed_tasks(user_id)
    return habits, tasks

# --- Завершити запис ---
def complete_entry(entry_type: str, entry_id: str, user_id: str):
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

# --- Завершити звичку ---
def complete_habit_perm(entry_id: str, user_id: str):
    move_entry("habits_active", "habits_completed", entry_id, user_id)

# --- Відкласти запис ---
def postpone_entry(entry_type, entry_id, user_id):
    source = f"{entry_type}s_active"
    target = f"{entry_type}s_postponed"
    move_entry(source, target, entry_id, user_id)

# --- Повернути запис ---
def restore_entry(entry_type, entry_id, user_id):
    source = f"{entry_type}s_postponed"
    target = f"{entry_type}s_active"
    move_entry(source, target, entry_id, user_id)

# --- Оновити запис + календар ---
def update_entry_with_calendar(table, entry_id, data, user_id):
    update_entry(table, entry_id, data, user_id)
    updated = fetch_table(table, user_id, entry_id)
    if updated and updated[0].get("event_id"):
        update_event_in_calendar(user_id, updated[0]["event_id"], updated[0])

# --- Статистика завершених ---
def get_completed_entries_by_month(user_id):
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


# --- Синхронізація ---
def sync_events_to_google_calendar(user_id):
    sync_all_to_calendar(user_id)
