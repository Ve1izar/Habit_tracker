import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ .env не завантажено або відсутні SUPABASE_URL/SUPABASE_KEY!")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
