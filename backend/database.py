import os
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime, timedelta, timezone
from supabase import create_client
from supabase.lib.client_options import ClientOptions

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Отримати токен з сесії ---
def get_token():
    if "token" in st.session_state:
        return st.session_state["token"]
    raise ValueError("❌ Токен не знайдено. Користувач не авторизований.")

# --- Створити клієнта з токеном користувача ---
def get_supabase_client_with_token(token: str):
    options = ClientOptions(headers={"Authorization": f"Bearer {token}"})
    return create_client(SUPABASE_URL, SUPABASE_KEY, options=options)

# --- Додати запис до таблиці ---
def insert_to_table(table: str, data: dict):
    client = get_supabase_client_with_token(get_token())
    client.table(table).insert(data).execute()

# --- Оновити запис у таблиці ---
def update_entry(table: str, entry_id: str, updated_data: dict, user_id: str):
    token = st.session_state.get("token")
    if not token:
        raise Exception("❌ Access token не знайдено")

    client = get_supabase_client_with_token(token)
    result = client.table(table).select("*").eq("id", entry_id).eq("user_id", user_id).execute()

    if not result.data:
        raise Exception("Запис не знайдено")

    existing = result.data[0]
    event_id = existing.get("event_id")

    # Оновлення запису в таблиці
    client.table(table).update(updated_data).eq("id", entry_id).eq("user_id", user_id).execute()

    # Якщо є event_id — оновити подію в Google Calendar
    if event_id:
        from backend.calendar_sync import update_event_in_calendar

        title = updated_data.get("name", existing["name"])
        description = updated_data.get("description", existing.get("description", ""))
        time = updated_data.get("time") or existing.get("time") or "09:00"

        # Якщо це завдання (має дату)
        if existing.get("date") or updated_data.get("date"):
            date = updated_data.get("date", existing.get("date"))
            dt_start = datetime.fromisoformat(f"{date}T{time}")
        else:
            now_date = datetime.now(timezone.utc).date().isoformat()
            dt_start = datetime.fromisoformat(f"{now_date}T{time}")

        dt_end = dt_start + timedelta(hours=1)

        updated_entry = {
            "name": title,
            "description": description,
            "start_time": dt_start,
            "end_time": dt_end,
            "frequency": updated_data.get("frequency", existing.get("frequency")),
            "day_of_week": updated_data.get("day_of_week", existing.get("day_of_week")),
            "monthly_week": updated_data.get("monthly_week", existing.get("monthly_week")),
        }

        update_event_in_calendar(user_id, event_id, updated_entry)


# --- Видалити запис з таблиці ---
def delete_entry(table: str, entry_id: str, user_id: str):

    token = st.session_state.get("token")
    if not token:
        raise Exception("❌ Access token не знайдено")

    client = get_supabase_client_with_token(token)

    result = client.table(table).select("*").eq("id", entry_id).eq("user_id", user_id).execute()
    if not result.data:
        raise Exception("Запис не знайдено")

    client.table(table).delete().eq("id", entry_id).eq("user_id", user_id).execute()

    # Якщо є event_id — видалити з календаря
    entry = result.data[0]
    event_id = entry.get("event_id")
    if event_id:
        from backend.calendar_sync import delete_event_by_id
        delete_event_by_id(user_id, event_id)

# --- Отримати всі записи з таблиці ---
def fetch_table(table: str, user_id: str, entry_id: str = None):
    client = get_supabase_client_with_token(get_token())
    query = client.table(table).select("*").eq("user_id", user_id)
    if entry_id:
        query = query.eq("id", entry_id)
    result = query.execute()
    return result.data if result.data else []


# --- Перемістити запис з однієї таблиці в іншу ---
def move_entry(source_table: str, target_table: str, entry_id: int, user_id: str, extra_fields: dict = None):
    token = st.session_state.get("token")
    if not token:
        raise Exception("❌ Access token не знайдено")

    client = get_supabase_client_with_token(token)
    result = client.table(source_table).select("*").eq("id", entry_id).eq("user_id", user_id).execute()

    if not result.data or len(result.data) == 0:
        raise Exception(f"❌ Запис не знайдено в {source_table} з id={entry_id} і user_id={user_id}")

    entry = result.data[0]
    if extra_fields:
        entry.update(extra_fields)

    client.table(target_table).insert(entry).execute()
    client.table(source_table).delete().eq("id", entry_id).eq("user_id", user_id).execute()

