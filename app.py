import streamlit as st
from frontend.auth import require_login, logout, register
from frontend.Pages import Home, Add, Postponed, Stats, Profile

st.set_page_config(page_title="Habit Tracker", layout="wide")

PAGES = {
    "🏠 Home": Home.show_home,
    "➕ Додати": Add.show_add,
    "⏸️ Відкладені": Postponed.show_postponed,
    "📊 Статистика": Stats.show_statistics,
    "👤 Профіль": Profile.show_profile,
}

# --- Перевірка авторизації ---
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

if "user" not in st.session_state:
    st.title("💼 Habit Tracker")

    if st.session_state.auth_mode == "login":
        st.info("Увійдіть, щоб користуватись додатком:")
        if st.button("Немає аккаунту? Зареєструватись"):
            st.session_state.auth_mode = "register"
        require_login()
    else:
        st.info("Зареєструйтесь для використання додатку:")
        if st.button("Вже є аккаунт? Увійти"):
            st.session_state.auth_mode = "login"
        register()
    st.stop()

# --- Якщо користувач авторизований ---
user = st.session_state["user"]

# Сайдбар навігації
st.sidebar.title("🔗 Навігація")
choice = st.sidebar.radio("Перейти до:", list(PAGES.keys()))
st.sidebar.markdown("---")
logout()

# Відображення вибраної сторінки
PAGES[choice]()
