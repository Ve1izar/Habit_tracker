import streamlit as st
from google.auth.exceptions import RefreshError
from backend.google_auth import (
    get_credentials,
    get_calendar_service_for_user,
    start_auth_flow,
    finish_auth_flow,
    get_token_path,
)
from backend.calendar_sync import sync_all_to_calendar, delete_spam_events, sync_habits_to_calendar
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
    # 🔄 Синхронізація справ
    # --------------------------
    st.markdown("---")
    st.subheader("🔄 Синхронізація активних справ (без event_id)")
    if st.button("🔁 Синхронізувати справи"):
        try:
            from backend.calendar_sync import sync_tasks_to_calendar
            sync_tasks_to_calendar(user_id)
            st.success("✅ Справи синхронізовано до Google Calendar.")
        except RefreshError:
            st.error("❌ Потрібна повторна авторизація Google.")
        except Exception as e:
            st.error(f"❌ Помилка синхронізації: {e}")

    # --------------------------
    # 🛑 Небезпечна зона
    # --------------------------
    st.markdown("---")
    with st.expander("🛑 Небезпечна зона"):
        st.markdown("**Очистити всі записи**")
        st.caption("Всі внесені вами дані про активні та відкладені справи та звички будуть видалені.")

        if st.button("🔥 Очистити всі записи"):
            try:
                # Видалення всіх подій з Google Calendar
                service = get_calendar_service_for_user(user_id)
                events = service.events().list(calendarId='primary', singleEvents=True).execute().get("items", [])
                deleted_count = 0
                for event in events:
                    try:
                        service.events().delete(calendarId='primary', eventId=event["id"]).execute()
                        deleted_count += 1
                    except Exception as e:
                        print(f"⚠️ Не вдалося видалити подію {event['id']}: {e}")

                # Видалення записів з таблиць Supabase
                from backend.database import get_supabase_client_with_token
                token = st.session_state.get("token")
                client = get_supabase_client_with_token(token)

                tables_to_clear = [
                    "habits_active", "tasks_active",
                    "habits_postponed", "tasks_postponed"
                ]
                for table in tables_to_clear:
                    client.table(table).delete().eq("user_id", user_id).execute()

                st.success(f"✅ Видалено {deleted_count} подій з Google Calendar та всі активні/відкладені записи.")

            except Exception as e:
                st.error(f"❌ Помилка при очищенні: {e}")


