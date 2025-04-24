import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
import os



load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_current_user():
    return st.session_state.get("user")

# --- Авторизація ---
def require_login():
    if "user" not in st.session_state:
        login()
    return st.session_state.get("user")


def login():
    st.subheader("🔐 Вхід")
    email = st.text_input("Email")
    password = st.text_input("Пароль", type="password")

    if st.button("Увійти"):
        try:
            result = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state["user"] = result.user
            st.success("✅ Вхід виконано успішно")
            st.rerun()
        except Exception:
            st.error("❌ Невірний email або пароль")


def logout():
    if st.sidebar.button("🚪 Вийти"):
        st.session_state.clear()
        st.rerun()


# --- Реєстрація ---
def register():
    st.subheader("📝 Реєстрація")
    name = st.text_input("Ім’я користувача")
    email = st.text_input("Email")
    password = st.text_input("Пароль", type="password")

    if st.button("Зареєструватись"):
        try:
            result = supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {"name": name}
                    },
                }
            )
            st.success("✅ Реєстрація пройшла успішно! Перевірте email для підтвердження.")
        except Exception:
            st.error("❌ Помилка при реєстрації")


# --- Отримання поточного користувача ---
def get_current_user():
    return st.session_state.get("user")


# --- Оновлення метаданих користувача ---
def update_user_metadata(data: dict):
    user = get_current_user()
    return supabase.auth.update_user(user_metadata=data)


def update_display_name(name: str):
    user = get_current_user()
    if user:
        supabase.auth.update_user({"data": {"name": name}})


def update_email(new_email: str):
    user = get_current_user()
    if user:
        supabase.auth.update_user({"email": new_email})


def update_password(new_password: str):
    user = get_current_user()
    if user:
        supabase.auth.update_user({"password": new_password})
