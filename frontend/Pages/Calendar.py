import streamlit as st
from google.auth.exceptions import RefreshError
from backend.google_auth import (
    get_credentials,
    get_calendar_service_for_user,
    start_auth_flow,
    finish_auth_flow,
    get_token_path,
)
from backend.calendar_sync import sync_all_to_calendar, delete_spam_events
from datetime import datetime
import os

def show_calendar():
    st.title("📅 Google Calendar інтеграція")

    user = st.session_state.get("user")
    if not user:
        st.error("❗ Ви не авторизовані.")
        return

    user_id = user.id
    token_path = get_token_path(user_id)

    # --------------------------
    # 🔐 Перевірка токена
    # --------------------------
    creds = None
    email = None
    if token_path.exists():
        try:
            creds = get_credentials(user_id)
            email = creds.id_token.get("email") if creds.id_token else None
            if email:
                st.success(f"🔓 Токен знайдено. Авторизовано як: **{email}**")
            else:
                st.warning("⚠️ Токен знайдено, але email не визначено.")
        except Exception as e:
            st.warning(f"⚠️ Проблема з токеном: {e}")
    else:
        st.info("🔒 Ви ще не авторизувалися для доступу до Google Calendar.")

    # --------------------------
    # ❌ Видалити токен
    # --------------------------
    if token_path.exists():
        if st.button("🚪 Вийти з Google акаунта"):
            try:
                os.remove(token_path)
                st.success("🔒 Токен видалено. Ви вийшли з акаунта Google.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Не вдалося видалити токен: {e}")

    # --------------------------
    # 🔑 Авторизація
    # --------------------------
    if not creds:
        flow, auth_url = start_auth_flow()
        st.markdown(f"[🔐 Натисніть тут для авторизації Google]({auth_url})")

        code = st.text_input("Вставте код авторизації сюди:")
        if st.button("🔓 Завершити авторизацію"):
            try:
                finish_auth_flow(flow, code, user_id)
                st.success("✅ Авторизацію завершено! Оновлюємо сторінку...")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Помилка авторизації: {e}")

    # --------------------------
    # 🔄 Синхронізація подій
    # --------------------------
    st.markdown("---")
    st.subheader("🔄 Синхронізація")

    if st.button("🔁 Синхронізувати записи без подій"):
        try:
            sync_all_to_calendar(user_id)
            st.success("✅ Усі записи без подій синхронізовано до Google Calendar.")
        except RefreshError:
            st.error("❌ Потрібна повторна авторизація Google.")
        except Exception as e:
            st.error(f"❌ Помилка синхронізації: {e}")

    # --------------------------
    # 🗑️ Масове очищення подій
    # --------------------------
    st.markdown("---")
    st.subheader("🧹 Очистити події з календаря (на 30 днів уперед)")

    if st.button("🧹 Очистити календар"):
        try:
            deleted_count = delete_spam_events(user_id)
            st.success(f"✅ Видалено {deleted_count} подій.")
        except Exception as e:
            st.error(f"❌ Помилка при видаленні подій: {e}")
