from dotenv import load_dotenv
from supabase import create_client
import os

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Додати новий запис до таблиці ---
def insert_to_table(table: str, data: dict):
    supabase.table(table).insert(data).execute()

# --- Оновити запис у таблиці ---
def update_entry(table: str, entry_id: int, updated_data: dict):
    supabase.table(table).update(updated_data).eq("id", entry_id).execute()

# --- Видалити запис з таблиці ---
def delete_entry(table: str, entry_id: int):
    supabase.table(table).delete().eq("id", entry_id).execute()

# --- Отримати записи з таблиці ---
def fetch_table(table: str, user_id: str):
    result = supabase.table(table).select("*").eq("user_id", user_id).execute()
    return result.data if result.data else []

# --- Перемістити запис з однієї таблиці в іншу ---
def move_entry(source_table: str, target_table: str, entry_id: int, user_id: str):
    record = supabase.table(source_table).select("*").eq("id", entry_id).eq("user_id", user_id).execute()
    if not record.data:
        return
    entry = record.data[0]
    insert_to_table(target_table, entry)
    delete_entry(source_table, entry_id)
