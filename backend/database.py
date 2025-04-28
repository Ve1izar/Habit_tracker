import os
from dotenv import load_dotenv
from supabase import create_client, ClientOptions
import streamlit as st

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
    options = ClientOptions(
        headers={"Authorization": f"Bearer {token}"}
    )
    return create_client(SUPABASE_URL, SUPABASE_KEY, options=options)

# --- Додати новий запис до таблиці ---
def insert_to_table(table: str, data: dict):
    client = get_supabase_client_with_token(get_token())
    client.table(table).insert(data).execute()

# --- Оновити запис у таблиці ---
def update_entry(table: str, entry_id: int, updated_data: dict):
    client = get_supabase_client_with_token(get_token())
    client.table(table).update(updated_data).eq("id", entry_id).execute()

# --- Видалити запис з таблиці ---
def delete_entry(table: str, entry_id: int):
    client = get_supabase_client_with_token(get_token())
    client.table(table).delete().eq("id", entry_id).execute()

# --- Отримати записи з таблиці ---
def fetch_table(table: str, user_id: str):
    client = get_supabase_client_with_token(get_token())
    result = client.table(table).select("*").eq("user_id", user_id).execute()
    return result.data if result.data else []

# --- Перемістити запис з однієї таблиці в іншу ---
def move_entry(source_table: str, target_table: str, entry_id: int, user_id: str):
    client = get_supabase_client_with_token(get_token())
    record = client.table(source_table).select("*").eq("id", entry_id).eq("user_id", user_id).execute()
    if not record.data:
        return
    entry = record.data[0]
    client.table(target_table).insert(entry).execute()
    client.table(source_table).delete().eq("id", entry_id).execute()
