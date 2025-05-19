import os
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime, timedelta, timezone
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_token():
    """
    Отримати токен з сесії Streamlit.
    :return:
    """
    if "token" in st.session_state:
        return st.session_state["token"]
    raise ValueError("❌ Токен не знайдено. Користувач не авторизований.")


def get_supabase_client_with_token(token: str) -> object:
    """
    Створити клієнта Supabase з токеном користувача.
    :param token:
    :return:
    """
    options = SyncClientOptions(headers={"Authorization": f"Bearer {token}"})
    return create_client(SUPABASE_URL, SUPABASE_KEY, options=options)


def insert_to_table(
        table: str,
        data: dict
) -> None:
    """
    Додати запис до таблиці Supabase.
    :param table:
    :param data:
    :return:
    """
    client = get_supabase_client_with_token(get_token())
    client.table(table).insert(data).execute()


def update_entry(
        table: str,
        entry_id: str,
        updated_data: dict,
        user_id: str
) -> None:
    """
    Оновлення запису в таблиці Supabase.
    :param table:
    :param entry_id:
    :param updated_data:
    :param user_id:
    :return:
    """
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

        frequency = updated_data.get("frequency", existing.get("frequency"))
        day_of_week = updated_data.get("day_of_week", existing.get("day_of_week"))

        updated_entry = {
            "name": title,
            "description": description,
            "start_time": dt_start,
            "end_time": dt_end,
            "frequency": frequency,
            "day_of_week": day_of_week,
        }

        if frequency == "monthly":
            monthly_week = updated_data.get("monthly_week", existing.get("monthly_week", 1))
            updated_entry["monthly_week"] = monthly_week

        update_event_in_calendar(user_id, event_id, updated_entry)


def delete_entry(
        table: str,
        entry_id: str,
        user_id: str
) -> None:
    """
    Видалити запис з таблиці Supabase.
    :param table:
    :param entry_id:
    :param user_id:
    :return:
    """

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


def fetch_table(
        table: str,
        user_id: str,
        entry_id: str = None
) -> list:
    """
    Отримати записи з таблиці Supabase.
    :param table:
    :param user_id:
    :param entry_id:
    :return:
    """
    client = get_supabase_client_with_token(get_token())
    query = client.table(table).select("*").eq("user_id", user_id)
    if entry_id:
        query = query.eq("id", entry_id)
    result = query.execute()
    return result.data if result.data else []


def move_entry(
        source_table: str,
        target_table: str,
        entry_id: int,
        user_id: str,
        extra_fields: dict = None
) -> None:
    """
    Перемістити запис з однієї таблиці в іншу.
    :param source_table:
    :param target_table:
    :param entry_id:
    :param user_id:
    :param extra_fields:
    :return:
    """
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


def clear_all_event_ids(user_id: str) -> None:
    """
    Очистити всі event_id в таблицях habits_active і tasks_active.
    :param user_id:
    :return:
    """
    client = get_supabase_client_with_token(get_token())

    for table in ["habits_active", "tasks_active"]:
        client.table(table).update({"event_id": None}).eq("user_id", user_id).execute()